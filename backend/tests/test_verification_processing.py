"""Phase 2C tests — verification processing lifecycle.

Covers all 16 required scenarios plus supplementary edge cases:
 1.  Process own pending verification → success
 2.  Processing changes status pending → processing (intermediate check)
 3.  Successful processing changes processing → completed
 4.  Processing exception changes processing → failed
 5.  Failed state stores safe error_message (no stack trace)
 6.  Nonexistent verification → 404
 7.  Another user's verification → 404 (no leakage)
 8.  Unauthenticated request → 401
 9.  Completed verification cannot be processed again → 409
10.  Failed verification cannot be processed again → 409
11.  Duplicate/concurrent processing does not corrupt state
12.  Status endpoint reflects persisted lifecycle state
13.  Database failure handled using existing error conventions → 500
14.  Success response uses existing StandardResponse envelope
15.  Error response uses existing error envelope
16.  No client-supplied user_id controls ownership
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from httpx import AsyncClient

from app.services.verification_processing_service import (
    InvalidStatusTransitionError,
    VerificationNotFoundError,
    VerificationProcessingService,
    _process_verification_core,
)
from app.repositories.verification_repository import VerificationRepository


# ==============================================================================
# Shared fixtures (mirrors test_verification_api.py for consistency)
# ==============================================================================

AUTH_PATCH = "app.api.dependencies.supabase_auth_service.get_user"
DB_USER_PATCH = "app.api.dependencies.user_repository.get_user_by_id"
PROCESS_PATCH = "app.api.v1.endpoints.verification.verification_processing_service.process_verification"
GET_OWN_PATCH = "app.api.v1.endpoints.verification.verification_service.get_own_verification"


@pytest.fixture
def owner_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
def other_user_id() -> uuid.UUID:
    return uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def verification_id() -> uuid.UUID:
    return uuid.UUID("cafecafe-cafe-cafe-cafe-cafecafecafe")


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)


def _make_record(
    *,
    vid: uuid.UUID,
    uid: uuid.UUID,
    status: str = "pending",
    now: datetime = None,
    error_message: str = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    return {
        "id": vid,
        "user_id": uid,
        "claim": "The Earth is the third planet from the Sun.",
        "status": status,
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": error_message,
        "created_at": now,
        "updated_at": now,
    }


def _owner_db(uid: uuid.UUID, now: datetime) -> dict:
    return {
        "id": uid,
        "email": "owner@verifai.app",
        "display_name": "Owner",
        "created_at": now,
        "updated_at": now,
    }


# ==============================================================================
# 1 & 14. Process own pending verification → 200 + StandardResponse envelope
# ==============================================================================


@pytest.mark.asyncio
async def test_process_own_pending_verification_success(
    client: AsyncClient, owner_id, verification_id, now
):
    """Process own pending verification returns 200 with StandardResponse."""
    completed = _make_record(vid=verification_id, uid=owner_id, status="completed", now=now)

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, new_callable=AsyncMock) as mock_proc:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_proc.return_value = completed

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    body = resp.json()

    # 14. Standard success envelope
    assert body["success"] is True
    assert "data" in body
    data = body["data"]
    assert data["id"] == str(verification_id)
    assert data["status"] == "completed"


# ==============================================================================
# 3. Successful processing → completed
# ==============================================================================


@pytest.mark.asyncio
async def test_process_returns_completed_status(
    client: AsyncClient, owner_id, verification_id, now
):
    """Successful processing must return completed status in response."""
    completed = _make_record(vid=verification_id, uid=owner_id, status="completed", now=now)

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, new_callable=AsyncMock) as mock_proc:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_proc.return_value = completed

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.json()["data"]["status"] == "completed"
    assert resp.json()["data"]["verdict"] is None      # no real verdict yet
    assert resp.json()["data"]["trust_score"] is None  # no real score yet
    assert resp.json()["data"]["evidence"] is None     # no evidence yet


# ==============================================================================
# 4 & 5. Processing exception → failed + safe error_message
# ==============================================================================


@pytest.mark.asyncio
async def test_process_exception_returns_failed_with_safe_message(
    client: AsyncClient, owner_id, verification_id, now
):
    """When processing raises, the endpoint returns the failed record (no stack trace)."""
    failed = _make_record(
        vid=verification_id,
        uid=owner_id,
        status="failed",
        now=now,
        error_message="Verification processing failed due to an internal error",
    )

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, new_callable=AsyncMock) as mock_proc:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_proc.return_value = failed

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    body = resp.json()
    assert resp.status_code == 200
    assert body["data"]["status"] == "failed"
    # Safe message — no traceback, no SQL, no internal path
    msg = body["data"]["error_message"]
    assert msg is not None
    assert "Traceback" not in msg
    assert "Exception" not in msg
    assert "SELECT" not in msg


# ==============================================================================
# 6. Nonexistent verification → 404
# ==============================================================================


@pytest.mark.asyncio
async def test_process_nonexistent_verification_returns_404(
    client: AsyncClient, owner_id, now
):
    """Processing a non-existent verification returns 404 VERIFICATION_NOT_FOUND."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=VerificationNotFoundError("not found")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            f"/api/v1/verification/{uuid.uuid4()}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 7. Another user's verification → 404 (no leakage)
# ==============================================================================


@pytest.mark.asyncio
async def test_process_another_users_verification_returns_404(
    client: AsyncClient, other_user_id, verification_id, now
):
    """Processing another user's verification returns 404, not 403."""
    other_db = {
        "id": other_user_id,
        "email": "other@v.app",
        "display_name": None,
        "created_at": now,
        "updated_at": now,
    }

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=VerificationNotFoundError("ownership")):
        mock_auth.return_value = {"id": str(other_user_id)}
        mock_db.return_value = other_db

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer other-tok"},
        )

    assert resp.status_code == 404
    assert resp.json()["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 8. Unauthenticated → 401
# ==============================================================================


@pytest.mark.asyncio
async def test_process_unauthenticated_returns_401(
    client: AsyncClient, verification_id
):
    """Processing without Authorization header returns 401."""
    resp = await client.post(f"/api/v1/verification/{verification_id}/process")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 9. Completed verification cannot be processed again → 409
# ==============================================================================


@pytest.mark.asyncio
async def test_process_completed_verification_returns_409(
    client: AsyncClient, owner_id, verification_id, now
):
    """Attempting to process an already-completed verification returns 409."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=InvalidStatusTransitionError("already completed")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 409
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["type"] == "INVALID_STATUS_TRANSITION"


# ==============================================================================
# 10. Failed verification cannot be processed again → 409
# ==============================================================================


@pytest.mark.asyncio
async def test_process_failed_verification_returns_409(
    client: AsyncClient, owner_id, verification_id, now
):
    """Attempting to re-process a failed verification returns 409."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=InvalidStatusTransitionError("already failed")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 409
    assert resp.json()["error"]["type"] == "INVALID_STATUS_TRANSITION"


# ==============================================================================
# 11. Duplicate processing does not corrupt state
# (tested at service level — concurrent atomic transitions)
# ==============================================================================


@pytest.mark.asyncio
async def test_duplicate_processing_raises_invalid_transition(
    owner_id, verification_id, now
):
    """A second concurrent process attempt raises InvalidStatusTransitionError.

    The first call wins the atomic transition_status CAS; the second call finds
    status != pending and therefore gets None back, which the service converts
    to InvalidStatusTransitionError.
    """
    mock_repo = AsyncMock(spec=VerificationRepository)

    # Fetch returns a record in "processing" state (first call already moved it)
    mock_repo.get_verification_by_id.return_value = _make_record(
        vid=verification_id, uid=owner_id, status="processing", now=now
    )
    # transition_status returns None (CAS missed)
    mock_repo.transition_status.return_value = None

    svc = VerificationProcessingService(repo=mock_repo)

    with pytest.raises(InvalidStatusTransitionError):
        await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )


# ==============================================================================
# 12. Status endpoint reflects persisted lifecycle state
# ==============================================================================


@pytest.mark.asyncio
async def test_status_endpoint_reflects_completed_state(
    client: AsyncClient, owner_id, verification_id, now
):
    """After processing, the status endpoint returns the updated lifecycle state."""
    completed = _make_record(vid=verification_id, uid=owner_id, status="completed", now=now)

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_get.return_value = completed

        resp = await client.get(
            f"/api/v1/verification/{verification_id}/status",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_status_endpoint_reflects_failed_state(
    client: AsyncClient, owner_id, verification_id, now
):
    """Status endpoint returns failed state when processing failed."""
    failed = _make_record(
        vid=verification_id,
        uid=owner_id,
        status="failed",
        now=now,
        error_message="Verification processing failed due to an internal error",
    )

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_get.return_value = failed

        resp = await client.get(
            f"/api/v1/verification/{verification_id}/status",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "failed"
    assert resp.json()["data"]["error_message"] is not None


# ==============================================================================
# 13. Database failure → 500 DATABASE_ERROR
# ==============================================================================


@pytest.mark.asyncio
async def test_process_database_failure_returns_500(
    client: AsyncClient, owner_id, verification_id, now
):
    """A database error during processing returns 500 DATABASE_ERROR."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=RuntimeError("Pool unavailable")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 500
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["type"] == "DATABASE_ERROR"


# ==============================================================================
# 15. Error response uses existing error envelope
# ==============================================================================


@pytest.mark.asyncio
async def test_error_response_uses_existing_envelope(
    client: AsyncClient, owner_id, verification_id, now
):
    """All error responses must follow {success: false, error: {type, message, details}}."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, side_effect=VerificationNotFoundError("not found")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    body = resp.json()
    assert "success" in body
    assert body["success"] is False
    assert "error" in body
    err = body["error"]
    assert "type" in err
    assert "message" in err
    assert "details" in err


# ==============================================================================
# 16. No client-supplied user_id controls ownership
# ==============================================================================


@pytest.mark.asyncio
async def test_ownership_from_auth_not_body(
    client: AsyncClient, owner_id, verification_id, now
):
    """The process endpoint must call process_verification with the auth-derived user_id."""
    completed = _make_record(vid=verification_id, uid=owner_id, status="completed", now=now)

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(PROCESS_PATCH, new_callable=AsyncMock) as mock_proc:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)
        mock_proc.return_value = completed

        # The endpoint takes no body — client cannot supply user_id at all
        resp = await client.post(
            f"/api/v1/verification/{verification_id}/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    call_kwargs = mock_proc.call_args
    called_user_id = call_kwargs.kwargs.get("user_id") or call_kwargs.args[1]
    assert called_user_id == owner_id


# ==============================================================================
# Service-level unit tests (VerificationProcessingService)
# ==============================================================================


@pytest.mark.asyncio
async def test_service_raises_not_found_when_record_missing(owner_id, verification_id):
    """Service raises VerificationNotFoundError when repository returns None."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    mock_repo.get_verification_by_id.return_value = None

    svc = VerificationProcessingService(repo=mock_repo)

    with pytest.raises(VerificationNotFoundError):
        await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )


@pytest.mark.asyncio
async def test_service_raises_not_found_for_wrong_owner(
    owner_id, other_user_id, verification_id, now
):
    """Service raises VerificationNotFoundError for cross-user access."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    mock_repo.get_verification_by_id.return_value = _make_record(
        vid=verification_id, uid=owner_id, now=now  # belongs to owner
    )

    svc = VerificationProcessingService(repo=mock_repo)

    with pytest.raises(VerificationNotFoundError):
        await svc.process_verification(
            verification_id=verification_id,
            user_id=other_user_id,  # different user
        )


@pytest.mark.asyncio
async def test_service_happy_path_transitions(owner_id, verification_id, now):
    """Full happy path: pending→processing→completed, all via transition_status."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = _make_record(vid=verification_id, uid=owner_id, status="pending", now=now)
    processing_record = _make_record(vid=verification_id, uid=owner_id, status="processing", now=now)
    completed_record = _make_record(vid=verification_id, uid=owner_id, status="completed", now=now)

    mock_repo.get_verification_by_id.return_value = pending_record
    # First transition_status call: pending→processing
    # Second transition_status call: processing→completed
    mock_repo.transition_status.side_effect = [processing_record, completed_record]

    svc = VerificationProcessingService(repo=mock_repo)
    result = await svc.process_verification(
        verification_id=verification_id,
        user_id=owner_id,
    )

    assert result["status"] == "completed"
    assert mock_repo.transition_status.await_count == 2

    # First call: pending→processing
    first_call = mock_repo.transition_status.call_args_list[0]
    assert first_call.kwargs["expected_status"] == "pending"
    assert first_call.kwargs["new_status"] == "processing"

    # Second call: processing→completed
    second_call = mock_repo.transition_status.call_args_list[1]
    assert second_call.kwargs["expected_status"] == "processing"
    assert second_call.kwargs["new_status"] == "completed"


@pytest.mark.asyncio
async def test_service_transitions_to_failed_on_stub_exception(
    owner_id, verification_id, now
):
    """When _process_verification_core raises, service transitions processing→failed."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = _make_record(vid=verification_id, uid=owner_id, status="pending", now=now)
    processing_record = _make_record(vid=verification_id, uid=owner_id, status="processing", now=now)
    failed_record = _make_record(
        vid=verification_id,
        uid=owner_id,
        status="failed",
        now=now,
        error_message="Verification processing failed due to an internal error",
    )

    mock_repo.get_verification_by_id.return_value = pending_record
    # First transition: pending→processing succeeds
    # Second transition: processing→failed succeeds
    mock_repo.transition_status.side_effect = [processing_record, failed_record]

    svc = VerificationProcessingService(repo=mock_repo)

    with patch(
        "app.services.verification_processing_service._process_verification_core",
        side_effect=RuntimeError("Simulated processing failure"),
    ):
        result = await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )

    assert result["status"] == "failed"
    assert result["error_message"] is not None
    assert "Traceback" not in result["error_message"]

    # Confirm processing→failed transition was called
    second_call = mock_repo.transition_status.call_args_list[1]
    assert second_call.kwargs["expected_status"] == "processing"
    assert second_call.kwargs["new_status"] == "failed"


@pytest.mark.asyncio
async def test_service_raises_invalid_transition_when_not_pending(
    owner_id, verification_id, now
):
    """Service raises InvalidStatusTransitionError when transition_status returns None (wrong state)."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    completed_record = _make_record(
        vid=verification_id, uid=owner_id, status="completed", now=now
    )
    mock_repo.get_verification_by_id.return_value = completed_record
    mock_repo.transition_status.return_value = None  # CAS miss — status != pending

    svc = VerificationProcessingService(repo=mock_repo)

    with pytest.raises(InvalidStatusTransitionError):
        await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )


@pytest.mark.asyncio
async def test_service_fallback_when_completed_transition_returns_none(
    owner_id, verification_id, now
):
    """Service returns a fallback dict when processing→completed transition returns None."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = _make_record(vid=verification_id, uid=owner_id, status="pending", now=now)
    processing_record = _make_record(vid=verification_id, uid=owner_id, status="processing", now=now)

    mock_repo.get_verification_by_id.return_value = pending_record
    # First transition: pending→processing succeeds
    # Second transition: processing→completed returns None (race edge case)
    mock_repo.transition_status.side_effect = [processing_record, None]

    svc = VerificationProcessingService(repo=mock_repo)
    result = await svc.process_verification(
        verification_id=verification_id,
        user_id=owner_id,
    )

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_service_fallback_when_failed_transition_returns_none(
    owner_id, verification_id, now
):
    """Service returns a fallback dict when processing→failed transition returns None."""
    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = _make_record(vid=verification_id, uid=owner_id, status="pending", now=now)
    processing_record = _make_record(vid=verification_id, uid=owner_id, status="processing", now=now)

    mock_repo.get_verification_by_id.return_value = pending_record
    # pending→processing succeeds; processing→failed returns None
    mock_repo.transition_status.side_effect = [processing_record, None]

    svc = VerificationProcessingService(repo=mock_repo)

    with patch(
        "app.services.verification_processing_service._process_verification_core",
        side_effect=RuntimeError("Boom"),
    ):
        result = await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )

    assert result["status"] == "failed"
    assert result["error_message"] is not None


# ==============================================================================
# Repository-level unit tests (transition_status)
# ==============================================================================


@pytest.mark.asyncio
async def test_repo_transition_status_success(verification_id, now):
    """transition_status returns updated dict when CAS succeeds."""
    from app.repositories.verification_repository import VerificationRepository

    db_manager = MagicMock()
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, *a):
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    db_manager.get_pool.return_value = mock_pool

    uid = uuid.uuid4()
    record = {
        "id": verification_id,
        "user_id": uid,
        "claim": "A claim.",
        "status": "processing",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    mock_conn.fetchrow.return_value = record

    repo = VerificationRepository(db_manager=db_manager)
    result = await repo.transition_status(
        verification_id=verification_id,
        expected_status="pending",
        new_status="processing",
    )

    assert result is not None
    assert result["status"] == "processing"
    mock_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_repo_transition_status_returns_none_on_cas_miss(verification_id):
    """transition_status returns None when the CAS predicate does not match."""
    from app.repositories.verification_repository import VerificationRepository

    db_manager = MagicMock()
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, *a):
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    db_manager.get_pool.return_value = mock_pool
    mock_conn.fetchrow.return_value = None  # CAS miss

    repo = VerificationRepository(db_manager=db_manager)
    result = await repo.transition_status(
        verification_id=verification_id,
        expected_status="pending",
        new_status="processing",
    )

    assert result is None


@pytest.mark.asyncio
async def test_repo_transition_status_raises_when_pool_none():
    """transition_status raises RuntimeError when pool is unavailable."""
    from app.repositories.verification_repository import VerificationRepository

    disconnected_db = MagicMock()
    disconnected_db.get_pool.return_value = None
    repo = VerificationRepository(db_manager=disconnected_db)

    with pytest.raises(RuntimeError, match="Database connection is not available"):
        await repo.transition_status(
            verification_id=uuid.uuid4(),
            expected_status="pending",
            new_status="processing",
        )


# ==============================================================================
# Processing stub unit test
# ==============================================================================


@pytest.mark.asyncio
async def test_processing_stub_returns_expected_shape(verification_id):
    """_process_verification_core returns phase/message dict, no real verdict."""
    result = await _process_verification_core(verification_id)
    assert result["phase"] == "processing_stub"
    assert "message" in result
    assert "verdict" not in result
    assert "trust_score" not in result
    assert "evidence" not in result


# ==============================================================================
# Additional — invalid UUID in path
# ==============================================================================


@pytest.mark.asyncio
async def test_process_invalid_uuid_in_path(client: AsyncClient, owner_id, now):
    """Non-UUID path parameter for process endpoint returns 422."""
    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = _owner_db(owner_id, now)

        resp = await client.post(
            "/api/v1/verification/not-a-uuid/process",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 422
