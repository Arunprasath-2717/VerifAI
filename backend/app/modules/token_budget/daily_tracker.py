"""Daily per-user token and analysis quota tracking."""

import asyncio
from collections import defaultdict
from datetime import UTC, datetime

from app.modules.token_budget.models import (
    UserDailyBudgetExceededError,
    UserDailyUsageResponse,
)


class UserDailyBudgetTracker:
    """Tracks daily usage metrics per user strictly partitioned by UTC date."""

    _instance: "UserDailyBudgetTracker | None" = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        # Structure: date_str -> user_id -> {"tokens": int, "analyses": int}
        self._daily_store: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {"tokens": 0, "analyses": 0})
        )

    @classmethod
    def get_instance(cls) -> "UserDailyBudgetTracker":
        if cls._instance is None:
            cls._instance = UserDailyBudgetTracker()
        return cls._instance

    @classmethod
    def reset_for_test(cls) -> None:
        """Clear state for hermetic unit and integration testing."""
        cls._instance = UserDailyBudgetTracker()

    @staticmethod
    def _current_date_key() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    async def check_and_increment_analysis(
        self,
        user_id: str,
        daily_max_analyses: int,
    ) -> None:
        """Verify and record an analysis initiation against the daily limit."""
        async with self._lock:
            date_key = self._current_date_key()
            user_data = self._daily_store[date_key][user_id]
            current_count = user_data["analyses"]

            if current_count >= daily_max_analyses:
                raise UserDailyBudgetExceededError(
                    message=(
                        f"Daily analysis limit reached for user {user_id}. "
                        f"Max permitted: {daily_max_analyses} analyses per day."
                    ),
                    details={
                        "user_id": user_id,
                        "date_utc": date_key,
                        "analyses_conducted": current_count,
                        "daily_max_analyses": daily_max_analyses,
                    },
                )
            user_data["analyses"] += 1

    async def check_daily_token_budget(
        self,
        user_id: str,
        estimated_tokens: int,
        daily_max_tokens: int,
    ) -> None:
        """Check whether estimated tokens would breach user daily token quota."""
        async with self._lock:
            date_key = self._current_date_key()
            user_data = self._daily_store[date_key][user_id]
            current_tokens = user_data["tokens"]

            if current_tokens + estimated_tokens > daily_max_tokens:
                raise UserDailyBudgetExceededError(
                    message=(
                        f"Daily token quota exceeded for user {user_id}. "
                        f"Attempting {estimated_tokens} tokens with {current_tokens} "
                        f"already used (limit: {daily_max_tokens})."
                    ),
                    details={
                        "user_id": user_id,
                        "date_utc": date_key,
                        "tokens_used": current_tokens,
                        "requested_tokens": estimated_tokens,
                        "daily_max_tokens": daily_max_tokens,
                    },
                )

    async def record_daily_tokens(
        self,
        user_id: str,
        tokens: int,
    ) -> None:
        """Increment actual tokens used by user for the current day."""
        async with self._lock:
            date_key = self._current_date_key()
            self._daily_store[date_key][user_id]["tokens"] += tokens

    async def get_user_daily_usage(
        self,
        user_id: str,
        daily_token_limit: int = 100000,
        daily_analyses_limit: int = 50,
    ) -> UserDailyUsageResponse:
        """Retrieve aggregated daily usage statistics for the user."""
        async with self._lock:
            date_key = self._current_date_key()
            user_data = self._daily_store[date_key][user_id]
            used_tokens = user_data["tokens"]
            used_analyses = user_data["analyses"]

            return UserDailyUsageResponse(
                user_id=user_id,
                date_utc=date_key,
                daily_token_limit=daily_token_limit,
                tokens_used_today=used_tokens,
                tokens_remaining_today=max(0, daily_token_limit - used_tokens),
                daily_analyses_limit=daily_analyses_limit,
                analyses_conducted_today=used_analyses,
                analyses_remaining_today=max(0, daily_analyses_limit - used_analyses),
            )
