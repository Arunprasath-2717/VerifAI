"""Database models for namespace-isolated private Knowledge Base (KB)."""

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin


class KnowledgeDocument(Base, TimestampMixin):
    """Represents an ingested document stored in a private namespace."""

    __tablename__ = "knowledge_documents"

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
    filename: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index",
    )

    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "content_hash",
            name="uq_knowledge_doc_owner_hash",
        ),
        Index("ix_knowledge_docs_owner_created", "owner_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeDocument(id={self.id}, owner='{self.owner_id}', "
            f"title='{self.title}', chunks={len(self.chunks) if self.chunks else 0})>"
        )


class KnowledgeChunk(Base, TimestampMixin):
    """Represents a discrete text chunk of a knowledge document."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    start_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    end_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationship
    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
    )

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunk_doc_index",
        ),
        Index("ix_knowledge_chunks_owner_doc", "owner_id", "document_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeChunk(id={self.id}, doc_id={self.document_id}, "
            f"index={self.chunk_index})>"
        )
