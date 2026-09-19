"""Asynchronous PostgreSQL database infrastructure using SQLAlchemy 2.x and asyncpg."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings

logger = logging.getLogger("verifai.database")

# Global engine reference for application lifespan management
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create or return the configured SQLAlchemy AsyncEngine.

    Connections are established lazily upon first query/transaction;
    calling this function does not perform any network operations.
    """
    global _engine
    if _engine is not None:
        return _engine

    app_settings = settings or get_settings()
    if not app_settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured.")

    db_url = app_settings.DATABASE_URL.get_secret_value()

    # Configure pool parameters safely based on dialect
    pool_kwargs: dict[str, Any] = {
        "echo": False,  # Prevent credential and query logging in production/dev
        "pool_pre_ping": True,
    }

    if "sqlite" not in db_url:
        # Conservative pool settings for PostgreSQL + asyncpg
        pool_kwargs.update(
            {
                "pool_size": app_settings.DATABASE_POOL_SIZE,
                "max_overflow": app_settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": app_settings.DATABASE_POOL_TIMEOUT,
            }
        )

    _engine = create_async_engine(db_url, **pool_kwargs)
    return _engine


def get_async_session_maker(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create or return the configured async session factory."""
    global _session_maker
    if _session_maker is not None and engine is None:
        return _session_maker

    target_engine = engine or get_async_engine()
    _session_maker = async_sessionmaker(
        bind=target_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _session_maker


async def dispose_async_engine(engine: AsyncEngine | None = None) -> None:
    """Gracefully dispose the async engine and close pooled connections."""
    global _engine, _session_maker
    target_engine = engine or _engine
    if target_engine is not None:
        try:
            await target_engine.dispose()
        except Exception:
            # Catch synchronous/mocked disposal exceptions gracefully
            pass
        if target_engine == _engine:
            _engine = None
            _session_maker = None


async def get_async_session(
    session_maker: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency providing an isolated asynchronous database session.

    Transactions must be explicitly committed or rolled back by the domain
    service/caller. The dependency guarantees session closure upon completion.
    """
    maker = session_maker or get_async_session_maker()
    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connectivity(
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
) -> dict[str, Any]:
    """Probe database connectivity safely using a harmless SELECT 1 query.

    Returns structured status without leaking credentials, connection URLs,
    or internal server stack traces.
    """
    app_settings = settings or get_settings()

    # State 1: Database configuration absent
    if not app_settings.DATABASE_URL:
        return {
            "configured": False,
            "status": "unconfigured",
        }

    # State 2: Database configured, attempt probe with short timeout
    target_engine = engine
    if target_engine is None:
        try:
            target_engine = get_async_engine(app_settings)
        except Exception as exc:
            logger.warning(
                "Failed to initialize database engine for connectivity check: %s",
                type(exc).__name__,
            )
            return {
                "configured": True,
                "status": "unavailable",
            }

    try:

        async def _probe() -> None:
            async with target_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        timeout = app_settings.DATABASE_CONNECT_TIMEOUT
        await asyncio.wait_for(_probe(), timeout=timeout)
        return {
            "configured": True,
            "status": "available",
        }
    except Exception as exc:
        # Log only exception class name; never log connection strings or server details
        logger.warning(
            "Database connectivity check failed: %s",
            type(exc).__name__,
        )
        return {
            "configured": True,
            "status": "unavailable",
        }
