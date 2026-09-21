"""SQLAlchemy 2.x domain model for ingested payloads and extension captures."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.verification import VerificationJob


class IngestedPayload(Base, TimestampMixin):
    """Represents captured AI-generated text received via extension, chat, or API."""

    __tablename__ = "ingested_payloads"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="CHROME_EXTENSION",
        index=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    captured_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    session_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    client_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    capture_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="RECEIVED",
        index=True,
    )
    verification_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("verifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    verification: Mapped["VerificationJob | None"] = relationship(
        "VerificationJob",
        foreign_keys=[verification_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_ingested_payloads_created_at", "created_at"),
        Index("ix_ingested_payloads_source_status", "source", "status"),
    )
