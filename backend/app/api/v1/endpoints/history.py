"""History, search/filtering, and user data lifecycle API endpoints."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.verification import _EPHEMERAL_JOBS, _job_to_response
from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_optional_current_user,
    get_optional_db_session,
    resolve_effective_owner,
)
from app.core.errors import ForbiddenError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.models.chat import Conversation
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.models.verification import AuditRecord, VerificationJob
from app.modules.chat.service import (
    _EPHEMERAL_CONVERSATIONS,
    _EPHEMERAL_MESSAGES,
)
from app.modules.knowledge.service import _EPHEMERAL_DOCS, clear_ephemeral_kb
from app.schemas.chat import (
    AuditHistoryItem,
    AuditHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    UserDeleteDataResponse,
)
from app.schemas.verification import (
    VerificationListResponse,
    VerificationResponse,
)

logger = logging.getLogger("verifai.api.history")

router = APIRouter(prefix="/history", tags=["History & User Lifecycle"])


@router.get(
    "/verifications",
    response_model=VerificationListResponse,
    summary="List and filter verification history",
)
async def list_verification_history(
    verdict: str | None = Query(
        default=None, description="Filter by verdict: SUPPORTED, CONTRADICTED, UNKNOWN"
    ),
    job_status: str | None = Query(
        default=None, description="Filter by job status: PENDING, COMPLETED, FAILED"
    ),
    start_date: datetime | None = Query(
        default=None, description="Filter jobs created after this UTC date"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter jobs created before this UTC date"
    ),
    search: str | None = Query(
        default=None, description="Search keyword in input text"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> VerificationListResponse:
    """Retrieve filtered, paginated verification history owned by caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if db is not None:
        query = select(VerificationJob).where(
            VerificationJob.owner_id == effective_owner
        )
        if verdict:
            from app.models.verification import ExtractedClaim

            query = query.where(
                VerificationJob.claims.any(
                    ExtractedClaim.verdict == verdict.upper().strip()
                )
            )
        if job_status:
            query = query.where(VerificationJob.status == job_status.upper().strip())
        if start_date:
            query = query.where(VerificationJob.created_at >= start_date)
        if end_date:
            query = query.where(VerificationJob.created_at <= end_date)
        if search:
            query = query.where(VerificationJob.input_text.ilike(f"%{search.strip()}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        query = (
            query.options(
                selectinload(VerificationJob.claims),
                selectinload(VerificationJob.audit_records),
            )
            .order_by(desc(VerificationJob.created_at))
            .limit(limit)
            .offset(offset)
        )
        jobs = (await db.execute(query)).scalars().all()

        items = [_job_to_response(j) for j in jobs]
        return VerificationListResponse(
            total=total, limit=limit, offset=offset, items=items
        )
    else:
        from app.api.v1.endpoints.verification import _EPHEMERAL_JOBS

        user_jobs = [
            j
            for j in _EPHEMERAL_JOBS.values()
            if getattr(j, "owner_id", None) == effective_owner
        ]

        if verdict:
            v_clean = verdict.upper().strip()
            user_jobs = [
                j
                for j in user_jobs
                if getattr(j, "overall_verdict", None) == v_clean
                or (
                    hasattr(j, "overall_verdict")
                    and getattr(j.overall_verdict, "value", None) == v_clean
                )
            ]
        if job_status:
            s_clean = job_status.upper().strip()
            user_jobs = [
                j
                for j in user_jobs
                if getattr(j, "status", None) == s_clean
                or (
                    hasattr(j, "status") and getattr(j.status, "value", None) == s_clean
                )
            ]
        if search:
            s_low = search.strip().lower()
            user_jobs = [
                j
                for j in user_jobs
                if hasattr(j, "input_text")
                and s_low in getattr(j, "input_text", "").lower()
            ]

        user_jobs.sort(
            key=lambda x: getattr(x, "created_at", datetime.min) or datetime.min,
            reverse=True,
        )
        total = len(user_jobs)
        items = user_jobs[offset : offset + limit]

        return VerificationListResponse(
            total=total, limit=limit, offset=offset, items=items
        )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List and filter conversation history",
)
async def list_conversation_history(
    search: str | None = Query(
        default=None, description="Search term in conversation title"
    ),
    start_date: datetime | None = Query(
        default=None, description="Filter created after UTC date"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter created before UTC date"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> ConversationListResponse:
    """Retrieve filtered conversation history owned by caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if db is not None:
        query = select(Conversation).where(Conversation.owner_id == effective_owner)
        if search:
            query = query.where(Conversation.title.ilike(f"%{search.strip()}%"))
        if start_date:
            query = query.where(Conversation.created_at >= start_date)
        if end_date:
            query = query.where(Conversation.created_at <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        query = (
            query.options(selectinload(Conversation.messages))
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        rows = (await db.execute(query)).scalars().all()

        items = [
            ConversationResponse(
                id=c.id,
                owner_id=c.owner_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(c.messages) if c.messages else 0,
            )
            for c in rows
        ]
        return ConversationListResponse(
            total=total, limit=limit, offset=offset, items=items
        )
    else:
        user_convs = list(_EPHEMERAL_CONVERSATIONS.get(effective_owner, {}).values())
        if search:
            s_low = search.strip().lower()
            user_convs = [c for c in user_convs if s_low in c.title.lower()]
        if start_date:
            user_convs = [c for c in user_convs if c.created_at >= start_date]
        if end_date:
            user_convs = [c for c in user_convs if c.created_at <= end_date]

        user_convs.sort(key=lambda c: c.updated_at, reverse=True)
        total = len(user_convs)
        items = [
            ConversationResponse(
                id=c.id,
                owner_id=c.owner_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(_EPHEMERAL_MESSAGES.get(c.id, [])),
            )
            for c in user_convs[offset : offset + limit]
        ]
        return ConversationListResponse(
            total=total, limit=limit, offset=offset, items=items
        )


@router.get(
    "/audit",
    response_model=AuditHistoryResponse,
    summary="List verification audit trail records",
)
async def list_audit_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> AuditHistoryResponse:
    """Retrieve audit events linked to the caller's verifications."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if db is not None:
        query = (
            select(AuditRecord)
            .join(VerificationJob, AuditRecord.verification_id == VerificationJob.id)
            .where(VerificationJob.owner_id == effective_owner)
            .order_by(desc(AuditRecord.timestamp))
            .limit(limit)
            .offset(offset)
        )
        count_query = (
            select(func.count(AuditRecord.id))
            .join(VerificationJob, AuditRecord.verification_id == VerificationJob.id)
            .where(VerificationJob.owner_id == effective_owner)
        )
        total = (await db.execute(count_query)).scalar_one()
        records = (await db.execute(query)).scalars().all()

        items = [
            AuditHistoryItem(
                id=r.id,
                verification_id=r.verification_id,
                stage=r.stage,
                event_type=r.event_type,
                status=r.status,
                message=r.message,
                details=r.details,
                timestamp=r.timestamp,
            )
            for r in records
        ]
        return AuditHistoryResponse(
            total=total, limit=limit, offset=offset, items=items
        )
    else:
        # In-memory audit retrieval
        from app.api.v1.endpoints.verification import _EPHEMERAL_JOBS

        user_job_ids = {
            j.verification_id
            for j in _EPHEMERAL_JOBS.values()
            if getattr(j, "owner_id", None) == effective_owner
        }
        # Build synthetic audit items from job logs
        audit_items: list[AuditHistoryItem] = []
        for jid in user_job_ids:
            job = _EPHEMERAL_JOBS[jid]
            audit_items.append(
                AuditHistoryItem(
                    id=uuid.uuid4(),
                    verification_id=uuid.UUID(str(jid)),
                    stage="ORCHESTRATION",
                    event_type="VERIFICATION_COMPLETED",
                    status="SUCCESS",
                    message="Verification job completed successfully.",
                    details={"total_claims": getattr(job, "total_claims", 0)},
                    timestamp=getattr(job, "created_at", datetime.now(UTC))
                    or datetime.now(UTC),
                )
            )

        total = len(audit_items)
        return AuditHistoryResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=audit_items[offset : offset + limit],
        )


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationResponse,
    summary="Get single verification from history",
)
async def get_history_verification(
    verification_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> VerificationResponse:
    """Retrieve details of a single verification job owned by caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    if db is not None:
        job = (
            await db.execute(
                select(VerificationJob)
                .where(VerificationJob.id == verification_id)
                .options(
                    selectinload(VerificationJob.claims),
                    selectinload(VerificationJob.audit_records),
                )
            )
        ).scalar_one_or_none()
        if not job:
            raise NotFoundError(
                message=f"Verification job '{verification_id}' not found.",
                details={"verification_id": str(verification_id)},
            )
        if job.owner_id != effective_owner:
            raise ForbiddenError(
                message="Access denied: Cannot access another user's verification job.",
                details={"verification_id": str(verification_id)},
            )
        return _job_to_response(job)
    else:
        if verification_id not in _EPHEMERAL_JOBS:
            raise NotFoundError(
                message=f"Verification job '{verification_id}' not found.",
                details={"verification_id": str(verification_id)},
            )
        job_item = _EPHEMERAL_JOBS[verification_id]
        if getattr(job_item, "owner_id", None) != effective_owner:
            raise ForbiddenError(
                message="Access denied: Cannot access another user's verification job.",
                details={"verification_id": str(verification_id)},
            )
        return job_item


@router.delete(
    "/verifications/{verification_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a single verification job",
)
async def delete_verification_record(
    verification_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Delete a single verification job owned by caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if db is not None:
        job_entity = (
            await db.execute(
                select(VerificationJob).where(VerificationJob.id == verification_id)
            )
        ).scalar_one_or_none()
        if not job_entity:
            raise NotFoundError(
                message=f"Verification job '{verification_id}' not found.",
                details={"verification_id": str(verification_id)},
            )
        if job_entity.owner_id != effective_owner:
            raise ForbiddenError(
                message="Access denied: Cannot delete another user's verification job.",
                details={"verification_id": str(verification_id)},
            )
        await db.delete(job_entity)
        await db.commit()
        return {"deleted": True, "verification_id": str(verification_id)}
    else:
        if verification_id not in _EPHEMERAL_JOBS:
            raise NotFoundError(
                message=f"Verification job '{verification_id}' not found.",
                details={"verification_id": str(verification_id)},
            )
        job_item = _EPHEMERAL_JOBS[verification_id]
        if getattr(job_item, "owner_id", None) != effective_owner:
            raise ForbiddenError(
                message="Access denied: Cannot delete another user's verification job.",
                details={"verification_id": str(verification_id)},
            )
        _EPHEMERAL_JOBS.pop(verification_id, None)
        return {"deleted": True, "verification_id": str(verification_id)}


@router.delete(
    "/purge",
    response_model=UserDeleteDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Purge all user-owned data (GDPR / Data Lifecycle)",
)
async def purge_all_user_data(
    http_request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession | None = Depends(get_optional_db_session),
    settings: Settings = Depends(get_settings),
) -> UserDeleteDataResponse:
    """Cascade purge all conversations, verifications, and KB documents for caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)

    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="purge_data",
            limit=3,
            user_id=effective_owner,
            settings=settings,
        )

    del_convs = 0
    del_verifs = 0
    del_docs = 0

    if db is not None:
        # 1. Delete conversations (cascades to messages and llm_runs)
        conv_res = await db.execute(
            delete(Conversation).where(Conversation.owner_id == effective_owner)
        )
        del_convs = int(getattr(conv_res, "rowcount", 0) or 0)

        # 2. Delete verifications (cascades to claims, evidence, judge verdicts, audit)
        v_res = await db.execute(
            delete(VerificationJob).where(VerificationJob.owner_id == effective_owner)
        )
        del_verifs = int(getattr(v_res, "rowcount", 0) or 0)

        # 3. Delete knowledge documents (cascades to chunks)
        kb_res = await db.execute(
            delete(KnowledgeDocument).where(
                KnowledgeDocument.owner_id == effective_owner
            )
        )
        del_docs = int(getattr(kb_res, "rowcount", 0) or 0)

        await db.commit()
    else:
        # In-memory purge
        del_convs = len(_EPHEMERAL_CONVERSATIONS.pop(effective_owner, {}))
        # Purge verifications
        from app.api.v1.endpoints.verification import _EPHEMERAL_JOBS

        to_remove_v = [
            k
            for k, v in _EPHEMERAL_JOBS.items()
            if getattr(v, "owner_id", None) == effective_owner
        ]
        for k in to_remove_v:
            _EPHEMERAL_JOBS.pop(k, None)
        del_verifs = len(to_remove_v)

        # Purge KB docs
        del_docs = len(_EPHEMERAL_DOCS.get(effective_owner, {}))
        clear_ephemeral_kb(owner_id=effective_owner)

    logger.info(
        "User '%s' purged data: %d convs, %d verifs, %d docs",
        effective_owner,
        del_convs,
        del_verifs,
        del_docs,
    )

    return UserDeleteDataResponse(
        success=True,
        deleted_conversations=del_convs,
        deleted_verifications=del_verifs,
        deleted_documents=del_docs,
        message=(
            f"Purged {del_convs} conversations, {del_verifs} verifications, "
            f"and {del_docs} documents."
        ),
    )
