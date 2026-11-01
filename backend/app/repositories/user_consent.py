"""Asynchronous repository for UserConsent audit records."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_consent import UserConsent

logger = logging.getLogger("verifai.repositories.user_consent")


class UserConsentRepository:
    """Encapsulates database operations for immutable legal consent records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_consent(
        self,
        user_id: uuid.UUID,
        terms_version: str,
        privacy_version: str,
        action_source: str = "signup_form",
        ip_address: str | None = None,
        user_agent: str | None = None,
        *,
        commit: bool = True,
    ) -> UserConsent:
        """Create and persist an authoritative, UTC-timestamped user consent record."""
        now = datetime.now(UTC)
        consent = UserConsent(
            id=uuid.uuid4(),
            user_id=user_id,
            terms_version=terms_version.strip(),
            privacy_version=privacy_version.strip(),
            consented_at=now,
            action_source=action_source.strip(),
            ip_address=ip_address.strip() if ip_address else None,
            user_agent=user_agent[:512].strip() if user_agent else None,
        )
        consent.created_at = now
        consent.updated_at = now

        self.session.add(consent)
        await self.session.flush()
        if commit:
            await self.session.commit()
            await self.session.refresh(consent)

        logger.info(
            "Recorded legal consent: user_id=%s, terms_v=%s, privacy_v=%s, source=%s",
            user_id,
            terms_version,
            privacy_version,
            action_source,
        )
        return consent

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[UserConsent]:
        """Retrieve all consent records for a specific user, ordered
        chronologically descending."""
        stmt = (
            select(UserConsent)
            .where(UserConsent.user_id == user_id)
            .order_by(UserConsent.consented_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_user_id(self, user_id: uuid.UUID) -> UserConsent | None:
        """Retrieve the most recent consent record for a specific user."""
        stmt = (
            select(UserConsent)
            .where(UserConsent.user_id == user_id)
            .order_by(UserConsent.consented_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def has_consented_to_current(
        self, user_id: uuid.UUID, current_terms_v: str, current_privacy_v: str
    ) -> bool:
        """Verify whether user has an existing record agreeing to the specified
        active versions."""
        latest = await self.get_latest_by_user_id(user_id)
        if not latest:
            return False
        return (
            latest.terms_version == current_terms_v
            and latest.privacy_version == current_privacy_v
        )
