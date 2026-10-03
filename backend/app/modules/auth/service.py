"""Authentication application service coordinating identity resolution and tokens."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings, get_settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    hash_password,
    verify_firebase_id_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserRole,
)

logger = logging.getLogger("verifai.auth.service")


class AuthenticationService:
    """Orchestrates user registration, local authentication, and Firebase federation."""

    def __init__(
        self,
        user_repository: UserRepository,
        settings: Settings | None = None,
        token_verifier: Any = None,
    ) -> None:
        self.user_repo = user_repository
        self.settings = settings or get_settings()
        self.token_verifier = token_verifier or verify_firebase_id_token

    async def register_user(self, request: UserRegisterRequest) -> UserResponse:
        """Register a new user account with Argon2id password hashing."""
        email_clean = request.email.strip().lower()
        username_clean = request.username.strip()

        existing = await self.user_repo.get_by_email_or_username(
            email=email_clean, username=username_clean
        )
        if existing:
            field = "Email" if existing.email == email_clean else "Username"
            raise ConflictError(
                message=f"{field} is already registered.",
                details={"field": field.lower()},
            )

        hashed = hash_password(request.password)
        now = datetime.now(UTC)

        new_user = User(
            id=uuid.uuid4(),
            email=email_clean,
            username=username_clean,
            hashed_password=hashed,
            role=UserRole.USER.value,
            is_active=True,
            is_verified=False,
        )
        new_user.created_at = now
        new_user.updated_at = now

        created_user = await self.user_repo.create(new_user)
        logger.info("Registered user %s (email=%s)", created_user.id, email_clean)

        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            username=created_user.username,
            role=UserRole(created_user.role),
            is_active=created_user.is_active,
            created_at=created_user.created_at,
        )

    async def authenticate_local(self, request: UserLoginRequest) -> TokenResponse:
        """Authenticate using local credentials and issue a signed session token."""
        identifier = request.email_or_username.strip()

        # Check by email first, then by username
        user = await self.user_repo.get_by_email(identifier)
        if not user:
            user = await self.user_repo.get_by_username(identifier)

        if not user or not user.is_active:
            raise UnauthorizedError(
                message="Invalid email/username or password.",
                details={"reason": "invalid_credentials"},
            )

        if not verify_password(request.password, user.hashed_password):
            raise UnauthorizedError(
                message="Invalid email/username or password.",
                details={"reason": "invalid_credentials"},
            )

        token, expires_in = create_access_token(
            subject=user.id,
            role=user.role,
            settings=self.settings,
        )

        logger.info("User %s logged in successfully via local credentials", user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            role=UserRole(user.role),
            user_id=user.id,
        )

    async def authenticate_firebase(self, id_token: str) -> tuple[TokenResponse, User]:
        """Verify Firebase RS256 token, resolve identity, and issue session token."""
        # 1. Cryptographic RS256 validation against Google JWKS
        payload = self.token_verifier(id_token, settings=self.settings)

        firebase_uid = payload["sub"]
        email = payload.get("email")
        display_name = payload.get("name")

        # 2. Identity resolution and auto-provisioning
        user, is_new = await self.user_repo.get_or_create_firebase_user(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
        )

        if not user.is_active:
            raise UnauthorizedError(
                message="User account is deactivated.",
                details={"reason": "account_deactivated"},
            )

        # 3. Mint internal session token
        token, expires_in = create_access_token(
            subject=user.id,
            role=user.role,
            settings=self.settings,
        )

        logger.info(
            "Firebase auth successful: internal_user_id=%s, firebase_uid=%s, new=%s",
            user.id,
            firebase_uid,
            is_new,
        )

        response = TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            role=UserRole(user.role),
            user_id=user.id,
        )
        return response, user
