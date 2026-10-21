"""Verification pipeline endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import Principal, enforce_rate_limit, get_principal, resolve_owner
from app.core.config import Settings, get_settings
from app.core.dependencies import get_optional_db_session
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


# Bounded ephemeral in-memory cache for development/demo when DATABASE_URL is not set
_EPHEMERAL_MAX_ENTRIES = 100
# Maps job ID -> (owner ID, response) so lookups stay namespace-scoped.
_EPHEMERAL_JOBS: dict[uuid.UUID, tuple[str, VerificationResponse]] = {}


def _persistence_failed(response: VerificationResponse) -> bool:
    return any(
        a.stage == "PERSISTENCE" and a.event_type == "DEGRADED_EXECUTION"
        for a in response.audit_trail
    )


def _cached_job(
    verification_id: uuid.UUID, principal: Principal
) -> VerificationResponse | None:
    cached = _EPHEMERAL_JOBS.get(verification_id)
    if cached is None:
        return None
    job_owner, cached_response = cached
    if principal.authenticated and job_owner != principal.owner_id:
        return None
    return cached_response


def _not_found(verification_id: uuid.UUID) -> NotFoundError:
    return NotFoundError(
        message=f"Verification job {verification_id} not found.",
        details={"verification_id": str(verification_id)},
    )


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
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(enforce_rate_limit),
) -> VerificationResponse:
    """Execute end-to-end verification pipeline."""
    owner = resolve_owner(principal, request.options.owner_id, settings)
    request = request.model_copy(
        update={"options": request.options.model_copy(update={"owner_id": owner})}
    )
    orchestrator = VerificationOrchestrator()
    response = await orchestrator.verify(request=request, db_session=db)
    if db is None or _persistence_failed(response):
        if len(_EPHEMERAL_JOBS) >= _EPHEMERAL_MAX_ENTRIES:
            oldest_key = next(iter(_EPHEMERAL_JOBS))
            _EPHEMERAL_JOBS.pop(oldest_key, None)
        _EPHEMERAL_JOBS[response.verification_id] = (owner, response)
    return response


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
    principal: Principal = Depends(get_principal),
) -> VerificationResponse:
    """Retrieve an existing verification job by UUID within the caller's namespace.

    Jobs owned by another namespace are reported as not found so that their
    existence is not disclosed.
    """
    if db is None:
        cached = _cached_job(verification_id, principal)
        if cached is not None:
            return cached
        raise _not_found(verification_id)

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
    if principal.authenticated:
        stmt = stmt.where(VerificationJob.owner_id == principal.owner_id)

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if job is None:
        # Jobs whose database save failed are still served from the process cache.
        cached = _cached_job(verification_id, principal)
        if cached is not None:
            return cached
        raise _not_found(verification_id)

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
