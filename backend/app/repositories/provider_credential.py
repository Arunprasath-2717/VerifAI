"""Owner-scoped persistence for encrypted BYOK provider credentials.

Every query takes ``user_id`` and filters on it, so a caller cannot read or
modify another user's credential by supplying a different provider ID.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider_credential import UserProviderCredential

logger = logging.getLogger("verifai.repositories.provider_credential")


class ProviderCredentialRepository:
    """Persistence operations scoped to one owner."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self, user_id: uuid.UUID, provider_id: str
    ) -> UserProviderCredential | None:
        stmt = select(UserProviderCredential).where(
            UserProviderCredential.user_id == user_id,
            UserProviderCredential.provider_id == provider_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[UserProviderCredential]:
        stmt = (
            select(UserProviderCredential)
            .where(UserProviderCredential.user_id == user_id)
            .order_by(UserProviderCredential.provider_id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def upsert(
        self,
        user_id: uuid.UUID,
        provider_id: str,
        encrypted_api_key: str,
        key_hint: str,
        base_url: str | None,
        organization_id: str | None,
    ) -> UserProviderCredential:
        """Insert or replace the caller's credential for a provider."""
        now = datetime.now(UTC)
        row = await self.get(user_id, provider_id)
        if row is None:
            row = UserProviderCredential(
                id=uuid.uuid4(),
                user_id=user_id,
                provider_id=provider_id,
                created_at=now,
            )
            self.session.add(row)
        row.encrypted_api_key = encrypted_api_key
        row.key_hint = key_hint
        row.base_url = base_url
        row.organization_id = organization_id
        row.validation_status = "NOT_TESTED"
        row.last_validated_at = None
        row.updated_at = now
        await self.session.commit()
        await self.session.refresh(row)
        logger.info("Stored provider credential: provider=%s", provider_id)
        return row

    async def mark_validated(
        self, row: UserProviderCredential, status: str
    ) -> UserProviderCredential:
        row.validation_status = status
        row.last_validated_at = datetime.now(UTC)
        row.updated_at = row.last_validated_at
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def delete(self, user_id: uuid.UUID, provider_id: str) -> bool:
        stmt = delete(UserProviderCredential).where(
            UserProviderCredential.user_id == user_id,
            UserProviderCredential.provider_id == provider_id,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        assert isinstance(result, CursorResult)
        return (result.rowcount or 0) > 0
