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

    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    GEMINI_API_KEY: str
    GEMINI_CHAT_LLM: str = "gemini-2.5-flash"


settings = Settings()
