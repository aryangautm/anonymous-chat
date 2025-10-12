"""
SQLAlchemy declarative base.

This module contains only the Base class to avoid circular imports
and to allow Alembic to import Base without triggering database connections.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
