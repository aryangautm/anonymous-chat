import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Conversation(Base):
    """
    Conversation session between anonymous visitor and AI persona.

    The conversation ID is also used as the session_id for visitors.
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visitor_metadata = Column(JSONB, nullable=True)
    # Stores non-identifying info: {"browser": "Chrome", "device": "Desktop"}
    started_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    last_activity_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)

    # Relationships
    persona = relationship("Persona", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, persona={self.persona_id})>"


class Message(Base):
    """
    Individual message in a conversation.
    """

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender = Column(String(10), nullable=False)  # 'VISITOR' or 'AI'
    content = Column(Text, nullable=False)
    sources_used = Column(JSONB, nullable=True)
    # For AI: [{"chunk_id": "...", "relevance_score": 0.95}]
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    message_metadata = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender})>"


class OwnerFeedback(Base):
    """
    Owner feedback for improving AI responses.
    """

    __tablename__ = "owner_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    visitor_question = Column(Text, nullable=False)
    original_response = Column(Text, nullable=False)
    improved_response = Column(Text, nullable=False)
    feedback_notes = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<OwnerFeedback(id={self.id}, applied={self.is_applied})>"
