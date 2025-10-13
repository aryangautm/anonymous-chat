from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

EMBEDDING_MODEL_NAME = settings.EMBEDDING_MODEL


class EmbeddingModel:
    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            cls._embedding_model = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME
            )
            print(f"Embedding model loaded")
        return cls._embedding_model
