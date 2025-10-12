"""
Alembic migration environment configuration.

This module configures Alembic to work with our FastAPI application,
loading database settings from the environment and importing all models
for autogenerate support.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add the parent directory to sys.path to enable imports from app module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import base config for database URL (only requires DATABASE_URL)
from app.core.base_config import base_settings

# Import all models here to ensure they're registered with Base.metadata
# This is critical for autogenerate to detect model changes
from app.models import RequestLog  # noqa: F401

# Import Base separately to avoid triggering engine creation
from app.models.base import Base

# Add any new models here as they're created
# from app.models import User, Message, etc.  # noqa: F401

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the SQLAlchemy URL from our base settings
config.set_main_option("sqlalchemy.url", base_settings.SYNC_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.

    Offline mode is useful for generating SQL scripts without a database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Production settings
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect server default changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.

    This is the default mode for running migrations against a live database.
    """
    # Use NullPool for migrations to avoid connection pooling issues
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Production settings for better migration detection
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect server default changes
            # Include schemas if you're using them
            # include_schemas=True,
            # Render items for batch migrations (useful for SQLite)
            render_as_batch=False,  # Set to True if using SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run based on Alembic's configuration
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
