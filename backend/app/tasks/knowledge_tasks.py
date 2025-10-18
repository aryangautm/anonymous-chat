from uuid import UUID
from typing import List
from celery import Task

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeModule
from app.services.ingestion.text_processor import text_processor
from app.services.ingestion.document_parser import load_document
from app.services.ingestion.web_parser import load_web_content
from app.memory.vectorstore import vector_store
from langchain_core.documents import Document
from datetime import datetime


class DatabaseTask(Task):
    """Base task with database session."""

    _session = None

    @property
    def session(self):
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    def after_return(self, *args, **kwargs):
        if self._session is not None:
            self._session.close()
            self._session = None


@celery_app.task(base=DatabaseTask, bind=True)
def process_knowledge_module_task(self, module_id: str):
    """
    Process knowledge module: chunk text and generate embeddings.

    This task:
    1. Retrieves module from database
    2. Extracts/chunks text based on module type
    3. Generates embeddings for each chunk
    4. Stores chunks with embeddings
    """
    db = self.session

    # Get module
    module = (
        db.query(KnowledgeModule).filter(KnowledgeModule.id == UUID(module_id)).first()
    )

    if not module:
        return {"error": "Module not found"}

    # Extract text based on module type
    docs = []
    if module.module_type == "bio":
        docs.append(Document(page_content=module.content.get("text", "")))

    elif module.module_type == "qna":
        # Extract Q&A pairs as text
        pairs = module.content.get("pairs", [])

        for pair in pairs:
            q = pair.get("q", "")
            a = pair.get("a", "")
            docs.append(Document(page_content=f"Q: {q}\nA: {a}"))

    elif module.module_type == "text_block":
        docs.append(Document(page_content=module.content.get("text", "")))

    elif module.module_type == "url_source":
        if "scraped_content" not in module.content:
            url = module.content.get("url")
            try:
                import asyncio

                scraped: List[Document] = asyncio.run(load_web_content(url))
                module.content["scraped_content"] = "\n\n".join(
                    [doc.page_content for doc in scraped]
                )
                module.content["last_scraped"] = str(datetime.now())
                db.commit()
            except Exception as e:
                return {"error": f"Failed to scrape URL: {str(e)}"}

        docs.extend(scraped)

    elif module.module_type == "document":
        docs.extend(load_document(module.file_storage_key))

    else:
        return {"error": f"Unknown module type: {module.module_type}"}

    if not docs:
        return {"error": "No content to process"}

    # Chunk text
    chunks: List[Document] = text_processor.chunk_text(
        text="\n\n".join([doc.page_content for doc in docs])
    )

    chunk_records: List[Document] = []
    for idx, chunk_document in enumerate(chunks):
        chunk_document.metadata.update(
            {
                "source_type": module.module_type,
                "module_id": module.id,
                "module": module,
                "chunk_index": idx,
                "created_at": datetime.now(),
            }
        )
        chunk_records.append(chunk_document)

    vector_store.add_documents(chunk_records)

    return {
        "module_id": str(module.id),
        "chunks_created": len(chunk_records),
        "total_tokens": sum(chunk.metadata["token_count"] for chunk in chunks),
    }
