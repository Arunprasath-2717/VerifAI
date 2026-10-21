"""Common dependency injection providers for FastAPI."""

import logging
from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session
from app.core.database import get_async_session_maker

logger = logging.getLogger("verifai.dependencies")


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
    """Provide an async database session if configured, or None for ephemeral runs.

    Only session-factory construction is guarded. Exceptions raised by the
    endpoint are thrown back into this generator at ``yield`` and must
    propagate unchanged, so the ``yield`` is never wrapped in ``try/except``.
    """
    if not settings.DATABASE_URL:
        yield None
        return

    try:
        maker = get_async_session_maker()
    except Exception as exc:
        logger.warning(
            "Could not initialize database session factory: %s. Proceeding "
            "ephemerally.",
            type(exc).__name__,
        )
        yield None
        return

    async with maker() as session:
        yield session


def get_supabase_client(
    settings: Settings = Depends(get_settings),
):
    """Provide configured SupabaseClient as a FastAPI dependency."""
    from app.core.supabase import SupabaseClient

    return SupabaseClient.from_settings(settings=settings)
