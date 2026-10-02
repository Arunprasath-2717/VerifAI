"""Common dependency injection providers for FastAPI."""

import logging
import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import _EPHEMERAL_USERS, decode_access_token
from app.models.user import User
from app.schemas.auth import UserRole

logger = logging.getLogger("verifai.dependencies")
http_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_settings(settings: Settings = Depends(get_settings)) -> Settings:
    """Provide current application settings as a FastAPI dependency."""
    return settings


async def get_async_session(
    session_maker: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous database session as a FastAPI dependency."""
    async for session in _get_async_session(session_maker=session_maker):
        yield session


# Alias for backward compatibility
get_db_session = get_async_session


async def get_optional_db_session(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession | None, None]:
    """Provide an async database session if configured, or None for ephemeral runs."""
    if not settings.DATABASE_URL:
        yield None
        return

    try:
        async for session in _get_async_session():
            yield session
    except Exception as exc:
        logger.warning(
            "Could not establish database session: %s. Proceeding ephemerally.",
            type(exc).__name__,
        )
        yield None


def get_supabase_client(
    settings: Settings = Depends(get_settings),
):
    """Provide configured SupabaseClient as a FastAPI dependency."""
    from app.core.supabase import SupabaseClient

    return SupabaseClient.from_settings(settings=settings)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_scheme),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    """Authenticate request using Bearer JWT token and resolve User entity."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedError(
            message="Authentication required. Please provide a valid Bearer token.",
            details={"scheme": "Bearer"},
        )

    token = credentials.credentials.strip()
    payload = decode_access_token(token, settings=settings)

    sub = payload.get("sub")
    is_firebase_token = str(payload.get("iss", "")).startswith(
        "https://securetoken.google.com"
    )

    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError) as exc:
        if is_firebase_token:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{sub}")
        else:
            raise UnauthorizedError(
                message="Token subject is not a valid user identifier.",
                details={"sub": str(sub)},
            ) from exc

    user: User | None = None

    if db is not None:
        stmt = select(User).where(User.id == user_uuid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    else:
        user = _EPHEMERAL_USERS.get(user_uuid)

    if user is None and is_firebase_token:
        # Auto-provision user account from validated Firebase ID token
        email = str(payload.get("email") or f"{sub}@firebase.user")
        username = str(payload.get("name") or email.split("@")[0]).replace(" ", "_")
        user = User(
            id=user_uuid,
            email=email,
            username=username,
            hashed_password="",
            role="USER",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        if db is not None:
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            _EPHEMERAL_USERS[user_uuid] = user

    if user is None:
        raise UnauthorizedError(
            message="Authenticated user account does not exist.",
            details={"user_id": str(user_uuid)},
        )

    if not user.is_active:
        raise UnauthorizedError(
            message="User account is deactivated.",
            details={"user_id": str(user_uuid)},
        )

    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_scheme),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Resolve authenticated user if Bearer token present, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    return await get_current_user(credentials=credentials, db=db, settings=settings)


def require_roles(
    allowed_roles: list[UserRole | str],
) -> Callable[..., Any]:
    """Dependency factory enforcing explicit Role-Based Access Control (RBAC)."""
    normalized_roles = {
        r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles
    }

    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in normalized_roles:
            logger.warning(
                "Access denied for user %s with role '%s'. Allowed: %s",
                current_user.id,
                current_user.role,
                normalized_roles,
            )
            roles_str = ", ".join(sorted(normalized_roles))
            raise ForbiddenError(
                message=f"Insufficient permissions. Required role: {roles_str}",
                details={
                    "user_role": current_user.role,
                    "allowed_roles": sorted(normalized_roles),
                },
            )
        return current_user

    return _role_checker


def resolve_effective_owner(
    current_user: User | None,
    client_owner_id: str | None,
    settings: Settings,
) -> str:
    """Determine effective owner/namespace ID with strict security enforcement.

    1. Authenticated non-admin: strictly forces user.id (rejects spoofing/IDOR).
    2. Authenticated admin: allows inspecting target namespace or defaults to admin.id.
    3. Unauthenticated: strictly forbidden in production; permitted only in dev/test.
    """
    if current_user is not None:
        user_id_str = str(current_user.id)
        role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if role_str == "ADMIN":
            if client_owner_id and client_owner_id.strip():
                return client_owner_id.strip()
            return user_id_str

        # Non-admin user: prevent IDOR/spoofing of another user's namespace
        if (
            client_owner_id
            and client_owner_id.strip()
            and client_owner_id.strip() != user_id_str
        ):
            logger.warning(
                "IDOR attempt: User %s attempted to access namespace '%s'",
                user_id_str,
                client_owner_id,
            )
            raise ForbiddenError(
                message=(
                    "Cannot access or specify resources outside your user namespace."
                ),
                details={
                    "user_id": user_id_str,
                    "requested_owner_id": client_owner_id,
                },
            )
        return user_id_str

    # Unauthenticated path: strictly development/testing only
    is_dev = (
        settings.ENVIRONMENT in ("development", "test", "testing") or settings.DEBUG
    )
    if not is_dev:
        raise UnauthorizedError(
            message="Authentication required in production environment.",
            details={"environment": settings.ENVIRONMENT},
        )

    if client_owner_id and client_owner_id.strip():
        return client_owner_id.strip()
    return settings.DEFAULT_OWNER_ID
