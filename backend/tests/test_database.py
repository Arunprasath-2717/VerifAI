"""Tests for DatabaseManager abstraction and health checks."""

from unittest.mock import AsyncMock, patch
import pytest
from app.core.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_manager_empty_url():
    """Verify connect returns False when DATABASE_URL is empty."""
    dm = DatabaseManager()
    result = await dm.connect(database_url="")
    assert result is False
    assert dm.is_connected is False
    assert dm.last_error == "DATABASE_URL is not configured"


@pytest.mark.asyncio
async def test_database_manager_health_when_disconnected():
    """Verify check_health returns disconnected when pool is None."""
    dm = DatabaseManager()
    healthy, status_msg, latency = await dm.check_health()
    assert healthy is False
    assert status_msg == "disconnected"
    assert latency == 0.0


@pytest.mark.asyncio
async def test_database_manager_connection_failure():
    """Verify connect handles connection errors gracefully without raising unhandled exceptions."""
    dm = DatabaseManager()
    with patch("asyncpg.create_pool", side_effect=Exception("Failed to reach Postgres host")):
        result = await dm.connect("postgresql://user:pass@nonexistent-host:5432/db")
        assert result is False
        assert dm.is_connected is False
        assert "Failed to reach Postgres host" in (dm.last_error or "")


@pytest.mark.asyncio
async def test_database_manager_successful_connection_and_health():
    """Verify connect, check_health, and disconnect with mocked asyncpg pool."""
    dm = DatabaseManager()

    # Mock connection and pool
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 1

    class MockPoolAcquireContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    from unittest.mock import MagicMock
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockPoolAcquireContext()
    mock_pool.close = AsyncMock()

    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        connected = await dm.connect("postgres://user:pass@supabase.co:5432/verifai")
        assert connected is True
        assert dm.is_connected is True
        assert dm.get_pool() == mock_pool

        healthy, status_msg, latency = await dm.check_health()
        assert healthy is True
        assert status_msg == "connected"
        assert latency >= 0.0

        await dm.disconnect()
        assert dm.is_connected is False
        assert dm.get_pool() is None
        mock_pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_disconnect_handles_error():
    """Verify disconnect handles close exceptions gracefully."""
    from unittest.mock import AsyncMock, MagicMock
    dm = DatabaseManager()
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock(side_effect=Exception("Close error"))
    dm._pool = mock_pool
    dm._is_connected = True

    await dm.disconnect()
    assert dm.is_connected is False
    assert dm.get_pool() is None


@pytest.mark.asyncio
async def test_database_check_health_query_unexpected_value():
    """Verify check_health handles unexpected return value."""
    from unittest.mock import AsyncMock, MagicMock
    dm = DatabaseManager()
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 0  # Not 1

    class MockPoolAcquireContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockPoolAcquireContext()
    dm._pool = mock_pool

    healthy, status_msg, latency = await dm.check_health()
    assert healthy is False
    assert status_msg == "unexpected query response"


@pytest.mark.asyncio
async def test_database_check_health_query_exception():
    """Verify check_health handles query exception gracefully."""
    from unittest.mock import AsyncMock, MagicMock
    dm = DatabaseManager()
    mock_pool = MagicMock()
    mock_pool.acquire.side_effect = Exception("Connection lost")
    dm._pool = mock_pool

    healthy, status_msg, latency = await dm.check_health()
    assert healthy is False
    assert status_msg == "disconnected"
    assert "Connection lost" in (dm.last_error or "")
