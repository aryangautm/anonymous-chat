"""
Base configuration for Alembic migrations.

This module provides minimal settings required for Alembic to run database migrations.
"""

from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class BaseConfig(BaseSettings):

    DATABASE_URL: str

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """
        Convert async database URL to sync URL for Alembic migrations.

        Alembic requires a synchronous database connection, so we replace
        asyncpg with psycopg2 driver.
        """
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance for Alembic
base_settings = BaseConfig()
