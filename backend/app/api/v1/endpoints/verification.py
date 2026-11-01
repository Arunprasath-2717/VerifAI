"""Verification pipeline endpoints with owner isolation, rate limiting, and RBAC.

Architecture: Database is required for all verification operations.
There is no in-memory ephemeral fallback in production.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.dependencies import get_async_session, get_optional_current_user
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.rate_limit import enforce_rate_limit, track_verification_concurrency
from app.models.user import User
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


def _job_to_response(job: VerificationJob) -> VerificationResponse:
    """Reconstruct full verification response envelope from database entity."""
    claims_out: list[ClaimResultSchema] = []
    for c in job.claims or []:
        evidence_out = [
            EvidenceSchema(
                id=ev.id,
                source_url=ev.source_url,
                source_title=ev.source_title,
                publisher=ev.publisher,
                publication_date=ev.publication_date,
                snippet=ev.snippet,
                retriever_name=ev.retriever_name,
                evidence_source=getattr(ev, "evidence_source", "EXTERNAL"),
                document_id=getattr(ev, "document_id", None),
                chunk_id=getattr(ev, "chunk_id", None),
                chunk_index=getattr(ev, "chunk_index", None),
                document_title=getattr(ev, "document_title", None),
                relevance_score=ev.relevance_score,
                authority_score=ev.authority_score,
            )
            for ev in (c.evidence_items or [])
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
            for je in (c.judge_evaluations or [])
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
        for ar in (job.audit_records or [])
    ]

    return VerificationResponse(
        verification_id=job.id,
        owner_id=job.owner_id,
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


def _is_anonymous_dev(settings: Settings) -> bool:
    """True only where anonymous callers are allowed (development/test)."""
    return settings.is_development


def resolve_verification_owner(
    current_user: User | None,
    client_owner_id: str | None,
    settings: Settings,
) -> str:
    """Determine effective owner_id for verification execution."""
    if current_user is not None:
        user_id_str = str(current_user.id)
        if current_user.role == "ADMIN":
            if client_owner_id and client_owner_id.strip():
                return client_owner_id.strip()
            return user_id_str

        if (
            client_owner_id
            and client_owner_id.strip()
            and client_owner_id.strip() != user_id_str
        ):
            raise ForbiddenError(
                message="Cannot run verifications on behalf of another user namespace.",
                details={
                    "user_id": user_id_str,
                    "requested_owner_id": client_owner_id,
                },
            )
        return user_id_str

    if not _is_anonymous_dev(settings):
        raise UnauthorizedError(
            message="Authentication required to run verifications in production.",
            details={"environment": settings.ENVIRONMENT},
        )

    if client_owner_id and client_owner_id.strip():
        return client_owner_id.strip()
    return settings.DEFAULT_OWNER_ID


@router.post(
    "/verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Claim Verification Pipeline",
    description=(
        "Decomposes input text into atomic claims, retrieves verified evidence, "
        "runs independent judges with disagreement analysis, and returns an "
        "auditable verification envelope. Results are persisted to PostgreSQL."
    ),
)
async def create_verification(
    request: VerificationCreateRequest,
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> VerificationResponse:
    """Execute end-to-end verification pipeline. Results are persisted to DB."""
    effective_owner = resolve_verification_owner(
        current_user=current_user,
        client_owner_id=request.options.owner_id,
        settings=settings,
    )
    request.options.owner_id = effective_owner

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="verification",
            limit=settings.RATE_LIMIT_VERIFY_PER_MINUTE,
            user_id=effective_owner,
            settings=settings,
        )

    # Track maximum concurrent jobs per user/owner
    async with track_verification_concurrency(
        owner_id=effective_owner,
        max_concurrent=settings.MAX_CONCURRENT_VERIFICATIONS_PER_USER,
        settings=settings,
    ):
        orchestrator = VerificationOrchestrator()
        response = await orchestrator.verify(request=request, db_session=db)

    return response


@router.get(
    "/verification/{verification_id}",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Verification Result",
    description=(
        "Fetches a completed verification job and its claims, evidence, "
        "and audit trail from PostgreSQL. Enforces ownership authorization."
    ),
)
async def get_verification(
    verification_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> VerificationResponse:
    """Retrieve an existing verification job by UUID from the database."""
    # Anonymous reads are allowed only where anonymous writes are (development/test).
    # In production every read must carry a Bearer token and pass the owner check.
    if current_user is None and not _is_anonymous_dev(settings):
        raise UnauthorizedError(
            message="Authentication required to read verification results.",
            details={"scheme": "Bearer"},
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

    # Enforce ownership authorization. Anonymous dev callers may read any job
    # in the dev namespace; authenticated non-admins may read only their own.
    if current_user is None:
        if job.owner_id != settings.DEFAULT_OWNER_ID:
            raise ForbiddenError(
                message="Access denied: You do not own this verification job.",
                details={"verification_id": str(verification_id)},
            )
    elif current_user.role != "ADMIN":
        if job.owner_id != str(current_user.id):
            raise ForbiddenError(
                message="Access denied: You do not own this verification job.",
                details={"verification_id": str(verification_id)},
            )

    return _job_to_response(job)


@router.get(
    "/verifications",
    response_model=list[VerificationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Verification History",
    description=(
        "Lists verification jobs for current user or all jobs for administrators. "
        "Results are ordered by creation date (newest first)."
    ),
)
async def list_verifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> list[VerificationResponse]:
    """List historical verification jobs from the database."""
    effective_owner = resolve_verification_owner(
        current_user=current_user,
        client_owner_id=None,
        settings=settings,
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
        .order_by(VerificationJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if current_user is None or current_user.role != "ADMIN":
        stmt = stmt.where(VerificationJob.owner_id == effective_owner)

    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [_job_to_response(j) for j in jobs]
