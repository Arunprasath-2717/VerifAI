"""Authentication endpoints for VerifAI."""

import logging
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_current_user_and_token
from app.repositories.user_repository import UserRepository, user_repository
from app.schemas.auth import (
    AuthResponseData,
    AuthTokens,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import StandardResponse
from app.services.supabase_auth import (
    AuthProviderError,
    DuplicateAccountError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    SupabaseAuthService,
    supabase_auth_service,
)

logger = logging.getLogger("verifai.api.auth")

router = APIRouter()


@router.post(
    "/register",
    response_model=StandardResponse[AuthResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Creates a user identity in Supabase Auth and synchronizes profile in application database.",
)
async def register(
    payload: RegisterRequest,
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> StandardResponse[AuthResponseData]:
    """Execute registration flow: Supabase Auth identity creation followed by database sync."""
    try:
        auth_result = await auth_service.sign_up(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except DuplicateAccountError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "DUPLICATE_ACCOUNT",
                "message": exc.message,
                "details": {},
            },
        ) from exc
    except AuthProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "AUTH_PROVIDER_ERROR",
                "message": exc.message,
                "details": {},
            },
        ) from exc

    supabase_user = auth_result["user"]
    user_id = supabase_user["id"]

    # Synchronize into PostgreSQL application users table
    try:
        user_record = await repo.create_user(
            user_id=user_id,
            email=payload.email,
            display_name=payload.display_name,
        )
    except Exception as exc:
        logger.error("Failed to insert user profile into database: %s", exc)
        # Attempt compensating cleanup in Supabase to avoid orphaned identity
        try:
            await auth_service.delete_user(str(user_id))
        except Exception as cleanup_exc:
            logger.warning("Failed to clean up Supabase identity after DB error: %s", cleanup_exc)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to create application user profile in database",
                "details": {},
            },
        ) from exc

    user_response = UserResponse(
        id=user_record["id"],
        email=user_record["email"],
        display_name=user_record["display_name"],
        created_at=user_record["created_at"],
        updated_at=user_record["updated_at"],
    )
    tokens = AuthTokens(**auth_result["session"])

    return StandardResponse(
        success=True,
        data=AuthResponseData(user=user_response, session=tokens),
    )


@router.post(
    "/login",
    response_model=StandardResponse[AuthResponseData],
    summary="Authenticate user",
    description="Validates credentials via Supabase Auth and returns active session tokens and user profile.",
)
async def login(
    payload: LoginRequest,
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> StandardResponse[AuthResponseData]:
    """Execute login flow with credential validation."""
    try:
        auth_result = await auth_service.sign_in_with_password(
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "INVALID_CREDENTIALS",
                "message": exc.message,
                "details": {},
            },
        ) from exc
    except AuthProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "AUTH_PROVIDER_ERROR",
                "message": exc.message,
                "details": {},
            },
        ) from exc

    supabase_user = auth_result["user"]
    user_id = supabase_user["id"]

    try:
        user_record = await repo.get_user_by_id(user_id)
        if user_record is None:
            # Sync record if not yet created in public.users table
            user_record = await repo.create_user(
                user_id=user_id,
                email=payload.email,
                display_name=supabase_user.get("user_metadata", {}).get("display_name"),
            )
    except Exception as exc:
        logger.error("Database error while loading user %s on login: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Database error loading user profile",
                "details": {},
            },
        ) from exc

    user_response = UserResponse(
        id=user_record["id"],
        email=user_record["email"],
        display_name=user_record["display_name"],
        created_at=user_record["created_at"],
        updated_at=user_record["updated_at"],
    )
    tokens = AuthTokens(**auth_result["session"])

    return StandardResponse(
        success=True,
        data=AuthResponseData(user=user_response, session=tokens),
    )


@router.post(
    "/logout",
    response_model=StandardResponse[MessageResponse],
    summary="Log out active session",
    description="Revokes the active user session in Supabase Auth.",
)
async def logout(
    user_and_token: Tuple[UserResponse, str] = Depends(get_current_user_and_token),
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
) -> StandardResponse[MessageResponse]:
    """Execute logout by invalidating the current Bearer token in Supabase Auth."""
    _, token = user_and_token
    await auth_service.sign_out(token)
    return StandardResponse(
        success=True,
        data=MessageResponse(message="Successfully logged out"),
    )


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="Get current user profile",
    description="Returns the profile information for the authenticated user.",
)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> StandardResponse[UserResponse]:
    """Fetch current user profile."""
    return StandardResponse(
        success=True,
        data=current_user,
    )


@router.patch(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="Update current user profile",
    description="Updates supported user profile fields (display_name) and refreshes updated_at timestamp.",
)
async def update_me(
    payload: UserUpdateRequest,
    user_and_token: Tuple[UserResponse, str] = Depends(get_current_user_and_token),
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> StandardResponse[UserResponse]:
    """Update profile information for the authenticated user."""
    current_user, token = user_and_token

    try:
        updated_record = await repo.update_user(current_user.id, payload.display_name)
    except Exception as exc:
        logger.error("Database error updating user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to update user profile in database",
                "details": {},
            },
        ) from exc

    if updated_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "USER_NOT_FOUND",
                "message": "User profile not found",
                "details": {},
            },
        )

    # Synchronize display_name to Supabase Auth metadata
    try:
        await auth_service.update_user(token, payload.display_name)
    except Exception as exc:
        logger.warning("Non-fatal: failed to update metadata in Supabase Auth: %s", exc)

    return StandardResponse(
        success=True,
        data=UserResponse(
            id=updated_record["id"],
            email=updated_record["email"],
            display_name=updated_record["display_name"],
            created_at=updated_record["created_at"],
            updated_at=updated_record["updated_at"],
        ),
    )


@router.delete(
    "/me",
    response_model=StandardResponse[MessageResponse],
    summary="Delete account",
    description="Permanently deletes the application user profile and terminates the Supabase Auth identity.",
)
async def delete_me(
    current_user: UserResponse = Depends(get_current_user),
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> StandardResponse[MessageResponse]:
    """Delete current user account from database and auth provider."""
    try:
        await repo.delete_user(current_user.id)
    except Exception as exc:
        logger.error("Database error deleting user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to delete user profile from database",
                "details": {},
            },
        ) from exc

    # Remove identity from Supabase Auth
    try:
        await auth_service.delete_user(str(current_user.id))
    except Exception as exc:
        logger.warning("Provider cleanup error for user %s: %s", current_user.id, exc)

    return StandardResponse(
        success=True,
        data=MessageResponse(message="Account successfully deleted"),
    )


@router.post(
    "/refresh",
    response_model=StandardResponse[AuthResponseData],
    summary="Refresh access token",
    description="Exchanges an active refresh token for a newly issued access token and session payload.",
)
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: SupabaseAuthService = Depends(lambda: supabase_auth_service),
    repo: UserRepository = Depends(lambda: user_repository),
) -> StandardResponse[AuthResponseData]:
    """Renew session using refresh token."""
    try:
        auth_result = await auth_service.refresh_session(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "INVALID_REFRESH_TOKEN",
                "message": exc.message,
                "details": {},
            },
        ) from exc
    except AuthProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "AUTH_PROVIDER_ERROR",
                "message": exc.message,
                "details": {},
            },
        ) from exc

    supabase_user = auth_result["user"]
    user_id = supabase_user["id"]

    try:
        user_record = await repo.get_user_by_id(user_id)
    except Exception as exc:
        logger.error("Database error during token refresh for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Database error loading user profile during token refresh",
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

    user_response = UserResponse(
        id=user_record["id"],
        email=user_record["email"],
        display_name=user_record["display_name"],
        created_at=user_record["created_at"],
        updated_at=user_record["updated_at"],
    )
    tokens = AuthTokens(**auth_result["session"])

    return StandardResponse(
        success=True,
        data=AuthResponseData(user=user_response, session=tokens),
    )
