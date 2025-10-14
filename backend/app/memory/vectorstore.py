from langchain_postgres import PGEngine, PGVectorStore
from core.database import async_engine
from app.services.embeddings.model import EmbeddingModel
from langchain_postgres.v2.indexes import IVFFlatIndex
from langchain_postgres.v2.hybrid_search_config import (
    HybridSearchConfig,
    reciprocal_rank_fusion,
)

pg_engine = PGEngine.from_engine(engine=async_engine)
index = IVFFlatIndex(name="knowledge_chunks_ivfflat", lists=100)
hybrid_search_config = HybridSearchConfig(
    tsv_lang="pg_catalog.english",
    fusion_function=reciprocal_rank_fusion,
    fusion_function_parameters={
        "rrf_k": 60,
        "fetch_top_k": 10,
    },
)

# Set an existing table name
TABLE_NAME = "knowledge_chunks"

# Lazy loading cache
vector_store = None


# Initialize PGVectorStore with lazy loading
async def get_vector_store():
    """Initialize and return PGVectorStore instance with lazy loading."""
    global vector_store

    if vector_store is None:
        store = await PGVectorStore.create(
            engine=pg_engine,
            table_name=TABLE_NAME,
            embedding_service=EmbeddingModel.get_embedding_model(),
            # Connect to existing VectorStore by customizing below column names
            id_column="id",
            content_column="chunk_text",
            embedding_column="embedding",
            metadata_columns=[
                "module_id",
                "module",
                "chunk_index",
                "token_count",
                "module",
                "created_at",
            ],
            metadata_json_column="chunk_metadata",
            hybrid_search_config=hybrid_search_config,
        )
        await store.aapply_vector_index(index)
        vector_store = store

    return vector_store
