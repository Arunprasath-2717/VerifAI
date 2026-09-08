"""Database connection and health check foundation for PostgreSQL/Supabase."""

import asyncio
import logging
import time
from typing import Optional, Tuple
import asyncpg

logger = logging.getLogger("verifai.database")


class DatabaseManager:
    """Reusable PostgreSQL/Supabase connection and health check abstraction."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None
        self._is_connected: bool = False
        self._last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Return cached connection status."""
        return self._is_connected and self._pool is not None

    @property
    def last_error(self) -> Optional[str]:
        """Return the last connection error message if any."""
        return self._last_error

    def get_pool(self) -> Optional[asyncpg.Pool]:
        """Access the underlying connection pool for future database modules."""
        return self._pool

    async def connect(
        self,
        database_url: str,
        min_size: int = 1,
        max_size: int = 5,
        timeout: float = 5.0,
    ) -> bool:
        """Initialize connection pool to PostgreSQL/Supabase.

        Fails gracefully on connectivity errors to prevent crashing the server
        in local development when a database is not yet provisioned.
        """
        if not database_url:
            self._is_connected = False
            self._last_error = "DATABASE_URL is not configured"
            logger.warning("Database connection skipped: DATABASE_URL not set.")
            return False

        # Normalize postgres:// to postgresql:// for asyncpg
        dsn = database_url
        if dsn.startswith("postgres://"):
            dsn = "postgresql://" + dsn[len("postgres://") :]

        try:
            logger.info("Establishing database connection pool...")
            self._pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=min_size,
                max_size=max_size,
                timeout=timeout,
                command_timeout=timeout,
            )
            # Verify connectivity with a ping query
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._is_connected = True
            self._last_error = None
            logger.info("Database connection pool established successfully.")
            return True
        except Exception as exc:
            self._is_connected = False
            self._last_error = str(exc)
            logger.warning("Database connection failed (non-fatal for startup): %s", exc)
            return False

    async def disconnect(self) -> None:
        """Gracefully close the connection pool on application shutdown."""
        if self._pool is not None:
            logger.info("Closing database connection pool...")
            try:
                await self._pool.close()
            except Exception as exc:
                logger.error("Error closing database connection pool: %s", exc)
            finally:
                self._pool = None
                self._is_connected = False
                logger.info("Database connection pool closed.")

    async def check_health(self, timeout: float = 2.0) -> Tuple[bool, str, float]:
        """Verify database connectivity with a live query.

        Returns:
            (is_healthy: bool, status_message: str, latency_ms: float)
        """
        if self._pool is None:
            return False, "disconnected", 0.0

        start_time = time.time()
        try:
            async with asyncio.timeout(timeout):
                async with self._pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    if result == 1:
                        latency_ms = round((time.time() - start_time) * 1000, 2)
                        self._is_connected = True
                        return True, "connected", latency_ms
                    return False, "unexpected query response", 0.0
        except Exception as exc:
            self._is_connected = False
            self._last_error = str(exc)
            return False, "disconnected", 0.0


# Global singleton instance
database_manager = DatabaseManager()
