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


settings = Settings()
