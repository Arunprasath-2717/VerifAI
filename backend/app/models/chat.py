"""SQLAlchemy 2.x domain models for Conversations, Messages, and Multi-LLM Runs."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.verification import VerificationJob


class Conversation(Base, TimestampMixin):
    """Represents a multi-turn conversation thread owned by a user."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        default="New Conversation",
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sequence_number",
    )
    llm_runs: Mapped[list["LLMRun"]] = relationship(
        "LLMRun",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="LLMRun.started_at",
    )

    __table_args__ = (
        Index("ix_conversations_owner_created", "owner_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, owner='{self.owner_id}', "
            f"title='{self.title[:30]}')>"
        )


class Message(Base, TimestampMixin):
    """Represents a single message in a conversation thread."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,  # USER, ASSISTANT, SYSTEM
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    llm_runs: Mapped[list["LLMRun"]] = relationship(
        "LLMRun",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_messages_conv_sequence",
            "conversation_id",
            "sequence_number",
        ),
        Index("ix_messages_owner_created", "owner_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, role='{self.role}', seq={self.sequence_number})>"
        )


class LLMRun(Base):
    """Represents an execution of an individual LLM provider/model for a prompt."""

    __tablename__ = "llm_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,  # openai, anthropic, google, ollama, local
    )
    model_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",  # PENDING, STREAMING, COMPLETED, FAILED, UNAVAILABLE
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    verification_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("verifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="llm_runs",
    )
    message: Mapped["Message | None"] = relationship(
        "Message",
        back_populates="llm_runs",
    )
    verification: Mapped["VerificationJob | None"] = relationship(
        "VerificationJob",
        foreign_keys=[verification_id],
    )

    __table_args__ = (
        Index("ix_llm_runs_owner_created", "owner_id", "started_at"),
        Index("ix_llm_runs_provider_model", "provider", "model_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<LLMRun(id={self.id}, model='{self.model_name}', status='{self.status}')>"
        )
