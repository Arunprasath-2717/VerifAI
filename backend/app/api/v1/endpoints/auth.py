"""Authentication and user management endpoints.

Authentication architecture:
- PRIMARY:  Firebase Auth RS256 JWT → POST /auth/firebase → VerifAI session token
- RETAINED: Local email/password login (for users created before Firebase migration)
- REMOVED:  Silent in-memory ephemeral fallbacks (database is required)
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_async_session, get_current_user
from app.core.errors import ConflictError, UnauthorizedError
from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    create_access_token,
    hash_password,
    verify_firebase_id_token,
    verify_password,
)
from app.models.user import User
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
    db: AsyncSession = Depends(get_async_session),
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

    email_clean = request_data.email.strip().lower()
    username_clean = request_data.username.strip()

    # Check for duplicate email or username
    stmt = select(User).where(
        or_(User.email == email_clean, User.username == username_clean)
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        field = "Email" if existing.email == email_clean else "Username"
        raise ConflictError(
            message=f"{field} is already registered.",
            details={"field": field.lower()},
        )

    # Hash password with Argon2id
    hashed = hash_password(request_data.password)
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    new_user = User(
        id=user_id,
        email=email_clean,
        username=username_clean,
        hashed_password=hashed,
        role=UserRole.USER.value,  # Strictly defaults to USER
        is_active=True,
    )
    new_user.created_at = now
    new_user.updated_at = now

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info("New user registered: %s (%s)", username_clean, user_id)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        role=UserRole(new_user.role),
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Obtain Session Token",
    description=(
        "Authenticates email/password credentials and returns a signed JWT session token. "
        "For Firebase-based auth, use POST /auth/firebase instead."
    ),
)
async def login(
    login_data: UserLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
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

    identifier = login_data.email_or_username.strip()

    stmt = select(User).where(
        or_(
            User.email == identifier.lower(),
            User.username == identifier,
        )
    )
    user: User | None = (await db.execute(stmt)).scalar_one_or_none()

    # Constant-time verification check
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning("Failed login attempt for identifier '%s'", identifier)
        raise UnauthorizedError(
            message="Invalid email/username or password.",
            details={"identifier": identifier},
        )

    if not user.is_active:
        raise UnauthorizedError(
            message="User account is deactivated.",
            details={"user_id": str(user.id)},
        )

    token, expires_in = create_access_token(
        subject=user.id,
        role=user.role,
        settings=settings,
    )

    logger.info("Successful login for user %s (%s)", user.username, user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        role=UserRole(user.role),
        user_id=user.id,
    )


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
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate or synchronize user via Firebase Auth ID token.

    Flow:
    1. Verify the Firebase ID token signature against Google JWKS.
    2. Compute deterministic UUIDv5 from firebase:{uid} for FK compatibility.
    3. Upsert user record in PostgreSQL.
    4. Return a VerifAI-issued session token (HS256, short-lived).
    """
    payload = verify_firebase_id_token(request.id_token, settings=settings)
    sub = str(payload.get("sub"))
    user_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{sub}")

    stmt = select(User).where(User.id == user_uuid)
    user: User | None = (await db.execute(stmt)).scalar_one_or_none()

    if user is None:
        # First Firebase login — auto-provision account
        email = str(payload.get("email") or f"{sub}@firebase.user")
        username = str(payload.get("name") or email.split("@")[0]).replace(" ", "_")
        # Ensure username uniqueness by appending suffix if necessary
        base_username = username[:48]  # leave room for suffix
        stmt_uname = select(User).where(User.username == base_username)
        conflict = (await db.execute(stmt_uname)).scalar_one_or_none()
        if conflict:
            base_username = f"{base_username}_{str(user_uuid)[:8]}"

        user = User(
            id=user_uuid,
            email=email,
            username=base_username,
            hashed_password="",  # Firebase users have no local password
            role="USER",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(
            "Auto-provisioned Firebase user: %s (%s)", user.username, user_uuid
        )
    else:
        # Update last_login_at on each successful Firebase auth
        user.last_login_at = datetime.now(UTC)
        await db.commit()

    token, expires_in = create_access_token(
        subject=user.id,
        role=user.role,
        settings=settings,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        role=UserRole(user.role),
        user_id=user.id,
    )
