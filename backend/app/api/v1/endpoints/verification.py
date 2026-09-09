"""Verification API endpoints for Phase 2B / 2C.

Phase 2B surface:
    POST   /api/v1/verification          — submit a claim for verification
    GET    /api/v1/verification/{id}     — retrieve a verification record
    GET    /api/v1/verification/{id}/status — get current lifecycle status

Phase 2C addition:
    POST   /api/v1/verification/{id}/process — trigger lifecycle processing

All endpoints require Bearer authentication via get_current_user.
Ownership is enforced through the service layer; a verification belonging
to another user is treated identically to a non-existent record (404) to
prevent resource-existence leakage.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.repositories.verification_repository import (
    VerificationRepository,
    verification_repository,
)
from app.schemas.auth import UserResponse
from app.schemas.common import StandardResponse
from app.schemas.verification import (
    CreateVerificationRequest,
    VerificationResponse,
    VerificationStatus,
)
from app.services.verification_service import VerificationService, verification_service
from app.services.verification_processing_service import (
    InvalidStatusTransitionError,
    VerificationNotFoundError,
    VerificationProcessingService,
    verification_processing_service,
)

logger = logging.getLogger("verifai.api.verification")

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper — build VerificationResponse from a raw repository dict
# ---------------------------------------------------------------------------


def _to_response(record: dict) -> VerificationResponse:
    """Construct a ``VerificationResponse`` from a raw repository record dict."""
    return VerificationResponse(
        id=record["id"],
        user_id=record["user_id"],
        claim=record["claim"],
        status=VerificationStatus(record["status"]),
        verdict=record.get("verdict"),
        trust_score=record.get("trust_score"),
        evidence=record.get("evidence"),
        error_message=record.get("error_message"),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


# ---------------------------------------------------------------------------
# POST /api/v1/verification
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=StandardResponse[VerificationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a claim for verification",
    description=(
        "Accepts an AI-generated claim and persists it as a new verification "
        "request. The record starts in ``pending`` state. "
        "The authenticated user is automatically set as the owner; "
        "ownership may never be supplied by the client."
    ),
)
async def create_verification(
    payload: CreateVerificationRequest,
    current_user: UserResponse = Depends(get_current_user),
    svc: VerificationService = Depends(lambda: verification_service),
) -> StandardResponse[VerificationResponse]:
    """Create a new verification record owned by the authenticated user."""
    try:
        record = await svc.submit_verification(
            user_id=current_user.id,
            claim=payload.claim,
        )
    except Exception as exc:
        logger.error(
            "Database error creating verification for user %s: %s",
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to persist verification request",
                "details": {},
            },
        ) from exc

    return StandardResponse(success=True, data=_to_response(record))


# ---------------------------------------------------------------------------
# GET /api/v1/verification/{verification_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{verification_id}",
    response_model=StandardResponse[VerificationResponse],
    summary="Retrieve a verification record",
    description=(
        "Returns the full verification record for the given ID. "
        "The record must belong to the authenticated user. "
        "Records belonging to other users are treated as non-existent."
    ),
)
async def get_verification(
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    svc: VerificationService = Depends(lambda: verification_service),
) -> StandardResponse[VerificationResponse]:
    """Return the verification record if it belongs to the current user."""
    try:
        record = await svc.get_own_verification(
            verification_id=verification_id,
            user_id=current_user.id,
        )
    except Exception as exc:
        logger.error(
            "Database error fetching verification %s for user %s: %s",
            verification_id,
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to retrieve verification record",
                "details": {},
            },
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "VERIFICATION_NOT_FOUND",
                "message": "Verification not found",
                "details": {},
            },
        )

    return StandardResponse(success=True, data=_to_response(record))


# ---------------------------------------------------------------------------
# GET /api/v1/verification/{verification_id}/status
# ---------------------------------------------------------------------------


@router.get(
    "/{verification_id}/status",
    response_model=StandardResponse[VerificationResponse],
    summary="Get verification lifecycle status",
    description=(
        "Returns the current status and key fields of a verification record. "
        "Clients can poll this endpoint to determine whether processing is "
        "pending, processing, completed, or failed. "
        "The record must belong to the authenticated user."
    ),
)
async def get_verification_status(
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    svc: VerificationService = Depends(lambda: verification_service),
) -> StandardResponse[VerificationResponse]:
    """Return the full record (including current status) for the given verification."""
    try:
        record = await svc.get_own_verification(
            verification_id=verification_id,
            user_id=current_user.id,
        )
    except Exception as exc:
        logger.error(
            "Database error fetching status for verification %s, user %s: %s",
            verification_id,
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to retrieve verification status",
                "details": {},
            },
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "VERIFICATION_NOT_FOUND",
                "message": "Verification not found",
                "details": {},
            },
        )

    return StandardResponse(success=True, data=_to_response(record))


# ---------------------------------------------------------------------------
# POST /api/v1/verification/{verification_id}/process
# ---------------------------------------------------------------------------


@router.post(
    "/{verification_id}/process",
    response_model=StandardResponse[VerificationResponse],
    summary="Trigger verification processing",
    description=(
        "Starts processing for a verification that is in ``pending`` state. "
        "Transitions the record through pending → processing → completed (or failed). "
        "Only the authenticated owner may trigger processing. "
        "Records belonging to other users are treated as non-existent. "
        "Only records in ``pending`` state may be processed."
    ),
)
async def process_verification(
    verification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    svc: VerificationProcessingService = Depends(
        lambda: verification_processing_service
    ),
) -> StandardResponse[VerificationResponse]:
    """Orchestrate the full pending → processing → completed/failed lifecycle."""
    try:
        record = await svc.process_verification(
            verification_id=verification_id,
            user_id=current_user.id,
        )
    except VerificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "VERIFICATION_NOT_FOUND",
                "message": "Verification not found",
                "details": {},
            },
        )
    except InvalidStatusTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "INVALID_STATUS_TRANSITION",
                "message": "Verification is not in pending state and cannot be processed",
                "details": {},
            },
        )
    except Exception as exc:
        logger.error(
            "Database error during processing of verification %s for user %s: %s",
            verification_id,
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to process verification",
                "details": {},
            },
        ) from exc

    return StandardResponse(success=True, data=_to_response(record))
