"""Dashboard statistics and aggregated metrics API endpoint."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.verification import _job_to_response
from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_async_session,
    get_optional_current_user,
    resolve_effective_owner,
)
from app.models.chat import Conversation
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.models.verification import (
    ExtractedClaim,
    RetrievedEvidence,
    VerificationJob,
)
from app.schemas.dashboard import (
    ChartPointSchema,
    DashboardLeaderboardEntry,
    DashboardStatsResponse,
    StatCardMetric,
)

logger = logging.getLogger("verifai.api.dashboard")
router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get Consolidated Dashboard Statistics",
    description=(
        "Calculates verification counts, claims, evidence, "
        "timeseries curves, and recent jobs."
    ),
)
async def get_dashboard_stats(
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> DashboardStatsResponse:
    """Aggregate real database statistics for the authenticated caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    now = datetime.now(UTC)

    # 1. Total Verifications
    verif_count_stmt = select(func.count(VerificationJob.id)).where(
        VerificationJob.owner_id == effective_owner
    )
    verif_count = (await db.execute(verif_count_stmt)).scalar_one() or 0

    # 2. Total Claims
    claims_count_stmt = (
        select(func.count(ExtractedClaim.id))
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(VerificationJob.owner_id == effective_owner)
    )
    claims_count = (await db.execute(claims_count_stmt)).scalar_one() or 0

    # 3. Total Evidence Sources (Evidence items + Private KB Docs)
    evidence_count_stmt = (
        select(func.count(RetrievedEvidence.id))
        .join(ExtractedClaim, RetrievedEvidence.claim_id == ExtractedClaim.id)
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(VerificationJob.owner_id == effective_owner)
    )
    retrieved_ev_count = (await db.execute(evidence_count_stmt)).scalar_one() or 0

    kb_doc_count_stmt = select(func.count(KnowledgeDocument.id)).where(
        KnowledgeDocument.owner_id == effective_owner
    )
    kb_doc_count = (await db.execute(kb_doc_count_stmt)).scalar_one() or 0
    total_evidence_sources = retrieved_ev_count + kb_doc_count

    # 4. Total Conversations
    conv_count_stmt = select(func.count(Conversation.id)).where(
        Conversation.owner_id == effective_owner
    )
    conv_count = (await db.execute(conv_count_stmt)).scalar_one() or 0

    # 5. Timeseries: group in SQL once per source instead of three queries
    # per calendar day (previously 111 count queries per dashboard request).
    # Both charts are derived from the same 30-day window in UTC.
    first_day = (now - timedelta(days=29)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_day = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # PostgreSQL timestamptz-to-date otherwise uses the DB session's timezone.
    # SQLite does not expose timezone(), so the simpler date() is used there.
    bind_getter = getattr(db, "get_bind", None)
    bind = bind_getter() if callable(bind_getter) else None
    postgres = getattr(getattr(bind, "dialect", None), "name", "") == "postgresql"

    def utc_date(column: Any) -> Any:
        timestamp = func.timezone("UTC", column) if postgres else column
        return func.date(timestamp)

    job_day = utc_date(VerificationJob.created_at)
    claim_day = utc_date(ExtractedClaim.created_at)
    evidence_day = utc_date(RetrievedEvidence.created_at)
    conversation_day = utc_date(Conversation.created_at)

    async def grouped_daily_counts(query: Any) -> dict[str, int]:
        rows = (await db.execute(query)).all()
        return {
            day.isoformat() if hasattr(day, "isoformat") else str(day): int(count)
            for day, count in rows
            if day is not None
        }

    jobs_by_day = await grouped_daily_counts(
        select(job_day, func.count(VerificationJob.id))
        .where(
            VerificationJob.owner_id == effective_owner,
            VerificationJob.created_at >= first_day,
            VerificationJob.created_at < end_day,
        )
        .group_by(job_day)
    )
    claims_by_day = await grouped_daily_counts(
        select(claim_day, func.count(ExtractedClaim.id))
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(
            VerificationJob.owner_id == effective_owner,
            ExtractedClaim.created_at >= first_day,
            ExtractedClaim.created_at < end_day,
        )
        .group_by(claim_day)
    )
    evidence_by_day = await grouped_daily_counts(
        select(evidence_day, func.count(RetrievedEvidence.id))
        .join(ExtractedClaim, RetrievedEvidence.claim_id == ExtractedClaim.id)
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(
            VerificationJob.owner_id == effective_owner,
            RetrievedEvidence.created_at >= first_day,
            RetrievedEvidence.created_at < end_day,
        )
        .group_by(evidence_day)
    )
    conversations_by_day = await grouped_daily_counts(
        select(conversation_day, func.count(Conversation.id))
        .where(
            Conversation.owner_id == effective_owner,
            Conversation.created_at >= first_day,
            Conversation.created_at < end_day,
        )
        .group_by(conversation_day)
    )

    monthly_points: list[ChartPointSchema] = []
    for offset in range(30):
        day = first_day + timedelta(days=offset)
        day_key = day.date().isoformat()
        monthly_points.append(
            ChartPointSchema(
                day=day.strftime("%b %d"),
                date=day_key,
                verifications=jobs_by_day.get(day_key, 0),
                claims=claims_by_day.get(day_key, 0),
                evidence=evidence_by_day.get(day_key, 0),
            )
        )
    weekly_points = [
        point.model_copy(
            update={"day": datetime.fromisoformat(point.date).strftime("%a")}
        )
        for point in monthly_points[-7:]
    ]
    weekly_conversations = [
        conversations_by_day.get(point.date, 0) for point in weekly_points
    ]

    # 6. Recent Verifications (Latest 5)
    recent_jobs_stmt = (
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
        .where(VerificationJob.owner_id == effective_owner)
        .order_by(desc(VerificationJob.created_at))
        .limit(5)
    )
    recent_jobs = (await db.execute(recent_jobs_stmt)).scalars().all()
    recent_verifications = [_job_to_response(j) for j in recent_jobs]

    # 7. Dynamic Stat Cards
    stat_cards = [
        StatCardMetric(
            title="Verifications",
            value=str(verif_count),
            trend="N/A",
            sub="Executed audits",
            sparkline=[p.verifications for p in weekly_points],
        ),
        StatCardMetric(
            title="Claims Analyzed",
            value=str(claims_count),
            trend="N/A",
            sub="Atomic propositions",
            sparkline=[p.claims for p in weekly_points] if weekly_points else [0],
        ),
        StatCardMetric(
            title="Evidence Sources",
            value=str(total_evidence_sources),
            trend="N/A",
            sub="Vault & web corpus",
            sparkline=[p.evidence for p in weekly_points] if weekly_points else [0],
        ),
        StatCardMetric(
            title="Conversations",
            value=str(conv_count),
            trend="N/A",
            sub="Multi-model threads",
            sparkline=weekly_conversations,
        ),
    ]

    # No benchmark aggregates are calculated here; never publish fabricated rankings.
    leaderboard_preview: list[DashboardLeaderboardEntry] = []

    return DashboardStatsResponse(
        verifications_count=verif_count,
        claims_count=claims_count,
        evidence_sources_count=total_evidence_sources,
        conversations_count=conv_count,
        weekly_chart_data=weekly_points,
        monthly_chart_data=monthly_points,
        recent_verifications=recent_verifications,
        stat_cards=stat_cards,
        leaderboard_preview=leaderboard_preview,
    )
