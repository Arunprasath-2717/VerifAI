"""Reports, analytics, and empirical benchmarking endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_async_session,
    get_optional_current_user,
    resolve_effective_owner,
)
from app.models.chat import LLMRun
from app.models.user import User
from app.models.verification import (
    ExtractedClaim,
    RetrievedEvidence,
    VerificationJob,
)
from app.schemas.dashboard import ChartPointSchema
from app.schemas.reports import (
    EvidenceSourceDomainItem,
    ModelUsageItem,
    ReportsAnalyticsResponse,
)

logger = logging.getLogger("verifai.api.reports")
router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get(
    "/analytics",
    response_model=ReportsAnalyticsResponse,
    summary="Get Verification and Model Analytics",
    description=(
        "Aggregates model usage, evidence sources, and historical "
        "verification activity."
    ),
)
async def get_reports_analytics(
    timeframe: str = Query(default="30D", description="Timeframe: 7D, 30D, 90D, 1Y"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ReportsAnalyticsResponse:
    """Compute empirical reports analytics for caller."""
    effective_owner = resolve_effective_owner(current_user, None, settings)
    now = datetime.now(UTC)

    days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}
    num_days = days_map.get(timeframe.upper().strip(), 30)
    # Include today and the preceding N-1 complete UTC calendar days.
    start_date = (now - timedelta(days=num_days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 1. Aggregate in SQL. Avoid materializing every VerificationJob (and
    # evidence timestamp) over a potentially year-long reporting period.
    totals_stmt = select(
        func.count(VerificationJob.id),
        func.coalesce(func.sum(VerificationJob.total_claims), 0),
        func.coalesce(func.sum(VerificationJob.supported_claims), 0),
        func.coalesce(func.sum(VerificationJob.contradicted_claims), 0),
        func.coalesce(func.sum(VerificationJob.unknown_claims), 0),
        func.coalesce(
            func.sum(func.coalesce(VerificationJob.trust_score, 0.0)), 0.0
        ),
    ).where(
        VerificationJob.owner_id == effective_owner,
        VerificationJob.created_at >= start_date,
        VerificationJob.created_at < end_date,
    )
    (
        total_verifs,
        total_claims,
        total_supported,
        total_contradicted,
        total_unknown,
        summed_trust,
    ) = (await db.execute(totals_stmt)).one()

    avg_trust = round(summed_trust / total_verifs, 2) if total_verifs else 0.0
    supported_pct = (
        round(total_supported / total_claims * 100, 1) if total_claims else 0.0
    )
    contradicted_pct = (
        round(total_contradicted / total_claims * 100, 1) if total_claims else 0.0
    )
    unknown_pct = round(total_unknown / total_claims * 100, 1) if total_claims else 0.0

    # 2. Fetch daily GROUP BY aggregates (at most 365 rows per series).
    # For PostgreSQL, explicitly convert timestamptz to UTC before date().
    bind_getter = getattr(db, "get_bind", None)
    bind = bind_getter() if callable(bind_getter) else None
    postgres = getattr(getattr(bind, "dialect", None), "name", "") == "postgresql"

    def utc_date(column):
        timestamp = func.timezone("UTC", column) if postgres else column
        return func.date(timestamp)

    job_date = utc_date(VerificationJob.created_at)
    job_daily_stmt = (
        select(
            job_date,
            func.count(VerificationJob.id),
            func.coalesce(func.sum(VerificationJob.total_claims), 0),
        )
        .where(
            VerificationJob.owner_id == effective_owner,
            VerificationJob.created_at >= start_date,
            VerificationJob.created_at < end_date,
        )
        .group_by(job_date)
    )
    job_daily_rows = (await db.execute(job_daily_stmt)).all()
    jobs_by_day = {
        day.isoformat() if hasattr(day, "isoformat") else str(day):
            (int(count), int(claims))
        for day, count, claims in job_daily_rows
        if day is not None
    }

    evidence_date = utc_date(RetrievedEvidence.created_at)
    evidence_daily_stmt = (
        select(evidence_date, func.count(RetrievedEvidence.id))
        .join(ExtractedClaim, RetrievedEvidence.claim_id == ExtractedClaim.id)
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(
            VerificationJob.owner_id == effective_owner,
            RetrievedEvidence.created_at >= start_date,
            RetrievedEvidence.created_at < end_date,
        )
        .group_by(evidence_date)
    )
    evidence_daily_rows = (await db.execute(evidence_daily_stmt)).all()
    evidence_by_day = {
        day.isoformat() if hasattr(day, "isoformat") else str(day): int(count)
        for day, count in evidence_daily_rows
        if day is not None
    }

    chart_points: list[ChartPointSchema] = []
    step_days = 1 if num_days <= 30 else (3 if num_days <= 90 else 14)
    current_cursor = start_date
    while current_cursor < end_date:
        next_cursor = min(current_cursor + timedelta(days=step_days), end_date)
        verifications = 0
        claims = 0
        evidence = 0
        day_cursor = current_cursor
        while day_cursor < next_cursor:
            day_key = day_cursor.date().isoformat()
            day_verifs, day_claims = jobs_by_day.get(day_key, (0, 0))
            verifications += day_verifs
            claims += day_claims
            evidence += evidence_by_day.get(day_key, 0)
            day_cursor += timedelta(days=1)
        day_label = (
            current_cursor.strftime("%a")
            if num_days <= 7
            else current_cursor.strftime("%b %d")
        )
        chart_points.append(
            ChartPointSchema(
                day=day_label,
                date=current_cursor.strftime("%Y-%m-%d"),
                verifications=verifications,
                claims=claims,
                evidence=evidence,
            )
        )
        current_cursor = next_cursor

    # 3. Model Usage Breakdown: completed inference only, not failed probes.
    # Previous versions counted invalid/failed attempted routes as productive use.
    model_usage_stmt = (
        select(LLMRun.model_name, func.count(LLMRun.id))
        .where(
            LLMRun.owner_id == effective_owner,
            LLMRun.started_at >= start_date,
            LLMRun.started_at < end_date,
            LLMRun.status == "COMPLETED",
        )
        .group_by(LLMRun.model_name)
        .order_by(desc(func.count(LLMRun.id)))
        .limit(6)
    )
    model_usage_rows = (await db.execute(model_usage_stmt)).all()
    model_usage: list[ModelUsageItem] = []
    for m_name, count in model_usage_rows:
        model_usage.append(ModelUsageItem(model=m_name, usage=count))

    # 4. Evidence Sources Breakdown
    evidence_stmt = (
        select(RetrievedEvidence.publisher, func.count(RetrievedEvidence.id))
        .join(ExtractedClaim, RetrievedEvidence.claim_id == ExtractedClaim.id)
        .join(VerificationJob, ExtractedClaim.verification_id == VerificationJob.id)
        .where(
            VerificationJob.owner_id == effective_owner,
            VerificationJob.created_at >= start_date,
            VerificationJob.created_at < end_date,
            RetrievedEvidence.created_at >= start_date,
            RetrievedEvidence.created_at < end_date,
        )
        .group_by(RetrievedEvidence.publisher)
        .order_by(desc(func.count(RetrievedEvidence.id)))
        .limit(6)
    )
    evidence_rows = (await db.execute(evidence_stmt)).all()
    evidence_sources: list[EvidenceSourceDomainItem] = []
    for pub, count in evidence_rows:
        if pub and pub.strip():
            evidence_sources.append(
                EvidenceSourceDomainItem(domain=pub.strip(), count=count)
            )

    return ReportsAnalyticsResponse(
        timeframe=timeframe,
        chart_data=chart_points,
        model_usage=model_usage,
        evidence_sources=evidence_sources,
        total_verifications=total_verifs,
        total_claims=total_claims,
        average_trust_score=avg_trust,
        supported_rate=supported_pct,
        contradicted_rate=contradicted_pct,
        unknown_rate=unknown_pct,
    )
