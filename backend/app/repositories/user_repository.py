"""User repository for application database operations."""

import logging
import uuid
from typing import Any, Dict, Optional, Union
from app.core.database import DatabaseManager, database_manager

logger = logging.getLogger("verifai.repositories.user")


class UserRepository:
    """Repository handling CRUD operations on the application users table."""

    def __init__(self, db_manager: DatabaseManager = database_manager) -> None:
        self.db = db_manager

    def _to_uuid(self, user_id: Union[str, uuid.UUID]) -> uuid.UUID:
        """Ensure user_id is a valid UUID object."""
        if isinstance(user_id, uuid.UUID):
            return user_id
        return uuid.UUID(str(user_id))

    async def create_user(
        self,
        user_id: Union[str, uuid.UUID],
        email: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new user profile record synchronized with Supabase Auth."""
        uid = self._to_uuid(user_id)
        query = """
            INSERT INTO users (id, email, display_name, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            RETURNING id, email, display_name, created_at, updated_at;
        """
        pool = self.db.get_pool()
        if pool is None:
            raise RuntimeError("Database connection is not available")

        async with pool.acquire() as conn:
            record = await conn.fetchrow(query, uid, email.lower().strip(), display_name)
            if record is None:
                raise RuntimeError("Failed to insert user record")
            return dict(record)

    async def get_user_by_id(
        self, user_id: Union[str, uuid.UUID]
    ) -> Optional[Dict[str, Any]]:
        """Fetch user profile by UUID."""
        uid = self._to_uuid(user_id)
        query = """
            SELECT id, email, display_name, created_at, updated_at
            FROM users
            WHERE id = $1;
        """
        pool = self.db.get_pool()
        if pool is None:
            raise RuntimeError("Database connection is not available")

        async with pool.acquire() as conn:
            record = await conn.fetchrow(query, uid)
            return dict(record) if record else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile by email address."""
        query = """
            SELECT id, email, display_name, created_at, updated_at
            FROM users
            WHERE email = $1;
        """
        pool = self.db.get_pool()
        if pool is None:
            raise RuntimeError("Database connection is not available")

        async with pool.acquire() as conn:
            record = await conn.fetchrow(query, email.lower().strip())
            return dict(record) if record else None

    async def update_user(
        self, user_id: Union[str, uuid.UUID], display_name: str
    ) -> Optional[Dict[str, Any]]:
        """Update display name and updated_at timestamp."""
        uid = self._to_uuid(user_id)
        query = """
            UPDATE users
            SET display_name = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING id, email, display_name, created_at, updated_at;
        """
        pool = self.db.get_pool()
        if pool is None:
            raise RuntimeError("Database connection is not available")

        async with pool.acquire() as conn:
            record = await conn.fetchrow(query, uid, display_name)
            return dict(record) if record else None

    async def delete_user(self, user_id: Union[str, uuid.UUID]) -> bool:
        """Delete user profile from database."""
        uid = self._to_uuid(user_id)
        query = "DELETE FROM users WHERE id = $1;"
        pool = self.db.get_pool()
        if pool is None:
            raise RuntimeError("Database connection is not available")

        async with pool.acquire() as conn:
            result = await conn.execute(query, uid)
            # asyncpg returns "DELETE <count>"
            return result == "DELETE 1"


# Default singleton instance
user_repository = UserRepository()
