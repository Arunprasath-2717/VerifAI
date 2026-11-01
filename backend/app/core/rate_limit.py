"""In-memory bounded sliding-window rate limiter and concurrency tracking."""

import ipaddress
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

    Architecture Note — Supported Deployment Topology:
    - Supported: Single-process / single-worker deployment topology.
    - Limitation: State is process-local and stored in memory. In multi-worker
      or multi-replica container topologies behind a load balancer, each process
      enforces limits independently. If horizontal scaling across multiple
      replicas is required in the future, a distributed backing store (e.g. Redis)
      should be introduced.
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


def _is_ip_in_trusted_networks(ip_str: str, trusted_networks: list[str]) -> bool:
    """Check if an IP string belongs to any of the trusted network CIDRs or IPs."""
    if not ip_str or not trusted_networks:
        return False
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return False

    for network_str in trusted_networks:
        try:
            net = ipaddress.ip_network(network_str.strip(), strict=False)
            if ip in net:
                return True
        except ValueError:
            continue
    return False


def _extract_valid_ip(candidate: str) -> str | None:
    """Validate and return normalized IP string (IPv4 or IPv6), or None if malformed."""
    if not candidate or not isinstance(candidate, str):
        return None
    clean = candidate.strip().strip("[]")
    # If IPv4 with port (e.g. 192.0.2.1:5000), strip port
    if ":" in clean and clean.count(":") == 1:
        clean = clean.split(":")[0].strip()
    try:
        ip = ipaddress.ip_address(clean)
        return str(ip)
    except ValueError:
        return None


def get_client_identifier(
    request: Request,
    user_id: str | None = None,
    settings: Any = None,
) -> str:
    """Derive client identity from authenticated user ID or verified client IP.

    Security Architecture & Trusted Proxy Policy:
    - If user_id is provided, identity is strictly 'usr:<user_id>'.
    - If user_id is None, client IP is used for rate limiting.
    - A direct request from an untrusted client strictly uses the socket peer
      address (request.client.host) for rate limiting.
    - X-Forwarded-For headers are completely IGNORED unless the immediate socket
      peer matches a configured trusted proxy in Settings.FORWARDED_ALLOW_IPS.
    - When behind a trusted proxy, X-Forwarded-For is parsed and validated,
      walking right-to-left to determine the first untrusted upstream client address.
    - If the header is missing, malformed, or empty, the trusted peer IP is used safely.
    """
    if user_id:
        return f"usr:{user_id}"

    peer_ip = "127.0.0.1"
    if request.client and request.client.host:
        peer_ip = request.client.host.strip()

    normalized_peer = _extract_valid_ip(peer_ip) or peer_ip

    from app.core.config import get_settings

    app_settings = settings or get_settings()
    trusted_networks = getattr(app_settings, "FORWARDED_ALLOW_IPS", [])

    # Untrusted peer: strictly enforce direct connection socket IP
    if not _is_ip_in_trusted_networks(normalized_peer, trusted_networks):
        return f"ip:{normalized_peer}"

    # Peer is a verified trusted proxy: inspect X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if not forwarded or not forwarded.strip():
        return f"ip:{normalized_peer}"

    # Parse comma-separated forwarded addresses
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    valid_ips: list[str] = []
    for part in parts:
        valid = _extract_valid_ip(part)
        if valid:
            valid_ips.append(valid)

    if not valid_ips:
        # Header was present but contained only malformed non-IP tokens
        return f"ip:{normalized_peer}"

    # Walk right-to-left to find first untrusted upstream client IP
    client_ip = valid_ips[0]  # default to leftmost valid IP if all are untrusted
    for candidate in reversed(valid_ips):
        if not _is_ip_in_trusted_networks(candidate, trusted_networks):
            client_ip = candidate
            break

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

    identifier = get_client_identifier(request, user_id=user_id, settings=app_settings)
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
