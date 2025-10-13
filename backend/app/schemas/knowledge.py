from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal


# Module type definitions
ModuleType = Literal[
    "bio",
    "qna",
    "text_block",
    "url_source",
    "document",
    "resume",
    "services",
    "social_media",
]


class KnowledgeModuleBase(BaseModel):
    """Base knowledge module schema."""

    module_type: ModuleType
    title: str | None = None
    content: dict = Field(..., description="Module-specific content structure")
    priority: int = Field(default=1, ge=1, le=10)
    is_active: bool = True
    metadata: dict | None = None


class KnowledgeModuleCreate(KnowledgeModuleBase):
    """Schema for creating a knowledge module."""

    pass


class KnowledgeModuleUpdate(BaseModel):
    """Schema for updating a knowledge module."""

    title: str | None = None
    content: dict | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    is_active: bool | None = None
    metadata: dict | None = None


class KnowledgeModuleResponse(KnowledgeModuleBase):
    """Schema for knowledge module response."""

    id: UUID
    persona_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeChunkResponse(BaseModel):
    """Schema for knowledge chunk response."""

    id: UUID
    module_id: UUID
    chunk_text: str
    chunk_index: int
    token_count: int | None
    metadata: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
