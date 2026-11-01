"""Legal compliance, policy versions, and user consent audit endpoints."""

import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_async_session, get_current_user
from app.models.user import User
from app.repositories.user_consent import UserConsentRepository
from app.schemas.legal import (
    ConsentCreateRequest,
    LegalVersionsResponse,
    UserConsentResponse,
)

logger = logging.getLogger("verifai.api.legal")
router = APIRouter()


@router.get(
    "/legal/versions",
    response_model=LegalVersionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Active Legal Document Versions",
    description=(
        "Returns current authoritative versions, effective dates, and contact "
        "details for Terms & Privacy Policy."
    ),
)
async def get_legal_versions(
    settings: Settings = Depends(get_settings),
) -> LegalVersionsResponse:
    """Retrieve active versions and effective dates for legal policies."""
    return LegalVersionsResponse(
        terms_version=settings.TERMS_VERSION,
        privacy_version=settings.PRIVACY_POLICY_VERSION,
        terms_effective_date=settings.TERMS_EFFECTIVE_DATE,
        privacy_effective_date=settings.PRIVACY_EFFECTIVE_DATE,
        legal_contact_email=settings.LEGAL_CONTACT_EMAIL,
        governing_law=settings.GOVERNING_LAW,
        minimum_age_requirement=settings.MINIMUM_AGE_REQUIREMENT,
    )


@router.get(
    "/legal/consent",
    response_model=list[UserConsentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User's Consent History",
    description=(
        "Returns all historical consent audit records for the authenticated user, "
        "strictly isolated to their user ID."
    ),
)
async def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[UserConsentResponse]:
    """Retrieve consent history for the authenticated user."""
    repo = UserConsentRepository(db)
    consents = await repo.get_by_user_id(current_user.id)
    return [
        UserConsentResponse(
            id=c.id,
            user_id=c.user_id,
            terms_version=c.terms_version,
            privacy_version=c.privacy_version,
            consented_at=c.consented_at,
            action_source=c.action_source,
        )
        for c in consents
    ]


@router.post(
    "/legal/consent",
    response_model=UserConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record or Re-accept Legal Terms Consent",
    description=(
        "Allows an authenticated user to record acceptance of updated Terms & "
        "Conditions and Privacy Policy."
    ),
)
async def record_user_consent(
    payload: ConsentCreateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> UserConsentResponse:
    """Record consent acceptance for the authenticated user."""
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    repo = UserConsentRepository(db)
    consent = await repo.record_consent(
        user_id=current_user.id,
        terms_version=payload.terms_version,
        privacy_version=payload.privacy_version,
        action_source=payload.action_source,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return UserConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        terms_version=consent.terms_version,
        privacy_version=consent.privacy_version,
        consented_at=consent.consented_at,
        action_source=consent.action_source,
    )
