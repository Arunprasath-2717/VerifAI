"""Domain models, records, and schemas for token accounting and budget enforcement."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import AppError


class BudgetExhaustedError(AppError):
    """Raised when an analysis exceeds its configured token budget."""

    def __init__(
        self,
        message: str = "Analysis token budget exhausted.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="TOKEN_BUDGET_EXHAUSTED",
            status_code=429,
            details=details,
        )


class UserDailyBudgetExceededError(AppError):
    """Raised when a user exceeds their daily token or analysis allowance."""

    def __init__(
        self,
        message: str = "Daily user token budget exceeded.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="USER_DAILY_BUDGET_EXCEEDED",
            status_code=429,
            details=details,
        )


@dataclass
class TokenUsageRecord:
    """Detailed record of an individual LLM invocation within an analysis."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    operation: str = "COMPLETION"  # EXTRACTION, CLAIM_EVALUATION, SUMMARIZATION
    provider: str = "unknown"
    model_name: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    is_estimated: bool = False
    retry_count: int = 0
    estimated_cost_usd: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "operation": self.operation,
            "provider": self.provider,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "is_estimated": self.is_estimated,
            "retry_count": self.retry_count,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
        }


class TokenUsageRecordSchema(BaseModel):
    """Pydantic schema for individual token usage records."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    operation: str
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    is_estimated: bool
    retry_count: int
    estimated_cost_usd: float
    timestamp: datetime


class AnalysisBudgetStatus(BaseModel):
    """Complete budget observability status for an analysis job."""

    model_config = ConfigDict(from_attributes=True)

    analysis_id: uuid.UUID
    owner_id: str
    budget_limit: int
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    remaining_tokens: int
    estimated_cost_usd: float = 0.0
    call_count: int = 0
    retry_count: int = 0
    is_exhausted: bool = False
    is_estimated: bool = False
    records: list[TokenUsageRecordSchema] = Field(default_factory=list)


class UserDailyUsageResponse(BaseModel):
    """Observability response for current user's daily budget usage."""

    user_id: str
    date_utc: str
    daily_token_limit: int
    tokens_used_today: int
    tokens_remaining_today: int
    daily_analyses_limit: int
    analyses_conducted_today: int
    analyses_remaining_today: int
