"""Comprehensive tests for authentication, Argon2id hashing, JWT, and RBAC."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.dependencies import require_roles
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import (
    clear_ephemeral_users,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from collections.abc import Generator

from app.models.user import User
from app.schemas.auth import UserRole


@pytest.fixture(autouse=True)
def clean_users() -> Generator[None, None, None]:
    """Ensure in-memory user registry is clean before and after each test."""
    clear_ephemeral_users()
    yield
    clear_ephemeral_users()


def test_argon2id_hashing_and_verification() -> None:
    """Verify Argon2id produces valid salted hashes and verifies in constant time."""
    password = "SecurePassword123!"
    hashed = hash_password(password)

    # Hash must start with Argon2id identifier
    assert hashed.startswith("$argon2id$")

    # Verification must succeed for matching password
    assert verify_password(password, hashed) is True

    # Verification must fail for wrong password
    assert verify_password("WrongPassword999!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False

    # Unique salts: hashing the same password twice yields different hashes
    hashed2 = hash_password(password)
    assert hashed != hashed2
    assert verify_password(password, hashed2) is True


def test_jwt_token_creation_and_decoding() -> None:
    """Verify signed JWT token claims: sub, role, iss, aud, exp, iat."""
    user_id = uuid.uuid4()
    settings = get_settings()

    token, expires_in = create_access_token(
        subject=user_id,
        role=UserRole.ANALYST,
        settings=settings,
    )
    assert isinstance(token, str)
    assert expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    payload = decode_access_token(token, settings=settings)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "ANALYST"
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["exp"] > payload["iat"]


def test_jwt_rejects_expired_token() -> None:
    """Verify that expired JWT access tokens raise UnauthorizedError."""
    user_id = uuid.uuid4()
    settings = get_settings()

    token, _ = create_access_token(
        subject=user_id,
        role=UserRole.USER,
        expires_delta=timedelta(seconds=-10),  # expired 10s ago
        settings=settings,
    )

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(token, settings=settings)
    assert "expired" in str(exc_info.value.message).lower()


def test_jwt_rejects_tampered_signature() -> None:
    """Verify that tampering with token signature or payload fails validation."""
    user_id = uuid.uuid4()
    settings = get_settings()

    token, _ = create_access_token(
        subject=user_id, role=UserRole.USER, settings=settings
    )
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"

    with pytest.raises(UnauthorizedError):
        decode_access_token(tampered_token, settings=settings)


def test_jwt_rejects_unsupported_algorithm() -> None:
    """Verify that tokens using 'none' or unapproved algorithms are rejected."""
    settings = get_settings()
    now = datetime.now(UTC)
    unauthorized_payload = {
        "sub": str(uuid.uuid4()),
        "role": "USER",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    # Unsigned token using algorithm="none"
    unsigned_token = jwt.encode(unauthorized_payload, key="", algorithm="none")

    with pytest.raises(UnauthorizedError):
        decode_access_token(unsigned_token, settings=settings)


def test_user_registration_success(client: TestClient) -> None:
    """Verify successful user registration with strict default USER role."""
    payload = {
        "email": "researcher@example.com",
        "username": "researcher_01",
        "password": "StrongPassword2026!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "researcher@example.com"
    assert data["username"] == "researcher_01"
    assert data["role"] == "USER"  # Strictly defaults to USER
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data


def test_user_registration_validation_rules(client: TestClient) -> None:
    """Verify input validation for invalid email, username, and password."""
    # Invalid email
    r1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "username": "valid_user",
            "password": "Pass12345678!",
        },
    )
    assert r1.status_code == 422

    # Username too short
    r2 = client.post(
        "/api/v1/auth/register",
        json={"email": "u@test.com", "username": "ab", "password": "Pass12345678!"},
    )
    assert r2.status_code == 422

    # Password lacking digit
    r3 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "u@test.com",
            "username": "valid_user",
            "password": "PasswordOnly",
        },
    )
    assert r3.status_code == 422

    # Password lacking letter
    r4 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "u@test.com",
            "username": "valid_user",
            "password": "123456789012",
        },
    )
    assert r4.status_code == 422


def test_user_registration_duplicate_conflict(client: TestClient) -> None:
    """Verify 409 Conflict when attempting to register duplicate email or username."""
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicate_user",
        "password": "ValidPassword123!",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Attempt duplicate email
    r2 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "other_username",
            "password": "ValidPassword123!",
        },
    )
    assert r2.status_code == 409
    assert "already registered" in r2.json()["error"]["message"].lower()

    # Attempt duplicate username
    r3 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "duplicate_user",
            "password": "ValidPassword123!",
        },
    )
    assert r3.status_code == 409
    assert "already registered" in r3.json()["error"]["message"].lower()


def test_login_and_me_lifecycle(client: TestClient) -> None:
    """Verify full auth flow: register -> login -> inspect /auth/me."""
    reg_payload = {
        "email": "lifecycle@example.com",
        "username": "lifecycle_user",
        "password": "SecretPassword2026!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login with username
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "lifecycle_user", "password": "SecretPassword2026!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # Access /auth/me with Bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "lifecycle@example.com"
    assert me_data["username"] == "lifecycle_user"
    assert me_data["role"] == "USER"


def test_login_with_email(client: TestClient) -> None:
    """Verify login works interchangeably with email address."""
    reg_payload = {
        "email": "email_login@example.com",
        "username": "email_user",
        "password": "SecretPassword2026!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": "email_login@example.com",
            "password": "SecretPassword2026!",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_login_failure_invalid_credentials(client: TestClient) -> None:
    """Verify 401 Unauthorized on invalid email/username or wrong password."""
    # Unknown user
    r1 = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": "non_existent_user",
            "password": "WrongPassword123!",
        },
    )
    assert r1.status_code == 401
    assert "invalid" in r1.json()["error"]["message"].lower()

    # Known user with wrong password
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpwd@example.com",
            "username": "wrongpwd_user",
            "password": "CorrectPassword123!",
        },
    )
    r2 = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": "wrongpwd_user",
            "password": "IncorrectPassword999!",
        },
    )
    assert r2.status_code == 401
    assert "invalid" in r2.json()["error"]["message"].lower()


def test_auth_me_unauthorized_without_token(client: TestClient) -> None:
    """Verify 401 Unauthorized when accessing /auth/me without Bearer header."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "authentication required" in response.json()["error"]["message"].lower()


@pytest.mark.anyio
async def test_rbac_require_roles_enforcement() -> None:
    """Verify require_roles dependency permits authorized roles and rejects unauthorized."""
    normal_user = User(
        id=uuid.uuid4(),
        email="user@test.com",
        username="normal_user",
        hashed_password="hash",
        role=UserRole.USER.value,
        is_active=True,
    )
    analyst_user = User(
        id=uuid.uuid4(),
        email="analyst@test.com",
        username="analyst_user",
        hashed_password="hash",
        role=UserRole.ANALYST.value,
        is_active=True,
    )
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        username="admin_user",
        hashed_password="hash",
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    admin_checker = require_roles([UserRole.ADMIN])
    analyst_or_admin = require_roles([UserRole.ANALYST, UserRole.ADMIN])

    # Admin passes both
    assert await admin_checker(current_user=admin_user) == admin_user
    assert await analyst_or_admin(current_user=admin_user) == admin_user

    # Analyst passes analyst_or_admin but fails admin_checker
    assert await analyst_or_admin(current_user=analyst_user) == analyst_user
    with pytest.raises(ForbiddenError):
        await admin_checker(current_user=analyst_user)

    # Normal user fails both admin and analyst checks
    with pytest.raises(ForbiddenError):
        await admin_checker(current_user=normal_user)
    with pytest.raises(ForbiddenError):
        await analyst_or_admin(current_user=normal_user)
