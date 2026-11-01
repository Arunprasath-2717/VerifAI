"""Payload ingestion endpoints for browser extension and client integrations."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_async_session,
    get_current_user,
    resolve_effective_owner,
)
from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.models.ingestion import IngestedPayload
from app.models.user import User
from app.modules.evidence.security import is_safe_url
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.ingestion import (
    IngestionPayloadRequest,
    IngestionResponse,
    IngestionSource,
    IngestionStatus,
)
from app.schemas.verification import (
    VerificationCreateRequest,
    VerificationResponse,
)

logger = logging.getLogger("verifai.api.ingestion")
router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest AI-Generated Response Payload",
    description=(
        "Receives captured AI-generated text from the Chrome extension or other "
        "clients. Requires a Bearer JWT. The record and any verification are owned "
        "by the authenticated user, validates provenance and source URL, optionally "
        "executes synchronous verification, and returns structured ingestion status."
    ),
)
async def ingest_payload(
    request: IngestionPayloadRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> IngestionResponse:
    """Ingest AI response text and optionally execute verification."""
    ingestion_id = uuid.uuid4()
    now_utc = datetime.now(UTC)
    owner_id = str(current_user.id)

    # A caller may only verify inside its own namespace. Admin may target another
    # namespace; non-admin mismatches are rejected (IDOR protection).
    verification_owner = resolve_effective_owner(
        current_user=current_user,
        client_owner_id=request.options.owner_id,
        settings=settings,
    )
    request.options.owner_id = verification_owner

    if request.verify_immediately and settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="verification",
            limit=settings.RATE_LIMIT_VERIFY_PER_MINUTE,
            user_id=owner_id,
            settings=settings,
        )

    # Validate source URL against SSRF / malicious destination if provided
    if request.source_url:
        if not is_safe_url(request.source_url):
            raise BadRequestError(
                message="Invalid or unsafe source_url (blocked by SSRF policy).",
                details={"source_url": request.source_url},
            )

    verification_resp: VerificationResponse | None = None
    verification_id: uuid.UUID | None = None
    ingestion_status = (
        IngestionStatus.VERIFIED
        if request.verify_immediately
        else IngestionStatus.RECEIVED
    )
    error_message: str | None = None

    # Step 1: Execute verification if requested
    if request.verify_immediately:
        try:
            ver_req = VerificationCreateRequest(
                text=request.text,
                query=request.prompt,
                options=request.options,
            )
            orchestrator = VerificationOrchestrator()
            verification_resp = await orchestrator.verify(
                request=ver_req,
                db_session=db,
            )
            verification_id = verification_resp.verification_id
        except Exception as exc:
            logger.error("Verification execution failed during ingestion: %s", exc)
            ingestion_status = IngestionStatus.FAILED
            error_message = f"Verification failed: {type(exc).__name__}"

    # Step 2: Persist ingestion record to database
    try:
        payload_record = IngestedPayload(
            id=ingestion_id,
            owner_id=owner_id,
            source=request.source.value,
            source_url=request.source_url,
            model_name=request.model_name,
            prompt=request.prompt,
            captured_text=request.text,
            session_id=request.session_id,
            client_version=request.client_version,
            capture_metadata=request.capture_metadata,
            status=ingestion_status.value,
            verification_id=verification_id,
            error_message=error_message,
        )
        db.add(payload_record)
        await db.commit()
    except Exception as exc:
        logger.warning(
            "Failed to persist ingested payload record: %s. Rolling back.",
            type(exc).__name__,
        )
        await db.rollback()

    return IngestionResponse(
        ingestion_id=ingestion_id,
        source=request.source,
        status=ingestion_status,
        created_at=now_utc,
        model_name=request.model_name,
        source_url=request.source_url,
        verification_id=verification_id,
        verification=verification_resp,
        error_message=error_message,
    )


@router.get(
    "/ingest/{ingestion_id}",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Ingestion Record",
    description=(
        "Fetches an ingested payload record by UUID. Requires a Bearer JWT. "
        "Callers may read only records they own; legacy ownerless records are "
        "visible to ADMIN accounts only."
    ),
)
async def get_ingested_payload(
    ingestion_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> IngestionResponse:
    """Retrieve an ingested payload record by UUID."""
    stmt = select(IngestedPayload).where(IngestedPayload.id == ingestion_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        raise NotFoundError(
            message=f"Ingested payload {ingestion_id} not found.",
            details={"ingestion_id": str(ingestion_id)},
        )

    is_admin = current_user.role == "ADMIN"
    if not is_admin and record.owner_id != str(current_user.id):
        # Quarantined (NULL owner) and other users' records are both denied.
        raise ForbiddenError(
            message="Access denied: You do not own this ingested payload.",
            details={"ingestion_id": str(ingestion_id)},
        )

    return IngestionResponse(
        ingestion_id=record.id,
        source=IngestionSource(record.source),
        status=IngestionStatus(record.status),
        created_at=record.created_at,
        model_name=record.model_name,
        source_url=record.source_url,
        verification_id=record.verification_id,
        verification=None,  # Linked job retrievable via /api/v1/verification/{id}
        error_message=record.error_message,
    )
