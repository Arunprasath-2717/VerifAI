"""Repository for User persistence and identity management."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
        """Retrieve user by username."""
        stmt = select(User).where(User.username == username.strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, email: str, username: str) -> User | None:
        """Check if an account exists matching either email or username."""
        clean_email = email.strip().lower()
        clean_username = username.strip()
        stmt = select(User).where(
            or_(User.email == clean_email, User.username == clean_username)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new User entity to the database."""
        now = datetime.now(UTC)
        if not user.created_at:
            user.created_at = now
        if not user.updated_at:
            user.updated_at = now

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create_firebase_user(
        self,
        firebase_uid: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> tuple[User, bool]:
        """Resolve or provision a User record from a validated Firebase UID.

        Uses deterministic UUIDv5 mapping so repeated logins for the same Firebase UID
        always map to the exact same internal user identifier.
        """
        deterministic_id = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{firebase_uid}")

        existing = await self.get_by_id(deterministic_id)
        if existing:
            existing.last_login_at = datetime.now(UTC)
            await self.session.commit()
            return existing, False

        user_email = (
            email.strip().lower()
            if email
            else f"firebase_{firebase_uid[:12]}@verifai.internal"
        )
        base_username = (
            display_name.strip().replace(" ", "_")
            if display_name
            else f"fb_{firebase_uid[:8]}"
        )
        user_name = base_username

        # Ensure username uniqueness
        candidate = await self.get_by_username(user_name)
        if candidate and candidate.id != deterministic_id:
            user_name = f"{base_username}_{deterministic_id.hex[:6]}"

        now = datetime.now(UTC)
        new_user = User(
            id=deterministic_id,
            email=user_email,
            username=user_name,
            hashed_password="",  # Firebase accounts do not have local passwords
            role=UserRole.USER.value,
            is_active=True,
            is_verified=True,
        )
        new_user.created_at = now
        new_user.updated_at = now

        self.session.add(new_user)
        try:
            await self.session.commit()
            await self.session.refresh(new_user)
            logger.info(
                "Auto-provisioned Firebase user %s (uid=%s)",
                deterministic_id,
                firebase_uid,
            )
            return new_user, True
        except Exception:
            await self.session.rollback()
            # If concurrent request already inserted the user, retrieve it
            retried = await self.get_by_id(deterministic_id)
            if retried:
                return retried, False
            raise
