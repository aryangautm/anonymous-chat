from langchain_postgres import PGEngine, PGVectorStore
from app.core.config import settings
from app.services.embeddings.model import EmbeddingModel
from langchain_postgres.v2.indexes import IVFFlatIndex
from langchain_postgres.v2.hybrid_search_config import (
    HybridSearchConfig,
    reciprocal_rank_fusion,
)

pg_engine = PGEngine.from_connection_string(url=settings.DATABASE_URL)
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
_vector_store = None


# Initialize PGVectorStore with lazy loading
def get_vector_store():
    """Initialize and return PGVectorStore instance with lazy loading."""
    global _vector_store

    if _vector_store is None:
        store = PGVectorStore.create_sync(
            engine=pg_engine,
            table_name=TABLE_NAME,
            embedding_service=EmbeddingModel.get_embedding_model(),
            # Connect to existing VectorStore by customizing below column names
            id_column="id",
            content_column="chunk_text",
            embedding_column="embedding",
            metadata_columns=[
                "module_id",
                "chunk_index",
                "token_count",
                "created_at",
            ],
            metadata_json_column="chunk_metadata",
            hybrid_search_config=hybrid_search_config,
        )

        try:
            store.apply_vector_index(index)
        except Exception as e:
            if "already exists" in str(e):
                print(f"Vector index already exists: SKIPPING")
            else:
                raise e

        _vector_store = store

    return _vector_store
