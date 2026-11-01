"""Repository for User persistence and identity management."""

import logging
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.user import User
from app.schemas.auth import UserRole

logger = logging.getLogger("verifai.repositories.user")


class UserRepository:
    """Manages database persistence for User accounts and authentication identities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by normalized email address."""
        stmt = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a username case-insensitively, including legacy accounts."""
        stmt = select(User).where(func.lower(User.username) == username.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, email: str, username: str) -> User | None:
        """Check if an account exists matching either email or username."""
        clean_email = email.strip().lower()
        clean_username = username.strip()
        stmt = select(User).where(
            or_(
                User.email == clean_email,
                func.lower(User.username) == clean_username.lower(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User, *, commit: bool = True) -> User:
        """Persist a new User entity to the database."""
        now = datetime.now(UTC)
        if not user.created_at:
            user.created_at = now
        if not user.updated_at:
            user.updated_at = now

        self.session.add(user)
        await self.session.flush()
        if commit:
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def get_or_create_firebase_user(
        self,
        firebase_uid: str,
        email: str | None = None,
        display_name: str | None = None,
        *,
        commit: bool = True,
    ) -> tuple[User, bool]:
        """Resolve or provision a User record from a validated Firebase UID.

        Uses deterministic UUIDv5 mapping so repeated logins for the same Firebase UID
        always map to the exact same internal user identifier.
        """
        deterministic_id = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{firebase_uid}")

        existing = await self.get_by_id(deterministic_id)
        if existing:
            existing.last_login_at = datetime.now(UTC)
            if commit:
                await self.session.commit()
            return existing, False

        user_email = (
            email.strip().lower()
            if email
            else f"firebase_{firebase_uid[:12]}@verifai.internal"
        )

        # A Firebase identity must never silently inherit an unrelated local
        # account's role, data, or sessions merely by claiming its email.
        # Linking accounts requires a separate, authenticated linking flow.
        if await self.get_by_email(user_email):
            raise ConflictError(
                message="Email already belongs to another account.",
                details={"reason": "firebase_email_conflict"},
            )

        suggested = (
            display_name.strip().lower().replace(" ", "_") if display_name else ""
        )
        base_username = re.sub(r"[^a-z0-9_-]", "_", suggested).strip("_-")
        if len(base_username) < 3:
            base_username = f"fb_{deterministic_id.hex[:10]}"
        base_username = base_username[:48]
        user_name = base_username
        # The database unique index remains the authority for concurrent writes.
        candidate = await self.get_by_username(user_name)
        if candidate and candidate.id != deterministic_id:
            user_name = f"{base_username}_{deterministic_id.hex[:12]}"

        now = datetime.now(UTC)
        new_user = User(
            id=deterministic_id,
            email=user_email,
            username=user_name,
            hashed_password="",  # nosec B106 - Firebase-only, no local password
            role=UserRole.USER.value,
            is_active=True,
            is_verified=True,
        )
        new_user.created_at = now
        new_user.updated_at = now

        self.session.add(new_user)
        try:
            await self.session.flush()
            if commit:
                await self.session.commit()
                await self.session.refresh(new_user)
            logger.info(
                "Auto-provisioned Firebase user %s (uid=%s)",
                deterministic_id,
                firebase_uid,
            )
            return new_user, True
        except Exception as exc:
            await self.session.rollback()
            # If concurrent request already inserted the user, retrieve it
            retried = await self.get_by_id(deterministic_id)
            if retried:
                return retried, False
            # Avoid linking or elevating an unrelated account if a concurrent
            # signup reserved the email while this transaction was pending.
            if await self.get_by_email(user_email):
                raise ConflictError(
                    message="Email already belongs to another account.",
                    details={"reason": "firebase_email_conflict"},
                ) from exc
            raise
