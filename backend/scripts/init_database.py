#!/usr/bin/env python
"""
Database initialization script.

This script ensures the database exists and is properly configured before
running migrations. It should be run before 'alembic upgrade head'.

Features:
- Creates database if it doesn't exist
- Installs required PostgreSQL extensions (pgvector)
- Safe to run multiple times (idempotent)
"""

import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.base_config import base_settings


def parse_database_url(url: str) -> dict:
    """
    Parse a database URL into components.

    Args:
        url: Database URL in format postgresql+psycopg2://user:pass@host:port/dbname

    Returns:
        Dictionary with connection parameters
    """
    parsed = urlparse(url)
    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
    }


def database_exists(cursor, database_name: str) -> bool:
    """
    Check if a database exists.

    Args:
        cursor: psycopg2 cursor
        database_name: Name of the database to check

    Returns:
        True if database exists, False otherwise
    """
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
    return cursor.fetchone() is not None


def extension_exists(cursor, extension_name: str) -> bool:
    """
    Check if a PostgreSQL extension is installed.

    Args:
        cursor: psycopg2 cursor
        extension_name: Name of the extension to check

    Returns:
        True if extension exists, False otherwise
    """
    cursor.execute("SELECT 1 FROM pg_extension WHERE extname = %s", (extension_name,))
    return cursor.fetchone() is not None


def create_database_if_not_exists(db_params: dict) -> None:
    """
    Create the database if it doesn't exist.

    Args:
        db_params: Database connection parameters
    """
    database_name = db_params["database"]

    # Connect to default 'postgres' database to create our database
    conn = psycopg2.connect(
        user=db_params["user"],
        password=db_params["password"],
        host=db_params["host"],
        port=db_params["port"],
        database="postgres",  # Connect to default database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        cursor = conn.cursor()

        if database_exists(cursor, database_name):
            print(f"✓ Database '{database_name}' already exists")
        else:
            print(f"Creating database '{database_name}'...")
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            print(f"✓ Database '{database_name}' created successfully")

        cursor.close()
    finally:
        conn.close()


def install_extensions(db_params: dict) -> None:
    """
    Install required PostgreSQL extensions.

    Args:
        db_params: Database connection parameters
    """
    extensions = ["vector"]  # pgvector extension

    conn = psycopg2.connect(
        user=db_params["user"],
        password=db_params["password"],
        host=db_params["host"],
        port=db_params["port"],
        database=db_params["database"],
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        cursor = conn.cursor()

        for ext in extensions:
            if extension_exists(cursor, ext):
                print(f"✓ Extension '{ext}' already installed")
            else:
                print(f"Installing extension '{ext}'...")
                try:
                    cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext}")
                    print(f"✓ Extension '{ext}' installed successfully")
                except psycopg2.Error as e:
                    print(f"⚠ Warning: Could not install extension '{ext}': {e}")
                    print(
                        "  You may need to install it manually with superuser privileges:"
                    )
                    print(
                        f"  psql -d {db_params['database']} -c 'CREATE EXTENSION {ext};'"
                    )

        cursor.close()
    finally:
        conn.close()


def main():
    """Main initialization routine."""
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)

    try:
        # Parse database URL
        db_url = base_settings.SYNC_DATABASE_URL
        db_params = parse_database_url(db_url)

        print(f"\nConnecting to PostgreSQL at {db_params['host']}:{db_params['port']}")
        print(f"Target database: {db_params['database']}\n")

        # Step 1: Create database if it doesn't exist
        create_database_if_not_exists(db_params)

        # Step 2: Install required extensions
        install_extensions(db_params)

        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)
        print("\nYou can now run migrations with:")
        print("  alembic upgrade head")
        print()

        return 0

    except psycopg2.OperationalError as e:
        print("\n✗ Error: Could not connect to PostgreSQL server")
        print(f"  {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Connection parameters in .env are correct")
        print("  3. Database user has appropriate permissions")
        return 1

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
