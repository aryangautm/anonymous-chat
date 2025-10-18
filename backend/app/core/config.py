"""
Application configuration and settings.

This module extends the base configuration with additional settings required
for the FastAPI application to run, such as CORS origins and authentication keys.
"""

from .base_config import BaseConfig


class Settings(BaseConfig):
    """
    Complete application settings including all environment variables.

    Inherits from BaseConfig to ensure database settings are available,
    and adds application-specific settings like CORS and authentication.
    """

    CORS_ORIGINS: str
    APP_AUTH_KEY: str

    # Redis Configuration (for Celery)
    REDIS_URL: str
    REDIS_RATE_LIMIT_DB: int = 1

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_S3_BUCKET_NAME: str
    AWS_REGION: str
    AWS_S3_INTERNAL_ENDPOINT: str
    AWS_S3_PUBLIC_URL: str

    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    GEMINI_API_KEY: str
    GEMINI_CHAT_LLM: str = "gemini-2.5-flash"

    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 50


settings = Settings()
