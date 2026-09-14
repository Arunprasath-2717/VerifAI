"""Comprehensive tests for Authentication endpoints and Supabase integration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from httpx import AsyncClient

from app.schemas.auth import UserResponse
from app.services.supabase_auth import (
    AuthProviderError,
    DuplicateAccountError,
    ExpiredTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidTokenError,
    SupabaseAuthService,
)


@pytest.fixture
def mock_user_id():
    """Consistent test user UUID."""
    return uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def sample_user_record(mock_user_id):
    """Sample user record dict matching database return format."""
    now = datetime.now(timezone.utc)
    return {
        "id": mock_user_id,
        "email": "student@verifai.app",
        "display_name": "Arun Prasath",
        "created_at": now,
        "updated_at": now,
    }


# ==============================================================================
# 1. Registration Success
# ==============================================================================
@pytest.mark.asyncio
async def test_registration_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify registration creates identity, synchronizes DB, and returns tokens."""
    payload = {
        "email": "student@verifai.app",
        "password": "SecurePassword123!",
        "display_name": "Arun Prasath",
    }

    mock_auth_response = {
        "user": {"id": str(mock_user_id), "email": "student@verifai.app"},
        "session": {
            "access_token": "mock-access-token-123",
            "refresh_token": "mock-refresh-token-456",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_up", new_callable=AsyncMock) as mock_sign_up, \
         patch("app.api.v1.endpoints.auth.user_repository.create_user", new_callable=AsyncMock) as mock_create_user:
        mock_sign_up.return_value = mock_auth_response
        mock_create_user.return_value = sample_user_record

        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == "student@verifai.app"
        assert data["data"]["user"]["id"] == str(mock_user_id)
        assert data["data"]["session"]["access_token"] == "mock-access-token-123"
        mock_sign_up.assert_awaited_once()
        mock_create_user.assert_awaited_once()


# ==============================================================================
# 2. Duplicate Registration
# ==============================================================================
@pytest.mark.asyncio
async def test_registration_duplicate_email(client: AsyncClient):
    """Verify registering an existing email returns 409 DUPLICATE_ACCOUNT."""
    payload = {
        "email": "existing@verifai.app",
        "password": "SecurePassword123!",
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_up", new_callable=AsyncMock) as mock_sign_up:
        mock_sign_up.side_effect = DuplicateAccountError("An account with this email already exists")

        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "DUPLICATE_ACCOUNT"
        assert "already exists" in data["error"]["message"]


# ==============================================================================
# 3. Invalid Registration Input (422)
# ==============================================================================
@pytest.mark.asyncio
async def test_registration_invalid_input(client: AsyncClient):
    """Verify validation errors for short password and invalid email return 422."""
    # Test short password
    res1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "valid@email.com", "password": "short"},
    )
    assert res1.status_code == 422
    assert res1.json()["error"]["type"] == "VALIDATION_ERROR"

    # Test invalid email format
    res2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email-format", "password": "ValidPassword123!"},
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["type"] == "VALIDATION_ERROR"

    # Test empty payload
    res3 = await client.post("/api/v1/auth/register", json={})
    assert res3.status_code == 422


# ==============================================================================
# 4. Login Success
# ==============================================================================
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify login validates credentials and returns session tokens with user profile."""
    payload = {"email": "student@verifai.app", "password": "SecurePassword123!"}

    mock_auth_response = {
        "user": {"id": str(mock_user_id), "email": "student@verifai.app"},
        "session": {
            "access_token": "new-access-token-789",
            "refresh_token": "new-refresh-token-012",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_in_with_password", new_callable=AsyncMock) as mock_login, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_login.return_value = mock_auth_response
        mock_get_user.return_value = sample_user_record

        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session"]["access_token"] == "new-access-token-789"
        assert data["data"]["user"]["email"] == "student@verifai.app"


# ==============================================================================
# 5. Invalid Credentials
# ==============================================================================
@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Verify incorrect credentials return 401 INVALID_CREDENTIALS."""
    payload = {"email": "student@verifai.app", "password": "WrongPassword!"}

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_in_with_password", new_callable=AsyncMock) as mock_login:
        mock_login.side_effect = InvalidCredentialsError("Invalid email or password")

        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "INVALID_CREDENTIALS"


# ==============================================================================
# 6. Current User Success (GET /auth/me)
# ==============================================================================
@pytest.mark.asyncio
async def test_current_user_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify GET /auth/me returns safe public profile when authenticated."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_get_auth_user.return_value = {"id": str(mock_user_id), "email": "student@verifai.app"}
        mock_get_user.return_value = sample_user_record

        headers = {"Authorization": "Bearer valid-mock-token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(mock_user_id)
        assert data["data"]["email"] == "student@verifai.app"
        assert data["data"]["display_name"] == "Arun Prasath"
        assert "password" not in data["data"]


# ==============================================================================
# 7. Missing Token (401 UNAUTHORIZED)
# ==============================================================================
@pytest.mark.asyncio
async def test_current_user_missing_token(client: AsyncClient):
    """Verify accessing protected route without token returns 401 UNAUTHORIZED."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 8. Invalid Token (401 INVALID_TOKEN)
# ==============================================================================
@pytest.mark.asyncio
async def test_current_user_invalid_token(client: AsyncClient):
    """Verify invalid or forged token returns 401 INVALID_TOKEN."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user:
        mock_get_auth_user.side_effect = InvalidTokenError("Invalid authentication token")

        headers = {"Authorization": "Bearer forged-token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "INVALID_TOKEN"


# ==============================================================================
# 9. Expired Token (401 EXPIRED_TOKEN)
# ==============================================================================
@pytest.mark.asyncio
async def test_current_user_expired_token(client: AsyncClient):
    """Verify expired token returns 401 EXPIRED_TOKEN."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user:
        mock_get_auth_user.side_effect = ExpiredTokenError("Authentication token has expired")

        headers = {"Authorization": "Bearer expired-token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "EXPIRED_TOKEN"


# ==============================================================================
# 10. Profile Update Success (PATCH /auth/me)
# ==============================================================================
@pytest.mark.asyncio
async def test_profile_update_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify updating display_name succeeds and refreshes profile."""
    updated_record = dict(sample_user_record)
    updated_record["display_name"] = "Arun P."

    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.update_user", new_callable=AsyncMock) as mock_update_user, \
         patch("app.api.v1.endpoints.auth.supabase_auth_service.update_user", new_callable=AsyncMock):
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record
        mock_update_user.return_value = updated_record

        headers = {"Authorization": "Bearer valid-token"}
        response = await client.patch(
            "/api/v1/auth/me",
            headers=headers,
            json={"display_name": "Arun P."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["display_name"] == "Arun P."


# ==============================================================================
# 11. Unauthorized Profile Access
# ==============================================================================
@pytest.mark.asyncio
async def test_profile_update_unauthorized(client: AsyncClient):
    """Verify unauthorized request to update profile is rejected without token."""
    response = await client.patch("/api/v1/auth/me", json={"display_name": "Hacker"})
    assert response.status_code == 401
    assert response.json()["error"]["type"] == "UNAUTHORIZED"


# ==============================================================================
# 12. Refresh Success (POST /auth/refresh)
# ==============================================================================
@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify valid refresh token issues new tokens and user profile."""
    mock_refresh_response = {
        "user": {"id": str(mock_user_id), "email": "student@verifai.app"},
        "session": {
            "access_token": "renewed-access-token",
            "refresh_token": "renewed-refresh-token",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.refresh_session", new_callable=AsyncMock) as mock_refresh, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_refresh.return_value = mock_refresh_response
        mock_get_user.return_value = sample_user_record

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-existing-refresh-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session"]["access_token"] == "renewed-access-token"


# ==============================================================================
# 13. Invalid Refresh Token
# ==============================================================================
@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Verify invalid refresh token returns 401 INVALID_REFRESH_TOKEN."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.refresh_session", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.side_effect = InvalidRefreshTokenError("Invalid or expired refresh token")

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "bad-or-expired-token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "INVALID_REFRESH_TOKEN"


# ==============================================================================
# 14. Logout
# ==============================================================================
@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify logout terminates session in provider and returns success message."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_user_auth, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_out", new_callable=AsyncMock) as mock_sign_out:
        mock_get_user_auth.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record

        headers = {"Authorization": "Bearer active-session-token"}
        response = await client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["message"] == "Successfully logged out"
        mock_sign_out.assert_awaited_once_with("active-session-token")


# ==============================================================================
# 15. Account Deletion
# ==============================================================================
@pytest.mark.asyncio
async def test_account_deletion_success(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify deleting account removes DB profile and provider identity."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_user_auth, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.delete_user", new_callable=AsyncMock) as mock_delete_repo, \
         patch("app.api.v1.endpoints.auth.supabase_auth_service.delete_user", new_callable=AsyncMock) as mock_delete_auth:
        mock_get_user_auth.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record

        headers = {"Authorization": "Bearer delete-token"}
        response = await client.delete("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["message"] == "Account successfully deleted"
        mock_delete_repo.assert_awaited_once_with(mock_user_id)
        mock_delete_auth.assert_awaited_once_with(str(mock_user_id))


# ==============================================================================
# 16. Database Failure Handling
# ==============================================================================
@pytest.mark.asyncio
async def test_database_failure_handling(client: AsyncClient, mock_user_id):
    """Verify database exceptions return 500 DATABASE_ERROR and trigger cleanup."""
    payload = {
        "email": "dbfail@verifai.app",
        "password": "SecurePassword123!",
    }

    mock_auth_response = {
        "user": {"id": str(mock_user_id), "email": "dbfail@verifai.app"},
        "session": {"access_token": "token", "refresh_token": "refresh"},
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_up", new_callable=AsyncMock) as mock_sign_up, \
         patch("app.api.v1.endpoints.auth.user_repository.create_user", side_effect=Exception("Database connection timeout")), \
         patch("app.api.v1.endpoints.auth.supabase_auth_service.delete_user", new_callable=AsyncMock) as mock_delete:
        mock_sign_up.return_value = mock_auth_response

        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "DATABASE_ERROR"
        # Compensating transaction cleanup called
        mock_delete.assert_awaited_once_with(str(mock_user_id))


# ==============================================================================
# 17. Authentication Provider Failure Handling
# ==============================================================================
@pytest.mark.asyncio
async def test_auth_provider_failure_handling(client: AsyncClient):
    """Verify Supabase unreachable / timeout returns 502 AUTH_PROVIDER_ERROR."""
    payload = {"email": "test@verifai.app", "password": "Password123!"}

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_in_with_password", side_effect=AuthProviderError("Supabase unavailable")):
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "AUTH_PROVIDER_ERROR"


# ==============================================================================
# 18. User Identity Mapping Verification
# ==============================================================================
@pytest.mark.asyncio
async def test_user_identity_mapping(client: AsyncClient):
    """Verify application users.id strictly maps 1-to-1 to Supabase Auth UID."""
    assigned_supabase_uid = uuid.uuid4()
    sample_record = {
        "id": assigned_supabase_uid,
        "email": "mapping@verifai.app",
        "display_name": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_up", new_callable=AsyncMock) as mock_sign_up, \
         patch("app.api.v1.endpoints.auth.user_repository.create_user", new_callable=AsyncMock) as mock_create_user:
        mock_sign_up.return_value = {
            "user": {"id": str(assigned_supabase_uid), "email": "mapping@verifai.app"},
            "session": {"access_token": "token", "refresh_token": "refresh"},
        }
        mock_create_user.return_value = sample_record

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "mapping@verifai.app", "password": "Password123!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["user"]["id"] == str(assigned_supabase_uid)
        mock_create_user.assert_awaited_once_with(
            user_id=str(assigned_supabase_uid),
            email="mapping@verifai.app",
            display_name=None,
        )


# ==============================================================================
# 19. SupabaseAuthService Unit Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_supabase_auth_service_methods():
    """Unit tests for SupabaseAuthService GoTrue API calling logic and error mapping."""
    mock_http_client = AsyncMock()
    service = SupabaseAuthService(client=mock_http_client)

    # 1. sign_up success
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "user": {"id": "test-id", "email": "test@verifai.app"},
        "session": {"access_token": "tok", "refresh_token": "ref"},
    }
    mock_http_client.post.return_value = mock_resp

    result = await service.sign_up("test@verifai.app", "password123")
    assert result["user"]["id"] == "test-id"

    # 2. sign_up duplicate account error mapping
    mock_resp_dup = MagicMock()
    mock_resp_dup.status_code = 400
    mock_resp_dup.content = b'{"msg": "User already registered"}'
    mock_resp_dup.json.return_value = {"msg": "User already registered"}
    mock_http_client.post.return_value = mock_resp_dup

    with pytest.raises(DuplicateAccountError):
        await service.sign_up("dup@verifai.app", "password123")

    # 3. sign_in invalid credentials
    mock_resp_cred = MagicMock()
    mock_resp_cred.status_code = 400
    mock_resp_cred.content = b'{"error": "invalid_grant", "error_description": "Invalid login credentials"}'
    mock_resp_cred.json.return_value = {
        "error": "invalid_grant",
        "error_description": "Invalid login credentials",
    }
    mock_http_client.post.return_value = mock_resp_cred

    with pytest.raises(InvalidCredentialsError):
        await service.sign_in_with_password("wrong@verifai.app", "badpass")

    # 4. get_user token expired
    mock_resp_exp = MagicMock()
    mock_resp_exp.status_code = 401
    mock_resp_exp.content = b'{"msg": "Token expired"}'
    mock_resp_exp.json.return_value = {"msg": "Token expired"}
    mock_http_client.get.return_value = mock_resp_exp

    with pytest.raises(ExpiredTokenError):
        await service.get_user("expired-token")

    # 5. refresh_session invalid refresh token
    mock_resp_ref = MagicMock()
    mock_resp_ref.status_code = 400
    mock_resp_ref.content = b'{"msg": "Invalid Refresh Token"}'
    mock_resp_ref.json.return_value = {"msg": "Invalid Refresh Token"}
    mock_http_client.post.return_value = mock_resp_ref

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh_session("bad-refresh")

    # 6. sign_out call
    mock_resp_out = MagicMock()
    mock_resp_out.status_code = 204
    mock_http_client.post.return_value = mock_resp_out
    await service.sign_out("token")

    # 7. delete_user call
    mock_resp_del = MagicMock()
    mock_resp_del.status_code = 200
    mock_http_client.delete.return_value = mock_resp_del
    await service.delete_user("test-user-id")


# ==============================================================================
# 20. Edge Cases and Error Paths
# ==============================================================================
@pytest.mark.asyncio
async def test_registration_auth_provider_failure(client: AsyncClient):
    """Verify registration handles AuthProviderError properly."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_up", side_effect=AuthProviderError("Service down")):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "providerdown@verifai.app", "password": "Password123!"},
        )
        assert response.status_code == 502
        assert response.json()["error"]["type"] == "AUTH_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_login_auto_sync_user(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify login creates user record if missing in DB."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_in_with_password", new_callable=AsyncMock) as mock_login, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.create_user", new_callable=AsyncMock) as mock_create_user:
        mock_login.return_value = {
            "user": {"id": str(mock_user_id), "email": "sync@verifai.app", "user_metadata": {"display_name": "Synced"}},
            "session": {"access_token": "tok", "refresh_token": "ref"},
        }
        mock_get_user.return_value = None  # Not yet in DB
        mock_create_user.return_value = sample_user_record

        response = await client.post("/api/v1/auth/login", json={"email": "sync@verifai.app", "password": "Password123!"})
        assert response.status_code == 200
        mock_create_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_database_error(client: AsyncClient, mock_user_id):
    """Verify login handles database errors gracefully."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.sign_in_with_password", new_callable=AsyncMock) as mock_login, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", side_effect=Exception("DB connection dropped")):
        mock_login.return_value = {
            "user": {"id": str(mock_user_id), "email": "dberr@verifai.app"},
            "session": {"access_token": "tok", "refresh_token": "ref"},
        }
        response = await client.post("/api/v1/auth/login", json={"email": "dberr@verifai.app", "password": "Password123!"})
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_update_me_database_error(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify update_me handles database error."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.update_user", side_effect=Exception("DB write failed")):
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record

        response = await client.patch("/api/v1/auth/me", headers={"Authorization": "Bearer tok"}, json={"display_name": "New"})
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_update_me_user_not_found(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify update_me returns 404 if record update returns None."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.update_user", new_callable=AsyncMock) as mock_update_user:
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record
        mock_update_user.return_value = None

        response = await client.patch("/api/v1/auth/me", headers={"Authorization": "Bearer tok"}, json={"display_name": "New"})
        assert response.status_code == 404
        assert response.json()["error"]["type"] == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_me_database_error(client: AsyncClient, mock_user_id, sample_user_record):
    """Verify delete_me handles database failure."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.v1.endpoints.auth.user_repository.delete_user", side_effect=Exception("DB delete failed")):
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = sample_user_record

        response = await client.delete("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_refresh_token_auth_provider_error(client: AsyncClient):
    """Verify refresh handles AuthProviderError."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.refresh_session", side_effect=AuthProviderError("Timeout")):
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "valid-ref"})
        assert response.status_code == 502
        assert response.json()["error"]["type"] == "AUTH_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_refresh_token_database_error(client: AsyncClient, mock_user_id):
    """Verify refresh handles database error."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.refresh_session", new_callable=AsyncMock) as mock_refresh, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", side_effect=Exception("DB error")):
        mock_refresh.return_value = {
            "user": {"id": str(mock_user_id)},
            "session": {"access_token": "tok", "refresh_token": "ref"},
        }
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "valid-ref"})
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_refresh_token_user_not_found_in_db(client: AsyncClient, mock_user_id):
    """Verify refresh returns 404 when user is not found in DB."""
    with patch("app.api.v1.endpoints.auth.supabase_auth_service.refresh_session", new_callable=AsyncMock) as mock_refresh, \
         patch("app.api.v1.endpoints.auth.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_refresh.return_value = {
            "user": {"id": str(mock_user_id)},
            "session": {"access_token": "tok", "refresh_token": "ref"},
        }
        mock_get_user.return_value = None

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "valid-ref"})
        assert response.status_code == 404
        assert response.json()["error"]["type"] == "USER_NOT_FOUND"


# ==============================================================================
# 21. Dependencies Branch Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_get_current_user_auth_provider_error(client: AsyncClient):
    """Verify dependencies handle AuthProviderError from Supabase."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", side_effect=AuthProviderError("Down")):
        response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert response.status_code == 502
        assert response.json()["error"]["type"] == "AUTH_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_get_current_user_missing_user_id_in_payload(client: AsyncClient):
    """Verify dependencies handle payload without id or sub."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"email": "no-id@verifai.app"}
        response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert response.status_code == 401
        assert response.json()["error"]["type"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_get_current_user_database_error(client: AsyncClient, mock_user_id):
    """Verify dependencies handle database exception."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", side_effect=Exception("DB pool timeout")):
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_get_current_user_not_found_in_database(client: AsyncClient, mock_user_id):
    """Verify dependencies return 404 when user exists in auth provider but not application DB."""
    with patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as mock_get_auth_user, \
         patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_get_auth_user.return_value = {"id": str(mock_user_id)}
        mock_get_user.return_value = None
        response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert response.status_code == 404
        assert response.json()["error"]["type"] == "USER_NOT_FOUND"


# ==============================================================================
# 22. SupabaseAuthService Comprehensive Unit Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_supabase_auth_service_extended_coverage():
    """Test all error branches and network failures in SupabaseAuthService."""
    import httpx
    from app.services.supabase_auth import AuthServiceError

    mock_client = AsyncMock()
    service = SupabaseAuthService(client=mock_client)

    # 1. Default client creation
    default_service = SupabaseAuthService()
    created_client = await default_service._get_client()
    assert isinstance(created_client, httpx.AsyncClient)
    await created_client.aclose()

    # 2. sign_up HTTP 500 and network error
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500
    mock_client.post.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.sign_up("err@test.com", "pass")

    mock_resp_400 = MagicMock()
    mock_resp_400.status_code = 400
    mock_resp_400.content = b'{"msg": "Password too weak"}'
    mock_resp_400.json.return_value = {"msg": "Password too weak"}
    mock_client.post.return_value = mock_resp_400
    with pytest.raises(AuthServiceError):
        await service.sign_up("weak@test.com", "pass")

    mock_client.post.side_effect = httpx.ConnectError("Network failure")
    with pytest.raises(AuthProviderError):
        await service.sign_up("net@test.com", "pass")

    # 3. sign_in HTTP 500, other error, and network error
    mock_client.post.side_effect = None
    mock_client.post.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.sign_in_with_password("err@test.com", "pass")

    mock_resp_403 = MagicMock()
    mock_resp_403.status_code = 403
    mock_resp_403.content = b'{"msg": "Account locked"}'
    mock_resp_403.json.return_value = {"msg": "Account locked"}
    mock_client.post.return_value = mock_resp_403
    with pytest.raises(AuthServiceError):
        await service.sign_in_with_password("lock@test.com", "pass")

    mock_client.post.side_effect = httpx.TimeoutException("Timeout")
    with pytest.raises(AuthProviderError):
        await service.sign_in_with_password("timeout@test.com", "pass")

    # 4. refresh_session HTTP 500, other error, and network error
    mock_client.post.side_effect = None
    mock_client.post.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.refresh_session("ref")

    mock_client.post.return_value = mock_resp_403
    with pytest.raises(AuthServiceError):
        await service.refresh_session("ref")

    mock_client.post.side_effect = httpx.ConnectError("Timeout")
    with pytest.raises(AuthProviderError):
        await service.refresh_session("ref")

    # 5. get_user invalid token, 500, and network error
    mock_client.get.side_effect = None
    mock_resp_inv = MagicMock()
    mock_resp_inv.status_code = 401
    mock_resp_inv.content = b'{"msg": "invalid jwt"}'
    mock_resp_inv.json.return_value = {"msg": "invalid jwt"}
    mock_client.get.return_value = mock_resp_inv
    with pytest.raises(InvalidTokenError):
        await service.get_user("bad-jwt")

    mock_client.get.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.get_user("token")

    mock_resp_403_get = MagicMock()
    mock_resp_403_get.status_code = 403
    mock_resp_403_get.content = b'{"msg": "Forbidden"}'
    mock_resp_403_get.json.return_value = {"msg": "Forbidden"}
    mock_client.get.return_value = mock_resp_403_get
    with pytest.raises(AuthServiceError):
        await service.get_user("token")

    mock_client.get.side_effect = httpx.ConnectError("Down")
    with pytest.raises(AuthProviderError):
        await service.get_user("token")

    # 6. update_user success, 401, 500, network error, and other error
    mock_client.put.side_effect = None
    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"id": "uid"}
    mock_client.put.return_value = mock_resp_200
    res = await service.update_user("tok", "New Display")
    assert res["id"] == "uid"

    mock_client.put.return_value = mock_resp_inv
    with pytest.raises(InvalidTokenError):
        await service.update_user("tok", "New Display")

    mock_client.put.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.update_user("tok", "New Display")

    mock_client.put.return_value = mock_resp_403_get
    with pytest.raises(AuthServiceError):
        await service.update_user("tok", "New Display")

    mock_client.put.side_effect = httpx.ConnectError("Down")
    with pytest.raises(AuthProviderError):
        await service.update_user("tok", "New Display")

    # 7. sign_out network error
    mock_client.post.side_effect = httpx.ConnectError("Down")
    await service.sign_out("tok")  # Should not raise

    mock_client.post.side_effect = None
    mock_client.post.return_value = mock_resp_400
    await service.sign_out("tok")  # Should log warning but not raise

    # 8. delete_user without service role key, network error, 404, 500, other
    service_no_key = SupabaseAuthService(client=mock_client)
    service_no_key.service_role_key = ""
    await service_no_key.delete_user("uid")  # Should return cleanly

    mock_client.delete.side_effect = httpx.ConnectError("Down")
    with pytest.raises(AuthProviderError):
        await service.delete_user("uid")

    mock_client.delete.side_effect = None
    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404
    mock_client.delete.return_value = mock_resp_404
    await service.delete_user("uid")  # Should return cleanly on 404

    mock_client.delete.return_value = mock_resp_500
    with pytest.raises(AuthProviderError):
        await service.delete_user("uid")

    mock_client.delete.return_value = mock_resp_400
    with pytest.raises(AuthServiceError):
        await service.delete_user("uid")

