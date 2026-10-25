"""SQLAlchemy 2.x domain model for User Consent audit records."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin


class UserConsent(Base, TimestampMixin):
    """Immutable audit record of user acceptance of Terms & Conditions and
    Privacy Policy."""

    __tablename__ = "user_consents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    terms_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    privacy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    action_source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="signup_form",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # Relationship back to the User model
    user = relationship("User", backref="consents")

    __table_args__ = (
        Index("ix_user_consents_user_consented", "user_id", "consented_at"),
        Index("ix_user_consents_versions", "terms_version", "privacy_version"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserConsent(id={self.id}, user_id={self.user_id}, "
            f"terms_version='{self.terms_version}', "
            f"privacy_version='{self.privacy_version}', "
            f"consented_at={self.consented_at})>"
        )
