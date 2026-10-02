"""In-memory bounded sliding-window rate limiter and concurrency tracking."""

import logging
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Request

from app.core.errors import RateLimitError

logger = logging.getLogger("verifai.rate_limit")


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter.

    Note: Single-process in-memory limiter. Multi-replica production deployments
    must utilize a distributed backing store (e.g., Redis).
    """

    def __init__(self, max_keys: int = 10000) -> None:
        self.max_keys = max_keys
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def _cleanup_stale(self, now: float, window_seconds: float) -> None:
        """Purge expired entries periodically to prevent memory unbounded growth."""
        if now - self._last_cleanup < 30.0 and len(self._history) < self.max_keys:
            return

        cutoff = now - (window_seconds * 2)
        stale_keys = []
        for key, timestamps in self._history.items():
            fresh = [t for t in timestamps if t > cutoff]
            if fresh:
                self._history[key] = fresh
            else:
                stale_keys.append(key)

        for key in stale_keys:
            self._history.pop(key, None)

        self._last_cleanup = now

    def check(
        self, key: str, limit: int, window_seconds: float = 60.0
    ) -> tuple[bool, int]:
        """Check if request under `key` is permitted within the sliding window.

        Returns:
            (allowed: bool, retry_after: int)
        """
        now = time.monotonic()
        self._cleanup_stale(now, window_seconds)

        timestamps = self._history[key]
        cutoff = now - window_seconds
        active = [t for t in timestamps if t > cutoff]
        self._history[key] = active

        if len(active) >= limit:
            oldest = active[0]
            retry_after = max(1, int(window_seconds - (now - oldest)))
            return False, retry_after

        active.append(now)
        return True, 0

    def clear(self) -> None:
        """Reset all rate limiting state."""
        self._history.clear()


# Global rate limiter instance
_GLOBAL_RATE_LIMITER = SlidingWindowRateLimiter()


def clear_rate_limits() -> None:
    """Reset all rate limiting and concurrency state."""
    _GLOBAL_RATE_LIMITER.clear()
    _ACTIVE_USER_VERIFICATIONS.clear()


def get_client_identifier(request: Request, user_id: str | None = None) -> str:
    """Derive client identity from authenticated user ID or remote client IP."""
    if user_id:
        return f"usr:{user_id}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    return f"ip:{client_ip}"


def _is_testing_environment(settings: Any) -> bool:
    """Detect if execution is within automated test suite."""
    import os
    import sys

    return (
        settings.ENVIRONMENT in ("test", "testing")
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in sys.modules
    )


def enforce_rate_limit(
    request: Request,
    action: str,
    limit: int,
    window_seconds: float = 60.0,
    user_id: str | None = None,
    settings: Any = None,
) -> None:
    """Enforce rate limit for an action or raise RateLimitError (HTTP 429)."""
    from app.core.config import get_settings

    app_settings = settings or get_settings()
    if not app_settings.RATE_LIMIT_ENABLED:
        return
    if (
        _is_testing_environment(app_settings)
        and not app_settings.RATE_LIMIT_ENABLED_IN_TEST
    ):
        return

    identifier = get_client_identifier(request, user_id=user_id)
    key = f"{action}:{identifier}"

    allowed, retry_after = _GLOBAL_RATE_LIMITER.check(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
    )
    if not allowed:
        logger.warning(
            "Rate limit exceeded for %s on action '%s' (limit=%d/%ds, retry_after=%ds)",
            identifier,
            action,
            limit,
            int(window_seconds),
            retry_after,
        )
        raise RateLimitError(
            message=(
                f"Rate limit exceeded for {action}. "
                f"Please retry in {retry_after} seconds."
            ),
            retry_after=retry_after,
            details={"action": action, "retry_after": retry_after},
        )


# ==============================================================================
# Bounded User Verification Concurrency Tracker (Max 3 Concurrent Jobs)
# ==============================================================================
_ACTIVE_USER_VERIFICATIONS: dict[str, int] = defaultdict(int)


@asynccontextmanager
async def track_verification_concurrency(
    owner_id: str,
    max_concurrent: int = 3,
    settings: Any = None,
) -> AsyncGenerator[None, None]:
    """Track and enforce maximum concurrent verification jobs per owner/user."""
    from app.core.config import get_settings

    app_settings = settings or get_settings()
    if (
        _is_testing_environment(app_settings)
        and not app_settings.RATE_LIMIT_ENABLED_IN_TEST
    ):
        yield
        return

    current = _ACTIVE_USER_VERIFICATIONS[owner_id]
    if current >= max_concurrent:
        logger.warning(
            "Concurrency limit exceeded for owner '%s' (%d >= %d)",
            owner_id,
            current,
            max_concurrent,
        )
        raise RateLimitError(
            message=(
                f"Maximum concurrent verification jobs ({max_concurrent}) exceeded. "
                "Please wait for active verifications to complete."
            ),
            retry_after=5,
            details={"owner_id": owner_id, "max_concurrent": max_concurrent},
        )

    _ACTIVE_USER_VERIFICATIONS[owner_id] += 1
    try:
        yield
    finally:
        _ACTIVE_USER_VERIFICATIONS[owner_id] = max(
            0, _ACTIVE_USER_VERIFICATIONS[owner_id] - 1
        )
