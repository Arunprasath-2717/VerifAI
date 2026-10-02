"""Cryptographic security, Argon2id password hashing, and JWT token management."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import argon2
import jwt

from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.models.user import User
from app.schemas.auth import UserRole

logger = logging.getLogger("verifai.security")

# Argon2id password hasher configured to OWASP / IETF RFC 9106 recommendations
_PASSWORD_HASHER = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB
    parallelism=1,
    hash_len=32,
    type=argon2.Type.ID,
)

# Ephemeral user store for development/testing when running without database
_EPHEMERAL_USERS: dict[uuid.UUID, User] = {}
_EPHEMERAL_USERS_BY_EMAIL: dict[str, uuid.UUID] = {}
_EPHEMERAL_USERS_BY_USERNAME: dict[str, uuid.UUID] = {}


def clear_ephemeral_users() -> None:
    """Clear in-memory user registry for hermetic testing."""
    _EPHEMERAL_USERS.clear()
    _EPHEMERAL_USERS_BY_EMAIL.clear()
    _EPHEMERAL_USERS_BY_USERNAME.clear()


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id with unique cryptographic salt."""
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")
    return _PASSWORD_HASHER.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored Argon2id hash (constant-time)."""
    if not plain_password or not hashed_password:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed_password, plain_password)
    except (
        argon2.exceptions.VerifyMismatchError,
        argon2.exceptions.VerificationError,
        argon2.exceptions.InvalidHashError,
    ):
        return False


def create_access_token(
    subject: str | uuid.UUID,
    role: str | UserRole,
    expires_delta: timedelta | None = None,
    settings: Settings | None = None,
) -> tuple[str, int]:
    """Generate signed JWT access token adhering to locked algorithm and claims.

    Returns:
        (access_token, expires_in_seconds)
    """
    app_settings = settings or get_settings()
    now = datetime.now(UTC)

    if expires_delta:
        expire = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expires_in = app_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire = now + timedelta(seconds=expires_in)

    role_str = role.value if isinstance(role, UserRole) else str(role)

    # Standard JWT claims: sub, role, iss, aud, iat, nbf, exp
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role_str,
        "iss": app_settings.JWT_ISSUER,
        "aud": app_settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    secret = app_settings.JWT_SECRET.get_secret_value()
    token = jwt.encode(
        payload,
        secret,
        algorithm=app_settings.JWT_ALGORITHM,
    )
    return token, expires_in


def decode_access_token(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Validate JWT signature, expiration, issuer, audience, and subject claims.

    Rejects unauthorized algorithms, expired tokens, or malformed payloads.
    """
    app_settings = settings or get_settings()
    secret = app_settings.JWT_SECRET.get_secret_value()

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[app_settings.JWT_ALGORITHM],
            issuer=app_settings.JWT_ISSUER,
            audience=app_settings.JWT_AUDIENCE,
            options={"require": ["sub", "iss", "aud", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(
            message="Access token has expired. Please log in again.",
            details={"reason": "token_expired"},
        ) from exc
    except jwt.InvalidAlgorithmError as exc:
        raise UnauthorizedError(
            message="Unsupported or rejected cryptographic algorithm in token.",
            details={"reason": "invalid_algorithm"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(
            message="Invalid access token.",
            details={"reason": "invalid_token"},
        ) from exc

    subject = payload.get("sub")
    if not subject or not str(subject).strip():
        raise UnauthorizedError(
            message="Token subject is missing or malformed.",
            details={"reason": "missing_subject"},
        )

    return payload
