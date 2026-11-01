"""Persistent, encrypted BYOK provider credentials owned by a single user."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, TimestampMixin


class UserProviderCredential(Base, TimestampMixin):
    """One encrypted API credential per (owner, provider).

    ``encrypted_api_key`` holds Fernet ciphertext only. The plaintext key is
    never stored, returned, or logged.
    """

    __tablename__ = "user_provider_credentials"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_api_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    validation_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NOT_TESTED"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "provider_id", name="uq_user_provider_credential"),
        Index("ix_user_provider_credentials_user", "user_id", "provider_id"),
    )
