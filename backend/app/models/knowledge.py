import uuid
from enum import Enum as PyEnum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class ProcessingStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class KnowledgeModule(Base):
    """
    Knowledge module for organizing persona data.

    Different module types store data differently in the JSONB content field.
    """

    __tablename__ = "knowledge_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(JSONB, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    module_metadata = Column(JSONB, nullable=True)
    file_storage_key = Column(String(255), nullable=True)
    processing_status = Column(
        Enum(
            ProcessingStatus,
            name="processing_status",
            create_type=True,
            native_enum=True,
        ),
        default=ProcessingStatus.PENDING,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    persona = relationship("Persona", back_populates="knowledge_modules")
    chunks = relationship(
        "KnowledgeChunk", back_populates="module", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<KnowledgeModule(id={self.id}, type={self.module_type})>"


class KnowledgeChunk(Base):
    """
    Text chunks with embeddings for RAG.

    Each knowledge module can have multiple chunks for vector search.
    """

    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    token_count = Column(Integer, nullable=True)
    chunk_metadata = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    module = relationship("KnowledgeModule", back_populates="chunks")

    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, index={self.chunk_index})>"
