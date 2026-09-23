"""Payload ingestion endpoints for browser extension and client integrations."""

import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session
from app.core.errors import BadRequestError, NotFoundError
from app.models.ingestion import IngestedPayload
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


async def get_optional_db_session(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession | None, None]:
    """Provide an async database session if configured, or None for ephemeral runs."""
    if not settings.DATABASE_URL:
        yield None
        return

    try:
        async for session in _get_async_session():
            yield session
    except Exception as exc:
        logger.warning(
            "Could not establish database session: %s. Proceeding ephemerally.",
            type(exc).__name__,
        )
        yield None


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest AI-Generated Response Payload",
    description=(
        "Receives captured AI-generated text from the Chrome extension or other "
        "clients, validates provenance and source URL, optionally executes "
        "synchronous verification, and returns structured ingestion status."
    ),
)
async def ingest_payload(
    request: IngestionPayloadRequest,
    db: AsyncSession | None = Depends(get_optional_db_session),
) -> IngestionResponse:
    """Ingest AI response text and optionally execute verification."""
    ingestion_id = uuid.uuid4()
    now_utc = datetime.now(UTC)

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
            error_message = f"Verification failed: {type(exc).__name__} - {exc}"

    # Step 2: Persist ingestion record if database is available
    if db is not None:
        try:
            payload_record = IngestedPayload(
                id=ingestion_id,
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
                exc,
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
    description="Fetches an ingested payload record and status by UUID.",
)
async def get_ingested_payload(
    ingestion_id: uuid.UUID,
    db: AsyncSession | None = Depends(get_optional_db_session),
) -> IngestionResponse:
    """Retrieve an ingested payload record by UUID."""
    if db is None:
        raise NotFoundError(
            message=f"Ingested payload {ingestion_id} not found.",
            details={"ingestion_id": str(ingestion_id)},
        )

    stmt = select(IngestedPayload).where(IngestedPayload.id == ingestion_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        raise NotFoundError(
            message=f"Ingested payload {ingestion_id} not found.",
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
