"""Common dependency injection providers for FastAPI."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session


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


def get_supabase_client(
    settings: Settings = Depends(get_settings),
):
    """Provide configured SupabaseClient as a FastAPI dependency."""
    from app.core.supabase import SupabaseClient

    return SupabaseClient.from_settings(settings=settings)
