"""Verification pipeline endpoints."""

import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.database import get_async_session as _get_async_session
from app.core.errors import NotFoundError
from app.models.verification import (
    ExtractedClaim,
    VerificationJob,
)
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    AuditRecordSchema,
    ClaimResultSchema,
    ContentType,
    EvidenceSchema,
    JudgeEvaluationSchema,
    UnknownReason,
    VerdictType,
    VerificationCreateRequest,
    VerificationResponse,
)

logger = logging.getLogger("verifai.api.verification")
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
    "/verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Claim Verification Pipeline",
    description=(
        "Decomposes input text into atomic claims, retrieves verified evidence, "
        "runs independent judges with disagreement analysis, and returns an "
        "auditable verification envelope."
    ),
)
async def create_verification(
    request: VerificationCreateRequest,
    db: AsyncSession | None = Depends(get_optional_db_session),
) -> VerificationResponse:
    """Execute end-to-end verification pipeline."""
    orchestrator = VerificationOrchestrator()
    return await orchestrator.verify(request=request, db_session=db)


@router.get(
    "/verification/{verification_id}",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Verification Result",
    description=(
        "Fetches a completed verification job and its claims, evidence, "
        "and audit trail."
    ),
)
async def get_verification(
    verification_id: uuid.UUID,
    db: AsyncSession | None = Depends(get_optional_db_session),
) -> VerificationResponse:
    """Retrieve an existing verification job by UUID."""
    if db is None:
        raise NotFoundError(
            message=f"Verification job {verification_id} not found.",
            details={"verification_id": str(verification_id)},
        )

    stmt = (
        select(VerificationJob)
        .options(
            selectinload(VerificationJob.claims).selectinload(
                ExtractedClaim.evidence_items
            ),
            selectinload(VerificationJob.claims).selectinload(
                ExtractedClaim.judge_evaluations
            ),
            selectinload(VerificationJob.audit_records),
        )
        .where(VerificationJob.id == verification_id)
    )

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if job is None:
        raise NotFoundError(
            message=f"Verification job {verification_id} not found.",
            details={"verification_id": str(verification_id)},
        )

    # Reconstruct response envelope from database entity
    claims_out: list[ClaimResultSchema] = []
    for c in job.claims:
        evidence_out = [
            EvidenceSchema(
                id=ev.id,
                source_url=ev.source_url,
                source_title=ev.source_title,
                publisher=ev.publisher,
                publication_date=ev.publication_date,
                snippet=ev.snippet,
                retriever_name=ev.retriever_name,
                relevance_score=ev.relevance_score,
                authority_score=ev.authority_score,
            )
            for ev in c.evidence_items
        ]
        judges_out = [
            JudgeEvaluationSchema(
                id=je.id,
                judge_name=je.judge_name,
                judgment=je.judgment,
                confidence=je.confidence,
                rationale=je.rationale,
                evidence_references=je.evidence_references,
            )
            for je in c.judge_evaluations
        ]
        claims_out.append(
            ClaimResultSchema(
                id=c.id,
                claim_index=c.claim_index,
                claim_text=c.claim_text,
                start_offset=c.start_offset,
                end_offset=c.end_offset,
                content_type=ContentType(c.content_type)
                if c.content_type is not None
                else ContentType.FACTUAL,
                verdict=VerdictType(c.verdict) if c.verdict is not None else None,
                is_verifiable=c.is_verifiable,
                confidence=c.confidence,
                is_calibrated=c.is_calibrated,
                calibration_status=c.calibration_status,
                unknown_reason=UnknownReason(c.unknown_reason)
                if c.unknown_reason is not None
                else None,
                explanation=c.explanation,
                degraded_evaluation=c.degraded_evaluation,
                arbitration_reason=c.arbitration_reason,
                evidence=evidence_out,
                judges=judges_out,
            )
        )

    audit_out = [
        AuditRecordSchema(
            id=ar.id,
            stage=ar.stage,
            event_type=ar.event_type,
            status=ar.status,
            message=ar.message,
            timestamp=ar.timestamp,
        )
        for ar in job.audit_records
    ]

    return VerificationResponse(
        verification_id=job.id,
        status=job.status,
        input_text=job.input_text,
        query=job.query,
        content_type=job.content_type,
        total_claims=job.total_claims,
        supported_claims=job.supported_claims,
        contradicted_claims=job.contradicted_claims,
        unknown_claims=job.unknown_claims,
        non_factual_claims=job.non_factual_claims,
        trust_score=job.trust_score,
        calibrated_confidence=job.calibrated_confidence,
        is_calibrated=job.is_calibrated,
        calibration_status=job.calibration_status,
        degraded_evaluation=job.degraded_evaluation,
        summary=job.summary,
        created_at=job.created_at,
        completed_at=job.completed_at,
        claims=claims_out,
        audit_trail=audit_out,
    )
