"""API-level tests for Phase 2B Verification endpoints.

Covers all 16 required test scenarios:
 1.  POST verification — valid authenticated user
 2.  POST validation failure (claim too short)
 3.  POST unauthenticated
 4.  GET own verification
 5.  GET nonexistent verification
 6.  GET another user's verification (must return 404, not leak existence)
 7.  GET unauthenticated
 8.  STATUS own verification
 9.  STATUS nonexistent verification
10.  STATUS another user's verification
11.  STATUS unauthenticated
12.  Database failure (POST and GET)
13.  Correct HTTP status codes
14.  Standard success response envelope
15.  Standard error response envelope
16.  Ownership derived from authentication, never from request body
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient

from app.schemas.auth import UserResponse


# ==============================================================================
# Shared fixtures
# ==============================================================================


@pytest.fixture
def owner_id() -> uuid.UUID:
    """UUID of the authenticated user (the verification owner)."""
    return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
def other_user_id() -> uuid.UUID:
    """UUID of a *different* user who does NOT own the verification."""
    return uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def verification_id() -> uuid.UUID:
    """Fixed UUID for a verification record."""
    return uuid.UUID("cafecafe-cafe-cafe-cafe-cafecafecafe")


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_record(owner_id, verification_id, now):
    """Raw dict as returned by the repository — mimics an asyncpg row."""
    return {
        "id": verification_id,
        "user_id": owner_id,
        "claim": "The Earth is the third planet from the Sun.",
        "status": "pending",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def owner_user_response(owner_id, now) -> UserResponse:
    return UserResponse(
        id=owner_id,
        email="owner@verifai.app",
        display_name="Owner",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Helper — patch get_current_user dependency + service method
# ---------------------------------------------------------------------------


AUTH_PATCH = "app.api.dependencies.supabase_auth_service.get_user"
DB_USER_PATCH = "app.api.dependencies.user_repository.get_user_by_id"
SUBMIT_PATCH = "app.api.v1.endpoints.verification.verification_service.submit_verification"
GET_OWN_PATCH = "app.api.v1.endpoints.verification.verification_service.get_own_verification"


def _auth_patches(user_id: uuid.UUID, user_record: dict):
    """Return context-manager stack that mocks the auth dependency chain."""
    import contextlib

    @contextlib.asynccontextmanager
    async def _cm():
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
             patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db:
            mock_auth.return_value = {"id": str(user_id)}
            mock_db.return_value = user_record
            yield mock_auth, mock_db

    return _cm()


# ==============================================================================
# 1. POST /verification — success (201 Created)
# ==============================================================================


@pytest.mark.asyncio
async def test_post_verification_success(
    client: AsyncClient,
    owner_id,
    owner_user_response,
    sample_record,
    now,
):
    """Valid authenticated request creates verification and returns 201."""
    owner_db_record = {
        "id": owner_id,
        "email": "owner@verifai.app",
        "display_name": "Owner",
        "created_at": now,
        "updated_at": now,
    }

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db_user, \
         patch(SUBMIT_PATCH, new_callable=AsyncMock) as mock_submit:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db_user.return_value = owner_db_record
        mock_submit.return_value = sample_record

        response = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer valid-token"},
            json={"claim": "The Earth is the third planet from the Sun."},
        )

    assert response.status_code == 201
    body = response.json()

    # 14. Standard success response envelope
    assert body["success"] is True
    assert "data" in body

    data = body["data"]
    assert data["id"] == str(sample_record["id"])
    assert data["user_id"] == str(owner_id)
    assert data["claim"] == "The Earth is the third planet from the Sun."
    assert data["status"] == "pending"
    assert data["verdict"] is None


# ==============================================================================
# 13. Correct HTTP status codes
# ==============================================================================


@pytest.mark.asyncio
async def test_post_verification_returns_201(
    client: AsyncClient,
    owner_id,
    sample_record,
    now,
):
    """Verify 201 Created on successful POST."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(SUBMIT_PATCH, new_callable=AsyncMock) as mock_sub:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_sub.return_value = sample_record

        resp = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={"claim": "The Earth is the third planet from the Sun."},
        )
    assert resp.status_code == 201


# ==============================================================================
# 2. POST validation failure (claim too short)
# ==============================================================================


@pytest.mark.asyncio
async def test_post_verification_claim_too_short(
    client: AsyncClient,
    owner_id,
    now,
):
    """Claim shorter than 10 chars must return 422 VALIDATION_ERROR."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={"claim": "Too short"},  # 9 chars
        )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    # 15. Standard error response envelope
    assert body["error"]["type"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_post_verification_claim_missing(
    client: AsyncClient,
    owner_id,
    now,
):
    """Missing claim field must return 422."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={},
        )

    assert response.status_code == 422


# ==============================================================================
# 3. POST unauthenticated
# ==============================================================================


@pytest.mark.asyncio
async def test_post_verification_unauthenticated(client: AsyncClient):
    """POST without Authorization header must return 401."""
    response = await client.post(
        "/api/v1/verification",
        json={"claim": "The Earth is the third planet from the Sun."},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 4. GET /verification/{id} — own verification (200 OK)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_own_verification(
    client: AsyncClient,
    owner_id,
    verification_id,
    sample_record,
    now,
):
    """Owner can retrieve their own verification record."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_get.return_value = sample_record

        response = await client.get(
            f"/api/v1/verification/{verification_id}",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == str(verification_id)
    assert body["data"]["user_id"] == str(owner_id)


# ==============================================================================
# 5. GET nonexistent verification (404)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_nonexistent_verification(
    client: AsyncClient,
    owner_id,
    now,
):
    """Requesting a verification that doesn't exist returns 404."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_get.return_value = None

        response = await client.get(
            f"/api/v1/verification/{uuid.uuid4()}",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 6. GET another user's verification — must return 404 (no leakage)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_another_users_verification_returns_404(
    client: AsyncClient,
    owner_id,
    other_user_id,
    verification_id,
    sample_record,
    now,
):
    """Requesting another user's verification must return 404, not 403.

    The service returns None for ownership violations to prevent resource
    existence leakage (IDOR). The endpoint must not distinguish 'not found'
    from 'belongs to another user'.
    """
    # other_user_id is authenticated
    other_db = {
        "id": other_user_id,
        "email": "other@verifai.app",
        "display_name": None,
        "created_at": now,
        "updated_at": now,
    }

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(other_user_id)}
        mock_db.return_value = other_db
        # Service returns None for ownership violation
        mock_get.return_value = None

        response = await client.get(
            f"/api/v1/verification/{verification_id}",
            headers={"Authorization": "Bearer other-token"},
        )

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 7. GET unauthenticated
# ==============================================================================


@pytest.mark.asyncio
async def test_get_verification_unauthenticated(
    client: AsyncClient,
    verification_id,
):
    """GET without Authorization header must return 401."""
    response = await client.get(f"/api/v1/verification/{verification_id}")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 8. GET /status — own verification
# ==============================================================================


@pytest.mark.asyncio
async def test_get_status_own_verification(
    client: AsyncClient,
    owner_id,
    verification_id,
    sample_record,
    now,
):
    """Owner can retrieve their own verification status."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_get.return_value = sample_record

        response = await client.get(
            f"/api/v1/verification/{verification_id}/status",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "pending"
    assert body["data"]["id"] == str(verification_id)


# ==============================================================================
# 9. STATUS nonexistent verification (404)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_status_nonexistent(
    client: AsyncClient,
    owner_id,
    now,
):
    """Status endpoint returns 404 for a nonexistent verification."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_get.return_value = None

        response = await client.get(
            f"/api/v1/verification/{uuid.uuid4()}/status",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 10. STATUS another user's verification — 404, no leakage
# ==============================================================================


@pytest.mark.asyncio
async def test_get_status_another_users_verification_returns_404(
    client: AsyncClient,
    other_user_id,
    verification_id,
    now,
):
    """Status endpoint returns 404 for another user's verification."""
    other_db = {
        "id": other_user_id,
        "email": "other@verifai.app",
        "display_name": None,
        "created_at": now,
        "updated_at": now,
    }

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(other_user_id)}
        mock_db.return_value = other_db
        mock_get.return_value = None  # service returns None for IDOR

        response = await client.get(
            f"/api/v1/verification/{verification_id}/status",
            headers={"Authorization": "Bearer other-tok"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "VERIFICATION_NOT_FOUND"


# ==============================================================================
# 11. STATUS unauthenticated
# ==============================================================================


@pytest.mark.asyncio
async def test_get_status_unauthenticated(client: AsyncClient, verification_id):
    """Status endpoint returns 401 when no Authorization header is provided."""
    response = await client.get(f"/api/v1/verification/{verification_id}/status")
    assert response.status_code == 401
    assert response.json()["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 12. Database failure — POST
# ==============================================================================


@pytest.mark.asyncio
async def test_post_verification_database_failure(
    client: AsyncClient,
    owner_id,
    now,
):
    """Database exception during POST returns 500 DATABASE_ERROR."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(SUBMIT_PATCH, side_effect=RuntimeError("Pool unavailable")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={"claim": "The Earth is the third planet from the Sun."},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "DATABASE_ERROR"


# ==============================================================================
# 12b. Database failure — GET
# ==============================================================================


@pytest.mark.asyncio
async def test_get_verification_database_failure(
    client: AsyncClient,
    owner_id,
    verification_id,
    now,
):
    """Database exception during GET returns 500 DATABASE_ERROR."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, side_effect=RuntimeError("DB pool gone")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.get(
            f"/api/v1/verification/{verification_id}",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "DATABASE_ERROR"


# ==============================================================================
# 12c. Database failure — STATUS
# ==============================================================================


@pytest.mark.asyncio
async def test_get_status_database_failure(
    client: AsyncClient,
    owner_id,
    verification_id,
    now,
):
    """Database exception during STATUS returns 500 DATABASE_ERROR."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, side_effect=RuntimeError("DB pool gone")):
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.get(
            f"/api/v1/verification/{verification_id}/status",
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "DATABASE_ERROR"


# ==============================================================================
# 16. Ownership derived from authentication, never from request body
# ==============================================================================


@pytest.mark.asyncio
async def test_owner_id_comes_from_auth_not_request_body(
    client: AsyncClient,
    owner_id,
    other_user_id,
    verification_id,
    sample_record,
    now,
):
    """The user_id in the created verification must come from the auth token,
    not from anything the client sends in the request body.

    We verify that submit_verification is called with the authenticated
    user's id, regardless of what the client payload contains.
    """
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(SUBMIT_PATCH, new_callable=AsyncMock) as mock_sub:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_sub.return_value = sample_record

        # Client sends only a claim — no user_id in body at all
        await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={"claim": "The Earth is the third planet from the Sun."},
        )

        # submit_verification must have been called with the auth-derived UUID
        call_kwargs = mock_sub.call_args
        assert call_kwargs is not None
        called_user_id = call_kwargs.kwargs.get("user_id") or call_kwargs.args[0]
        assert called_user_id == owner_id


# ==============================================================================
# Additional edge cases
# ==============================================================================


@pytest.mark.asyncio
async def test_invalid_uuid_in_path(client: AsyncClient, owner_id, now):
    """A non-UUID path parameter should be rejected with 422."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db

        response = await client.get(
            "/api/v1/verification/not-a-valid-uuid",
            headers={"Authorization": "Bearer tok"},
        )

    # FastAPI validates UUID path params and returns 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_verification_200_status_code(
    client: AsyncClient,
    owner_id,
    verification_id,
    sample_record,
    now,
):
    """Successful GET returns exactly 200 OK."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(GET_OWN_PATCH, new_callable=AsyncMock) as mock_get:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_get.return_value = sample_record

        response = await client.get(
            f"/api/v1/verification/{verification_id}",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_response_contains_all_required_fields(
    client: AsyncClient,
    owner_id,
    verification_id,
    sample_record,
    now,
):
    """POST response data must contain all required VerificationResponse fields."""
    owner_db = {"id": owner_id, "email": "o@v.app", "display_name": None, "created_at": now, "updated_at": now}

    with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth, \
         patch(DB_USER_PATCH, new_callable=AsyncMock) as mock_db, \
         patch(SUBMIT_PATCH, new_callable=AsyncMock) as mock_sub:
        mock_auth.return_value = {"id": str(owner_id)}
        mock_db.return_value = owner_db
        mock_sub.return_value = sample_record

        response = await client.post(
            "/api/v1/verification",
            headers={"Authorization": "Bearer tok"},
            json={"claim": "The Earth is the third planet from the Sun."},
        )

    data = response.json()["data"]
    required = {"id", "user_id", "claim", "status", "created_at", "updated_at"}
    for field in required:
        assert field in data, f"Missing required field: {field}"


# ==============================================================================
# Verification Service unit tests
# ==============================================================================


@pytest.mark.asyncio
async def test_service_submit_calls_repo(owner_id):
    """VerificationService.submit_verification delegates to the repository."""
    from app.services.verification_service import VerificationService

    mock_repo = AsyncMock()
    record = {
        "id": uuid.uuid4(),
        "user_id": owner_id,
        "claim": "A claim.",
        "status": "pending",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    mock_repo.create_verification.return_value = record

    svc = VerificationService(repo=mock_repo)
    result = await svc.submit_verification(user_id=owner_id, claim="A claim.")

    mock_repo.create_verification.assert_awaited_once_with(
        user_id=owner_id, claim="A claim."
    )
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_service_get_own_returns_none_for_wrong_owner(owner_id, other_user_id, verification_id, now):
    """Service returns None when user_id != record user_id (IDOR prevention)."""
    from app.services.verification_service import VerificationService

    mock_repo = AsyncMock()
    mock_repo.get_verification_by_id.return_value = {
        "id": verification_id,
        "user_id": owner_id,  # record belongs to owner
        "claim": "A claim.",
        "status": "pending",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    svc = VerificationService(repo=mock_repo)
    # other_user_id tries to access owner's record
    result = await svc.get_own_verification(
        verification_id=verification_id,
        user_id=other_user_id,  # different user
    )
    assert result is None


@pytest.mark.asyncio
async def test_service_get_own_returns_record_for_correct_owner(owner_id, verification_id, now):
    """Service returns the record when user_id matches the record owner."""
    from app.services.verification_service import VerificationService

    mock_repo = AsyncMock()
    record = {
        "id": verification_id,
        "user_id": owner_id,
        "claim": "A claim.",
        "status": "pending",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    mock_repo.get_verification_by_id.return_value = record

    svc = VerificationService(repo=mock_repo)
    result = await svc.get_own_verification(
        verification_id=verification_id,
        user_id=owner_id,
    )
    assert result is not None
    assert result["id"] == verification_id


@pytest.mark.asyncio
async def test_service_get_own_returns_none_when_not_found(owner_id, verification_id):
    """Service returns None when the repository returns None (record not found)."""
    from app.services.verification_service import VerificationService

    mock_repo = AsyncMock()
    mock_repo.get_verification_by_id.return_value = None

    svc = VerificationService(repo=mock_repo)
    result = await svc.get_own_verification(
        verification_id=verification_id,
        user_id=owner_id,
    )
    assert result is None
