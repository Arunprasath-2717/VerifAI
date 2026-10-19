"""Thread-safe and concurrency-safe token budget manager for an analysis job."""

import asyncio
import logging
import uuid

from app.core.config import Settings, get_settings
from app.modules.token_budget.estimator import TokenEstimator
from app.modules.token_budget.models import (
    AnalysisBudgetStatus,
    BudgetExhaustedError,
    TokenUsageRecord,
    TokenUsageRecordSchema,
)

logger = logging.getLogger("verifai.token_budget")


class AnalysisBudgetManager:
    """Manages token accounting and budget enforcement for a single analysis execution.

    Features:
    - Thread-safe and asyncio concurrency-safe reservations and usage recording.
    - Tracks actual vs estimated usage without double counting.
    - Stops LLM work immediately when the remaining budget is insufficient.
    - Calculates estimated costs using configured pricing models.
    """

    def __init__(
        self,
        analysis_id: uuid.UUID,
        owner_id: str,
        budget_limit: int = 20000,
        settings: Settings | None = None,
    ) -> None:
        self.analysis_id = analysis_id
        self.owner_id = owner_id
        self.budget_limit = budget_limit
        self.settings = settings or get_settings()

        self._lock = asyncio.Lock()
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_tokens_spent: int = 0
        self._total_cost_usd: float = 0.0
        self._total_retries: int = 0
        self._active_reservations: dict[str, int] = {}
        self._records: list[TokenUsageRecord] = []
        self._is_exhausted: bool = False
        self._any_estimated: bool = False

    @property
    def remaining_tokens(self) -> int:
        """Available budget considering both spent tokens and active reservations."""
        committed = self._total_tokens_spent + sum(self._active_reservations.values())
        return max(0, self.budget_limit - committed)

    @property
    def spent_tokens(self) -> int:
        return self._total_tokens_spent

    @property
    def is_exhausted(self) -> bool:
        return self._is_exhausted or self.remaining_tokens <= 0

    async def can_spend(self, estimated_tokens: int) -> bool:
        """Check whether the remaining budget can accommodate the estimated tokens."""
        async with self._lock:
            if self._is_exhausted:
                return False
            available = self.budget_limit - (
                self._total_tokens_spent + sum(self._active_reservations.values())
            )
            return available >= estimated_tokens

    async def reserve(self, estimated_tokens: int) -> str:
        """Reserve token budget before dispatching an LLM call (prevents races)."""
        async with self._lock:
            available = self.budget_limit - (
                self._total_tokens_spent + sum(self._active_reservations.values())
            )
            if available < estimated_tokens:
                self._is_exhausted = True
                raise BudgetExhaustedError(
                    message=(
                        f"Cannot reserve {estimated_tokens} tokens for analysis "
                        f"{self.analysis_id}. Available budget: {available}."
                    ),
                    details={
                        "analysis_id": str(self.analysis_id),
                        "requested_tokens": estimated_tokens,
                        "available_tokens": available,
                        "budget_limit": self.budget_limit,
                    },
                )

            reservation_id = str(uuid.uuid4())
            self._active_reservations[reservation_id] = estimated_tokens
            logger.debug(
                "Reserved %d tokens (reservation_id=%s). Remaining unreserved: %d",
                estimated_tokens,
                reservation_id,
                available - estimated_tokens,
            )
            return reservation_id

    async def release_reservation(self, reservation_id: str) -> None:
        """Safely release an unused token reservation."""
        async with self._lock:
            if reservation_id in self._active_reservations:
                released = self._active_reservations.pop(reservation_id)
                logger.debug(
                    "Released reservation %s (%d tokens).", reservation_id, released
                )

    async def record_usage(
        self,
        operation: str,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        is_estimated: bool = False,
        retry_count: int = 0,
        reservation_id: str | None = None,
    ) -> TokenUsageRecord:
        """Record actual or estimated token usage, replacing any active reservation."""
        async with self._lock:
            # Reconcile reservation if provided
            if reservation_id and reservation_id in self._active_reservations:
                self._active_reservations.pop(reservation_id)

            total_call_tokens = input_tokens + output_tokens
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_tokens_spent += total_call_tokens
            self._total_retries += retry_count
            if is_estimated:
                self._any_estimated = True

            cost = TokenEstimator.calculate_cost(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                pricing_map=self.settings.MODEL_PRICING_PER_1M_TOKENS,
            )
            self._total_cost_usd += cost

            record = TokenUsageRecord(
                id=uuid.uuid4(),
                operation=operation,
                provider=provider,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_call_tokens,
                is_estimated=is_estimated,
                retry_count=retry_count,
                estimated_cost_usd=cost,
            )
            self._records.append(record)

            if (
                self._total_tokens_spent + sum(self._active_reservations.values())
                >= self.budget_limit
            ):
                self._is_exhausted = True

            logger.info(
                "Recorded usage: %s %s/%s -> %d in, %d out (%d total). "
                "Spent: %d/%d (exhausted=%s)",
                operation,
                provider,
                model_name,
                input_tokens,
                output_tokens,
                total_call_tokens,
                self._total_tokens_spent,
                self.budget_limit,
                self._is_exhausted,
            )
            return record

    def get_status(self) -> AnalysisBudgetStatus:
        """Produce point-in-time snapshot of the analysis budget state."""
        committed = self._total_tokens_spent + sum(self._active_reservations.values())
        rem = max(0, self.budget_limit - committed)
        return AnalysisBudgetStatus(
            analysis_id=self.analysis_id,
            owner_id=self.owner_id,
            budget_limit=self.budget_limit,
            total_input_tokens=self._total_input_tokens,
            total_output_tokens=self._total_output_tokens,
            total_tokens=self._total_tokens_spent,
            remaining_tokens=rem,
            estimated_cost_usd=round(self._total_cost_usd, 6),
            call_count=len(self._records),
            retry_count=self._total_retries,
            is_exhausted=self._is_exhausted or rem <= 0,
            is_estimated=self._any_estimated,
            records=[
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
                    timestamp=r.timestamp,
                )
                for r in self._records
            ],
        )
