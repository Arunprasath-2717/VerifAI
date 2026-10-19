"""Authentication and user management endpoints.

Architecture:
- Router acts as a clean HTTP controller.
- Business logic is delegated to AuthenticationService.
- Persistence is handled by UserRepository.
"""

import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_async_session, get_current_user
from app.core.rate_limit import enforce_rate_limit
from app.core.security import verify_firebase_id_token
from app.models.user import User
from app.modules.auth.service import AuthenticationService
from app.repositories.user import UserRepository
from app.schemas.auth import (
    FirebaseAuthRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserRole,
)

logger = logging.getLogger("verifai.api.auth")
router = APIRouter()


def get_auth_service(
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> AuthenticationService:
    """Dependency provider injecting AuthenticationService with UserRepository."""
    return AuthenticationService(
        user_repository=UserRepository(db),
        settings=settings,
        token_verifier=verify_firebase_id_token,
    )


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description=(
        "Registers a new user account with secure Argon2id password hashing. "
        "All registrations strictly default to the 'USER' role to prevent "
        "privilege escalation. Requires an active database connection."
    ),
)
async def register(
    request_data: UserRegisterRequest,
    http_request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    """Register a new user account with a password credential."""
    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="register",
            limit=settings.RATE_LIMIT_REGISTER_PER_MINUTE,
            window_seconds=60.0,
            settings=settings,
        )

    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    return await auth_service.register_user(
        request_data, ip_address=ip_address, user_agent=user_agent
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Obtain Session Token",
    description=(
        "Authenticates email/password credentials and returns a signed "
        "JWT session token. For Firebase-based auth, use POST /auth/firebase."
    ),
)
async def login(
    login_data: UserLoginRequest,
    http_request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate user with email/username and password."""
    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="login",
            limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
            window_seconds=60.0,
            settings=settings,
        )

    return await auth_service.authenticate_local(login_data)


@router.get(
    "/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns identity and role of currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=UserRole(current_user.role),
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post(
    "/auth/firebase",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate via Firebase Auth (PRIMARY)",
    description=(
        "Validates a Google/Firebase ID token (RS256), synchronizes the user account "
        "to the PostgreSQL users table (auto-provisioning on first login), "
        "and returns a VerifAI session token. "
        "This is the PRIMARY authentication path for all clients."
    ),
)
async def authenticate_with_firebase(
    request: FirebaseAuthRequest,
    http_request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate or synchronize user via Firebase Auth ID token."""
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    token_response, _ = await auth_service.authenticate_firebase(
        request.id_token,
        display_name=request.display_name,
        terms_accepted=request.terms_accepted,
        is_signup=request.is_signup,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return token_response
