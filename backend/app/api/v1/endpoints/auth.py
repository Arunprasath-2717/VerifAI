"""Authentication and user management endpoints."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user, get_optional_db_session
from app.core.errors import ConflictError, UnauthorizedError
from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    _EPHEMERAL_USERS,
    _EPHEMERAL_USERS_BY_EMAIL,
    _EPHEMERAL_USERS_BY_USERNAME,
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
        "privilege escalation."
    ),
)
async def register(
    request_data: UserRegisterRequest,
    http_request: Request,
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    """Register a new user account."""
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

    # Check for duplicate user
    if db is not None:
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
    else:
        if email_clean in _EPHEMERAL_USERS_BY_EMAIL:
            raise ConflictError(
                message="Email is already registered.",
                details={"field": "email"},
            )
        if username_clean in _EPHEMERAL_USERS_BY_USERNAME:
            raise ConflictError(
                message="Username is already registered.",
                details={"field": "username"},
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

    if db is not None:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    else:
        _EPHEMERAL_USERS[user_id] = new_user
        _EPHEMERAL_USERS_BY_EMAIL[email_clean] = user_id
        _EPHEMERAL_USERS_BY_USERNAME[username_clean] = user_id

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
    summary="Authenticate User and Obtain JWT Token",
    description=(
        "Authenticates credentials and returns a signed HS256 JWT access token."
    ),
)
async def login(
    login_data: UserLoginRequest,
    http_request: Request,
    db: AsyncSession | None = Depends(get_optional_db_session),
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
    user: User | None = None

    if db is not None:
        stmt = select(User).where(
            or_(
                User.email == identifier.lower(),
                User.username == identifier,
            )
        )
        user = (await db.execute(stmt)).scalar_one_or_none()
    else:
        user_id = _EPHEMERAL_USERS_BY_EMAIL.get(identifier.lower())
        if not user_id:
            user_id = _EPHEMERAL_USERS_BY_USERNAME.get(identifier)
        if user_id:
            user = _EPHEMERAL_USERS.get(user_id)

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
    summary="Authenticate via Firebase Auth",
    description=(
        "Validates a Google/Firebase ID token, synchronizes the user account, "
        "and returns a VerifAI session token."
    ),
)
async def authenticate_with_firebase(
    request: FirebaseAuthRequest,
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate or synchronize user via Firebase Auth ID token."""
    payload = verify_firebase_id_token(request.id_token, settings=settings)
    sub = str(payload.get("sub"))
    user_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{sub}")

    user: User | None = None
    if db is not None:
        stmt = select(User).where(User.id == user_uuid)
        user = (await db.execute(stmt)).scalar_one_or_none()
    else:
        user = _EPHEMERAL_USERS.get(user_uuid)

    if user is None:
        email = str(payload.get("email") or f"{sub}@firebase.user")
        username = str(payload.get("name") or email.split("@")[0]).replace(" ", "_")
        user = User(
            id=user_uuid,
            email=email,
            username=username,
            hashed_password="",
            role="USER",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        if db is not None:
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            _EPHEMERAL_USERS[user_uuid] = user

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
