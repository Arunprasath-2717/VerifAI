"""Reusable authentication and authorization dependencies for FastAPI endpoints."""

import logging
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.user_repository import UserRepository, user_repository
from app.schemas.auth import UserResponse
from app.services.supabase_auth import (
    AuthProviderError,
    ExpiredTokenError,
    InvalidTokenError,
    SupabaseAuthService,
    supabase_auth_service,
)

logger = logging.getLogger("verifai.api.dependencies")

# auto_error=False allows us to return our standardized JSON error envelope on missing tokens
security = HTTPBearer(auto_error=False)


async def get_token_credentials(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract and validate the raw Bearer token from the Authorization header."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "UNAUTHORIZED",
                "message": "Missing or invalid authentication credentials",
                "details": {},
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_token_credentials),
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> UserResponse:
    """Validate Bearer token via Supabase Auth and retrieve the current application user profile.

    Reusable across Web UI, Browser Extension, and MCP protected endpoints.
    """
    try:
        provider_user = await auth_service.get_user(token)
    except ExpiredTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "EXPIRED_TOKEN",
                "message": exc.message,
                "details": {},
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except (InvalidTokenError, Exception) as exc:
        if isinstance(exc, AuthProviderError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "type": "AUTH_PROVIDER_ERROR",
                    "message": exc.message,
                    "details": {},
                },
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "INVALID_TOKEN",
                "message": "Invalid authentication token",
                "details": {},
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = provider_user.get("id") or provider_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "INVALID_TOKEN",
                "message": "Invalid token payload: missing user identity",
                "details": {},
            },
        )

    # Retrieve application user profile from PostgreSQL
    try:
        user_record = await repo.get_user_by_id(user_id)
    except Exception as exc:
        logger.error("Database error while fetching user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "A database error occurred while fetching user profile",
                "details": {},
            },
        ) from exc

    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "USER_NOT_FOUND",
                "message": "User profile not found in application database",
                "details": {},
            },
        )

    return UserResponse(
        id=user_record["id"],
        email=user_record["email"],
        display_name=user_record["display_name"],
        created_at=user_record["created_at"],
        updated_at=user_record["updated_at"],
    )


async def get_current_user_and_token(
    token: str = Depends(get_token_credentials),
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> Tuple[UserResponse, str]:
    """Retrieve both the validated UserResponse and the raw Bearer token."""
    user = await get_current_user(token=token, auth_service=auth_service, repo=repo)
    return user, token
