"""Token budget observability and daily usage endpoints.

Provides per-user daily quota visibility, per-analysis token cost breakdown,
and administrative budget status. All routes enforce owner isolation.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_async_session, get_current_user
from app.models.user import User
from app.modules.token_budget import (
    UserDailyBudgetTracker,
    UserDailyUsageResponse,
)
from app.modules.token_budget.models import TokenUsageRecordSchema
from app.repositories.token_usage import TokenUsageRepository

logger = logging.getLogger("verifai.api.token_budget")
router = APIRouter(prefix="/token-budget", tags=["Token Budget & Cost"])


# ---------------------------------------------------------------------------
# Daily usage summary
# ---------------------------------------------------------------------------


@router.get(
    "/daily",
    summary="Get my daily token usage",
    response_model=UserDailyUsageResponse,
)
async def get_my_daily_usage(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UserDailyUsageResponse:
    """Return the authenticated user's daily token quota and remaining allowance.

    The budget window resets at midnight UTC. Values are maintained in an
    in-process tracker and are authoritative for the current process instance.
    """
    tracker = UserDailyBudgetTracker.get_instance()
    return await tracker.get_user_daily_usage(
        user_id=str(current_user.id),
        daily_token_limit=settings.USER_DAILY_TOKEN_LIMIT,
        daily_analyses_limit=settings.USER_DAILY_ANALYSIS_LIMIT,
    )


# ---------------------------------------------------------------------------
# Per-verification token history
# ---------------------------------------------------------------------------


@router.get(
    "/history",
    summary="Get my token usage history",
    response_model=list[TokenUsageRecordSchema],
)
async def get_my_token_history(
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[TokenUsageRecordSchema]:
    """Return paginated token usage records for the authenticated user (most-recent first)."""
    repo = TokenUsageRepository(session=db)
    records = await repo.get_by_owner_id(
        owner_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )
    return [
        TokenUsageRecordSchema(
            id=r.id,
            operation=r.operation,
            provider=r.provider,
            model_name=r.model_name,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            total_tokens=r.total_tokens,
            is_estimated=r.is_estimated,
            retry_count=r.retry_count,
            estimated_cost_usd=r.estimated_cost_usd,
            timestamp=r.created_at,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# Per-verification breakdown (owner-isolated)
# ---------------------------------------------------------------------------


@router.get(
    "/verification/{verification_id}",
    summary="Get token usage for a specific verification job",
    response_model=list[TokenUsageRecordSchema],
)
async def get_verification_token_usage(
    verification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[TokenUsageRecordSchema]:
    """Return all token usage records for a specific verification job.

    Owner isolation is enforced: only records belonging to the calling user
    are returned even if the verification_id exists in the database.
    """
    repo = TokenUsageRepository(session=db)
    all_records = await repo.get_by_verification_id(verification_id)

    owner_str = str(current_user.id)
    owned = [r for r in all_records if r.owner_id == owner_str]

    return [
        TokenUsageRecordSchema(
            id=r.id,
            operation=r.operation,
            provider=r.provider,
            model_name=r.model_name,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            total_tokens=r.total_tokens,
            is_estimated=r.is_estimated,
            retry_count=r.retry_count,
            estimated_cost_usd=r.estimated_cost_usd,
            timestamp=r.created_at,
        )
        for r in owned
    ]
