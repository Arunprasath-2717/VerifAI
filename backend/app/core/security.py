"""Cryptographic security, Argon2id password hashing, and JWT token management."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import argon2
import jwt

from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
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


_GOOGLE_JWKS_URL = "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
_JWKS_CLIENT: jwt.PyJWKClient | None = None


def get_jwks_client() -> jwt.PyJWKClient:
    """Return singleton PyJWKClient configured with Google's public JWKS."""
    global _JWKS_CLIENT
    if _JWKS_CLIENT is None:
        _JWKS_CLIENT = jwt.PyJWKClient(
            _GOOGLE_JWKS_URL,
            cache_keys=True,
            max_cached_keys=16,
        )
    return _JWKS_CLIENT


def verify_firebase_id_token(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Validate a Firebase Auth ID token against Google's public keys.

    Validates:
    - Algorithm is RS256
    - Audience matches FIREBASE_PROJECT_ID
    - Issuer matches https://securetoken.google.com/{FIREBASE_PROJECT_ID}
    - Signature, expiration, and required subject
    """
    app_settings = settings or get_settings()
    project_id = app_settings.FIREBASE_PROJECT_ID
    issuer = f"https://securetoken.google.com/{project_id}"

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=issuer,
            options={"require": ["sub", "iss", "aud", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(
            message="Firebase access token has expired.",
            details={"reason": "token_expired"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(
            message=f"Invalid Firebase access token: {str(exc)}",
            details={"reason": "invalid_firebase_token"},
        ) from exc
    except Exception as exc:
        raise UnauthorizedError(
            message=f"Firebase token verification failed: {str(exc)}",
            details={"reason": "firebase_verification_failed"},
        ) from exc

    subject = payload.get("sub")
    if not subject or not str(subject).strip():
        raise UnauthorizedError(
            message="Firebase token missing subject (uid).",
            details={"reason": "missing_subject"},
        )

    return payload


def decode_access_token(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Validate JWT signature, expiration, issuer, audience, and subject claims.

    Supports both VerifAI internal HS256 tokens and Firebase Auth RS256 ID tokens.
    """
    app_settings = settings or get_settings()

    # Detect algorithm from token header
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise UnauthorizedError(
            message="Malformed or unparseable access token header.",
            details={"reason": "unparseable_header"},
        ) from exc

    alg = unverified_header.get("alg")

    # If RS256 and Firebase is enabled, route to Firebase verification
    if alg == "RS256" and app_settings.FIREBASE_AUTH_ENABLED:
        return verify_firebase_id_token(token, settings=app_settings)

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


def clear_ephemeral_users() -> None:
    """Clear users table for testing and teardowns."""
    import asyncio
    import concurrent.futures

    from sqlalchemy import delete

    from app.core.database import get_async_session_maker
    from app.models.user import User

    async def _clean() -> None:
        maker = get_async_session_maker()
        async with maker() as session:
            await session.execute(delete(User))
            await session.commit()

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, _clean()).result()
        else:
            asyncio.run(_clean())
    except Exception as exc:
        logger.debug("Best-effort test user cleanup failed: %s", type(exc).__name__)
