"""SQLAlchemy model for persistent token accounting and audit trail."""

import uuid

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, TimestampMixin


class TokenUsage(Base, TimestampMixin):
    """Persisted token usage record for an LLM operation in an analysis."""

    __tablename__ = "token_usages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_estimated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    estimated_cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_token_usages_owner_created", "owner_id", "created_at"),
        Index("ix_token_usages_verif_op", "verification_id", "operation"),
    )
