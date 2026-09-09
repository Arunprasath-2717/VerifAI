"""Tests for VerificationRepository database operations (Phase 2A)."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.repositories.verification_repository import VerificationRepository


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db_manager():
    """Mock database manager with a simulated asyncpg connection pool."""
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


def _make_record(
    *,
    vid: uuid.UUID = None,
    uid: uuid.UUID = None,
    claim: str = "The Earth is flat.",
    status: str = "pending",
    verdict: str = None,
    trust_score=None,
    evidence=None,
    error_message: str = None,
    now: datetime = None,
):
    """Build a fake asyncpg-style record dict that the repository will accept."""
    now = now or datetime.now(timezone.utc)
    return {
        "id": vid or uuid.uuid4(),
        "user_id": uid or uuid.uuid4(),
        "claim": claim,
        "status": status,
        "verdict": verdict,
        "trust_score": trust_score,
        "evidence": evidence,
        "error_message": error_message,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# create_verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_verification_success(mock_db_manager):
    """create_verification inserts a row and returns it as a dict."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    uid = uuid.uuid4()
    vid = uuid.uuid4()
    record = _make_record(vid=vid, uid=uid, status="pending")
    mock_conn.fetchrow.return_value = record

    result = await repo.create_verification(uid, "The Earth is flat.")

    assert result["id"] == vid
    assert result["user_id"] == uid
    assert result["status"] == "pending"
    assert result["verdict"] is None
    mock_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_verification_accepts_string_uuid(mock_db_manager):
    """create_verification accepts a string UUID and converts it internally."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    uid = uuid.uuid4()
    record = _make_record(uid=uid)
    mock_conn.fetchrow.return_value = record

    result = await repo.create_verification(str(uid), "Some claim.")
    assert result is not None


@pytest.mark.asyncio
async def test_create_verification_db_returns_none_raises(mock_db_manager):
    """create_verification raises RuntimeError when fetchrow returns None."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetchrow.return_value = None

    with pytest.raises(RuntimeError, match="Failed to insert verification record"):
        await repo.create_verification(uuid.uuid4(), "Some claim.")


# ---------------------------------------------------------------------------
# update_verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_verification_success(mock_db_manager):
    """update_verification returns updated row with new status and verdict."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    vid = uuid.uuid4()
    uid = uuid.uuid4()
    record = _make_record(
        vid=vid,
        uid=uid,
        status="completed",
        verdict="refuted",
        trust_score=Decimal("0.250"),
    )
    mock_conn.fetchrow.return_value = record

    result = await repo.update_verification(
        vid,
        status="completed",
        verdict="refuted",
        trust_score=Decimal("0.250"),
    )

    assert result is not None
    assert result["status"] == "completed"
    assert result["verdict"] == "refuted"


@pytest.mark.asyncio
async def test_update_verification_not_found(mock_db_manager):
    """update_verification returns None when no matching row exists."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetchrow.return_value = None

    result = await repo.update_verification(uuid.uuid4(), status="failed")
    assert result is None


@pytest.mark.asyncio
async def test_update_verification_with_evidence(mock_db_manager):
    """update_verification serialises evidence list to JSON before storing."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    evidence = [{"url": "https://example.com", "title": "Source A"}]
    record = _make_record(
        status="completed",
        verdict="supported",
        evidence=json.dumps(evidence),  # db would return it as a JSON string
    )
    mock_conn.fetchrow.return_value = record

    result = await repo.update_verification(
        uuid.uuid4(),
        status="completed",
        verdict="supported",
        evidence=evidence,
    )

    # _row_to_dict should have parsed the JSON string back into a list
    assert isinstance(result["evidence"], list)
    assert result["evidence"][0]["url"] == "https://example.com"


# ---------------------------------------------------------------------------
# get_verification_by_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_verification_by_id_found(mock_db_manager):
    """get_verification_by_id returns the row when it exists."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    vid = uuid.uuid4()
    record = _make_record(vid=vid)
    mock_conn.fetchrow.return_value = record

    result = await repo.get_verification_by_id(vid)
    assert result is not None
    assert result["id"] == vid


@pytest.mark.asyncio
async def test_get_verification_by_id_not_found(mock_db_manager):
    """get_verification_by_id returns None when the row does not exist."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetchrow.return_value = None

    result = await repo.get_verification_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_verification_by_id_string_uuid(mock_db_manager):
    """get_verification_by_id accepts a string UUID."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    vid = uuid.uuid4()
    mock_conn.fetchrow.return_value = _make_record(vid=vid)

    result = await repo.get_verification_by_id(str(vid))
    assert result["id"] == vid


# ---------------------------------------------------------------------------
# get_verifications_by_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_verifications_by_user_returns_list(mock_db_manager):
    """get_verifications_by_user returns a list of dicts for the user."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    uid = uuid.uuid4()
    records = [_make_record(uid=uid) for _ in range(3)]
    mock_conn.fetch.return_value = records

    results = await repo.get_verifications_by_user(uid)
    assert len(results) == 3
    for r in results:
        assert r["user_id"] == uid


@pytest.mark.asyncio
async def test_get_verifications_by_user_empty(mock_db_manager):
    """get_verifications_by_user returns an empty list when no verifications exist."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetch.return_value = []

    results = await repo.get_verifications_by_user(uuid.uuid4())
    assert results == []


@pytest.mark.asyncio
async def test_get_verifications_by_user_passes_pagination(mock_db_manager):
    """get_verifications_by_user passes limit and offset parameters to the query."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    uid = uuid.uuid4()
    mock_conn.fetch.return_value = []

    await repo.get_verifications_by_user(uid, limit=5, offset=10)

    # Verify the DB call was made with limit and offset
    call_args = mock_conn.fetch.call_args
    assert call_args is not None
    args = call_args[0]
    # args: (query, uid, limit, offset)
    assert args[2] == 5
    assert args[3] == 10


# ---------------------------------------------------------------------------
# count_verifications_by_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_verifications_by_user(mock_db_manager):
    """count_verifications_by_user returns the integer count."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetchval.return_value = 7

    count = await repo.count_verifications_by_user(uuid.uuid4())
    assert count == 7


@pytest.mark.asyncio
async def test_count_verifications_returns_zero_when_none(mock_db_manager):
    """count_verifications_by_user returns 0 when fetchval returns None."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.fetchval.return_value = None

    count = await repo.count_verifications_by_user(uuid.uuid4())
    assert count == 0


# ---------------------------------------------------------------------------
# delete_verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_verification_success(mock_db_manager):
    """delete_verification returns True when a row is deleted."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.execute.return_value = "DELETE 1"

    deleted = await repo.delete_verification(uuid.uuid4(), uuid.uuid4())
    assert deleted is True


@pytest.mark.asyncio
async def test_delete_verification_not_found(mock_db_manager):
    """delete_verification returns False when the row does not exist or is not owned."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    mock_conn.execute.return_value = "DELETE 0"

    deleted = await repo.delete_verification(uuid.uuid4(), uuid.uuid4())
    assert deleted is False


# ---------------------------------------------------------------------------
# Pool unavailable — RuntimeError on every write/read method
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_methods_raise_when_pool_is_none():
    """Every public method raises RuntimeError when the database pool is unavailable."""
    disconnected_db = MagicMock()
    disconnected_db.get_pool.return_value = None
    repo = VerificationRepository(db_manager=disconnected_db)

    vid = uuid.uuid4()
    uid = uuid.uuid4()

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.create_verification(uid, "A claim.")

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.update_verification(vid, status="completed")

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.get_verification_by_id(vid)

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.get_verifications_by_user(uid)

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.count_verifications_by_user(uid)

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.delete_verification(vid, uid)


# ---------------------------------------------------------------------------
# Evidence JSON round-trip (_row_to_dict)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_json_string_is_parsed(mock_db_manager):
    """_row_to_dict converts a JSON string evidence field to a Python object."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    evidence_list = [{"url": "https://a.com"}, {"url": "https://b.com"}]
    record = _make_record(evidence=json.dumps(evidence_list))
    mock_conn.fetchrow.return_value = record

    result = await repo.get_verification_by_id(uuid.uuid4())
    assert isinstance(result["evidence"], list)
    assert len(result["evidence"]) == 2


@pytest.mark.asyncio
async def test_evidence_none_stays_none(mock_db_manager):
    """_row_to_dict leaves evidence as None when the DB field is NULL."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    record = _make_record(evidence=None)
    mock_conn.fetchrow.return_value = record

    result = await repo.get_verification_by_id(uuid.uuid4())
    assert result["evidence"] is None


@pytest.mark.asyncio
async def test_evidence_invalid_json_becomes_none(mock_db_manager):
    """_row_to_dict sets evidence to None if the JSON string is malformed."""
    db_mgr, mock_conn = mock_db_manager
    repo = VerificationRepository(db_manager=db_mgr)

    record = _make_record(evidence="not-valid-json{{{")
    mock_conn.fetchrow.return_value = record

    result = await repo.get_verification_by_id(uuid.uuid4())
    assert result["evidence"] is None
