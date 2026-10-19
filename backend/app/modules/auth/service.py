"""Authentication application service coordinating identity resolution and tokens."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings, get_settings
from app.core.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_firebase_id_token,
    verify_password,
)
from app.models.user import User
from app.models.user_consent import UserConsent
from app.repositories.user import UserRepository
from app.repositories.user_consent import UserConsentRepository
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
        consent_repository: UserConsentRepository | None = None,
    ) -> None:
        self.user_repo = user_repository
        self.settings = settings or get_settings()
        self.token_verifier = token_verifier or verify_firebase_id_token
        self.consent_repo = consent_repository or UserConsentRepository(
            user_repository.session
        )

    async def register_user(
        self,
        request: UserRegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserResponse:
        """Register a new user account with Argon2id hashing and mandatory consent."""
        if not getattr(request, "terms_accepted", False):
            raise BadRequestError(
                message="You must read and agree to the Terms & Conditions "
                "and Privacy Policy.",
                details={"field": "terms_accepted"},
            )

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

        # Persist mandatory legal consent audit record
        try:
            await self.consent_repo.record_consent(
                user_id=created_user.id,
                terms_version=self.settings.TERMS_VERSION,
                privacy_version=self.settings.PRIVACY_POLICY_VERSION,
                action_source="signup_form",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as exc:
            logger.error(
                "Failed to persist user consent for user %s: %s", created_user.id, exc
            )
            # Remove created user to prevent orphaned account without recorded consent
            try:
                await self.user_repo.session.delete(created_user)
                await self.user_repo.session.commit()
            except Exception:
                pass
            raise AppError(
                message="Failed to persist mandatory legal consent. "
                "Registration aborted.",
                code="CONSENT_PERSISTENCE_FAILED",
                status_code=500,
                details={"reason": "consent_persistence_failed"},
            ) from exc

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

    async def authenticate_firebase(
        self,
        id_token: str,
        display_name: str | None = None,
        terms_accepted: bool | None = None,
        is_signup: bool = False,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[TokenResponse, User]:
        """Verify Firebase RS256 token, resolve identity, and issue session token.

        Consent is enforced on the server before any account is provisioned:
        - A new account must be created with ``terms_accepted=True``.
        - An existing account whose latest consent does not match the current
          terms/privacy versions must re-accept (``terms_accepted=True``), or the
          request is rejected with ``TERMS_REACCEPTANCE_REQUIRED``.
        """
        # 1. Cryptographic RS256 validation against Google JWKS
        payload = self.token_verifier(id_token, settings=self.settings)

        firebase_uid = payload["sub"]
        email = payload.get("email")
        resolved_name = payload.get("name") or display_name

        # 2. Consent gate, evaluated before any row is written
        existing = await self.user_repo.get_by_id(
            uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{firebase_uid}")
        )
        if existing is None:
            if terms_accepted is not True:
                raise BadRequestError(
                    message="You must read and agree to the Terms & Conditions "
                    "and Privacy Policy.",
                    details={"field": "terms_accepted"},
                )
        else:
            current = await self.consent_repo.has_consented_to_current(
                existing.id,
                self.settings.TERMS_VERSION,
                self.settings.PRIVACY_POLICY_VERSION,
            )
            if not current and terms_accepted is not True:
                raise ForbiddenError(
                    message="Accept the updated Terms & Conditions to continue.",
                    details={
                        "reason": "TERMS_REACCEPTANCE_REQUIRED",
                        "terms_version": self.settings.TERMS_VERSION,
                        "privacy_version": self.settings.PRIVACY_POLICY_VERSION,
                    },
                )

        # 3. Identity resolution and auto-provisioning
        user, is_new = await self.user_repo.get_or_create_firebase_user(
            firebase_uid=firebase_uid,
            email=email,
            display_name=resolved_name,
        )

        if not user.is_active:
            raise UnauthorizedError(
                message="User account is deactivated.",
                details={"reason": "account_deactivated"},
            )

        # 4. Persist consent for new accounts and re-acceptance
        if is_new:
            try:
                provider_id = payload.get("firebase", {}).get("sign_in_provider", "")
                action_source = (
                    "google_sso" if "google" in provider_id else "signup_form"
                )
                await self.consent_repo.record_consent(
                    user_id=user.id,
                    terms_version=self.settings.TERMS_VERSION,
                    privacy_version=self.settings.PRIVACY_POLICY_VERSION,
                    action_source=action_source,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as exc:
                logger.error(
                    "Failed to persist consent for Firebase user %s: %s", user.id, exc
                )
                try:
                    await self.user_repo.session.delete(user)
                    await self.user_repo.session.commit()
                except Exception:
                    pass
                raise AppError(
                    message="Failed to record legal consent for new account.",
                    code="CONSENT_PERSISTENCE_FAILED",
                    status_code=500,
                    details={"reason": "consent_persistence_failed"},
                ) from exc
        elif terms_accepted is True:
            # Recorded only when the stored consent is not current; a repeat
            # login with an up-to-date record must not add duplicate rows.
            current = await self.consent_repo.has_consented_to_current(
                user.id,
                self.settings.TERMS_VERSION,
                self.settings.PRIVACY_POLICY_VERSION,
            )
            if not current:
                try:
                    await self.consent_repo.record_consent(
                        user_id=user.id,
                        terms_version=self.settings.TERMS_VERSION,
                        privacy_version=self.settings.PRIVACY_POLICY_VERSION,
                        action_source="reacceptance",
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                except Exception as exc:
                    # Consent is required here, so a failed write must fail the login.
                    logger.error("Consent re-acceptance recording failed: %s", exc)
                    raise AppError(
                        message="Failed to record legal consent. Please try again.",
                        code="CONSENT_PERSISTENCE_FAILED",
                        status_code=500,
                        details={"reason": "consent_persistence_failed"},
                    ) from exc

        # 4. Mint internal session token
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

    async def record_user_consent(
        self,
        user_id: uuid.UUID,
        terms_version: str,
        privacy_version: str,
        action_source: str = "reacceptance",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserConsent:
        """Record explicit consent acceptance for an authenticated user."""
        return await self.consent_repo.record_consent(
            user_id=user_id,
            terms_version=terms_version,
            privacy_version=privacy_version,
            action_source=action_source,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_user_consents(self, user_id: uuid.UUID) -> list[UserConsent]:
        """Retrieve user consent records strictly isolated to the specified user."""
        return await self.consent_repo.get_by_user_id(user_id)
