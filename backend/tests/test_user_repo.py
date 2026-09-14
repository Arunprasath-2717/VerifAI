"""Tests for UserRepository database operations."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.repositories.user_repository import UserRepository


@pytest.fixture
def mock_db_manager():
    """Mock database manager with simulated asyncpg connection and pool."""
    db_manager = MagicMock()
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    db_manager.get_pool.return_value = mock_pool
    return db_manager, mock_conn


@pytest.mark.asyncio
async def test_create_user_success(mock_db_manager):
    """Verify create_user executes INSERT and returns user dictionary."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_conn.fetchrow.return_value = {
        "id": test_id,
        "email": "test@example.com",
        "display_name": "Test User",
        "created_at": now,
        "updated_at": now,
    }

    user = await repo.create_user(test_id, "test@example.com", "Test User")
    assert user["id"] == test_id
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test User"
    mock_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_id_found(mock_db_manager):
    """Verify get_user_by_id returns user dict when record exists."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_conn.fetchrow.return_value = {
        "id": test_id,
        "email": "test@example.com",
        "display_name": "Test User",
        "created_at": now,
        "updated_at": now,
    }

    user = await repo.get_user_by_id(test_id)
    assert user is not None
    assert user["id"] == test_id


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mock_db_manager):
    """Verify get_user_by_id returns None when user does not exist."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    mock_conn.fetchrow.return_value = None

    user = await repo.get_user_by_id(uuid.uuid4())
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_found(mock_db_manager):
    """Verify get_user_by_email returns user dict when email matches."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_conn.fetchrow.return_value = {
        "id": test_id,
        "email": "test@example.com",
        "display_name": "Test User",
        "created_at": now,
        "updated_at": now,
    }

    user = await repo.get_user_by_email("test@example.com")
    assert user is not None
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_update_user_success(mock_db_manager):
    """Verify update_user updates display_name and returns updated record."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_conn.fetchrow.return_value = {
        "id": test_id,
        "email": "test@example.com",
        "display_name": "New Name",
        "created_at": now,
        "updated_at": now,
    }

    updated = await repo.update_user(test_id, "New Name")
    assert updated is not None
    assert updated["display_name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_user_success(mock_db_manager):
    """Verify delete_user returns True when record deleted."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    mock_conn.execute.return_value = "DELETE 1"

    deleted = await repo.delete_user(uuid.uuid4())
    assert deleted is True


@pytest.mark.asyncio
async def test_delete_user_not_found(mock_db_manager):
    """Verify delete_user returns False when no rows affected."""
    db_mgr, mock_conn = mock_db_manager
    repo = UserRepository(db_manager=db_mgr)
    mock_conn.execute.return_value = "DELETE 0"

    deleted = await repo.delete_user(uuid.uuid4())
    assert deleted is False


@pytest.mark.asyncio
async def test_user_repo_disconnected_pool():
    """Verify repository methods raise RuntimeError if pool is None."""
    disconnected_db = MagicMock()
    disconnected_db.get_pool.return_value = None
    repo = UserRepository(db_manager=disconnected_db)

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.create_user(uuid.uuid4(), "test@example.com")

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.get_user_by_id(uuid.uuid4())

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.get_user_by_email("test@example.com")

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.update_user(uuid.uuid4(), "New Name")

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.delete_user(uuid.uuid4())
