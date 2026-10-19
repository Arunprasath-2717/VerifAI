"""Repository for persistent token usage records and analytics."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_usage import TokenUsage
from app.modules.token_budget.models import TokenUsageRecord


class TokenUsageRepository:
    """Handles database persistence and queries for TokenUsage records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_record(
        self,
        record: TokenUsageRecord,
        owner_id: str,
        verification_id: uuid.UUID | None = None,
    ) -> TokenUsage:
        """Persist a single token usage record."""
        usage_entity = TokenUsage(
            id=record.id,
            verification_id=verification_id,
            owner_id=owner_id,
            operation=record.operation,
            provider=record.provider,
            model_name=record.model_name,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            total_tokens=record.total_tokens,
            is_estimated=record.is_estimated,
            retry_count=record.retry_count,
            estimated_cost_usd=record.estimated_cost_usd,
        )
        self.session.add(usage_entity)
        await self.session.flush()
        return usage_entity

    async def save_records(
        self,
        records: list[TokenUsageRecord],
        owner_id: str,
        verification_id: uuid.UUID | None = None,
    ) -> list[TokenUsage]:
        """Persist a batch of token usage records within the current transaction."""
        entities: list[TokenUsage] = []
        for r in records:
            e = TokenUsage(
                id=r.id,
                verification_id=verification_id,
                owner_id=owner_id,
                operation=r.operation,
                provider=r.provider,
                model_name=r.model_name,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                total_tokens=r.total_tokens,
                is_estimated=r.is_estimated,
                retry_count=r.retry_count,
                estimated_cost_usd=r.estimated_cost_usd,
            )
            self.session.add(e)
            entities.append(e)
        if entities:
            await self.session.flush()
        return entities

    async def get_by_verification_id(
        self, verification_id: uuid.UUID
    ) -> list[TokenUsage]:
        """Retrieve token usages for a specific verification job."""
        stmt = (
            select(TokenUsage)
            .where(TokenUsage.verification_id == verification_id)
            .order_by(TokenUsage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_owner_id(
        self,
        owner_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TokenUsage]:
        """Retrieve historical token usages for a specific owner."""
        stmt = (
            select(TokenUsage)
            .where(TokenUsage.owner_id == owner_id)
            .order_by(desc(TokenUsage.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_owner_daily_tokens(
        self,
        owner_id: str,
        target_date: datetime | None = None,
    ) -> int:
        """Compute total tokens spent by an owner on a given UTC date."""
        target = target_date or datetime.now(UTC)
        start_of_day = datetime(
            target.year, target.month, target.day, 0, 0, 0, tzinfo=UTC
        )
        stmt = select(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).where(
            TokenUsage.owner_id == owner_id,
            TokenUsage.created_at >= start_of_day,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
