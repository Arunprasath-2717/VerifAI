"""Per-account brute-force protection for password login.

IP-based rate limiting alone is not enough: an attacker rotating addresses can
guess one account's password indefinitely. This tracks consecutive failures per
normalized account identifier and locks it for a cooldown after too many.

State is process-local, matching the rate limiter. A multi-replica deployment
needs a shared store (for example Redis) to keep the lock global.
"""

import logging
import threading
import time
from dataclasses import dataclass, field

from app.core.errors import RateLimitError

logger = logging.getLogger("verifai.lockout")

MAX_TRACKED_ACCOUNTS = 10_000


@dataclass
class _Record:
    failures: int = 0
    window_start: float = 0.0
    locked_until: float = 0.0
    last_seen: float = field(default=0.0)


class AccountLockout:
    """Counts failed password attempts per account and enforces a cooldown."""

    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: float = 900.0,
        lock_seconds: float = 900.0,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._records: dict[str, _Record] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(identifier: str) -> str:
        return identifier.strip().casefold()

    def _evict_if_full(self, now: float) -> None:
        if len(self._records) < MAX_TRACKED_ACCOUNTS:
            return
        # Drop the least recently seen record. Bounded memory beats unbounded growth
        # under a credential-stuffing flood; the cost is a reset for an evicted account.
        oldest = min(self._records, key=lambda k: self._records[k].last_seen)
        self._records.pop(oldest, None)

    def check_allowed(self, identifier: str) -> None:
        """Raise 429 if the account is currently locked. Does not record anything."""
        key = self._key(identifier)
        now = time.monotonic()
        with self._lock:
            record = self._records.get(key)
            if record and record.locked_until > now:
                retry_after = max(1, int(record.locked_until - now))
                raise RateLimitError(
                    message=(
                        "Too many failed sign-in attempts. "
                        f"Try again in {retry_after} seconds."
                    ),
                    retry_after=retry_after,
                    details={"reason": "account_locked", "retry_after": retry_after},
                )

    def record_failure(self, identifier: str) -> None:
        key = self._key(identifier)
        now = time.monotonic()
        with self._lock:
            record = self._records.get(key)
            if record is None:
                self._evict_if_full(now)
                record = _Record(window_start=now)
                self._records[key] = record
            if now - record.window_start > self.window_seconds:
                record.failures = 0
                record.window_start = now
            record.failures += 1
            record.last_seen = now
            if record.failures >= self.max_failures:
                record.locked_until = now + self.lock_seconds
                record.failures = 0
                record.window_start = now
                logger.warning("Account temporarily locked after repeated failures.")

    def record_success(self, identifier: str) -> None:
        with self._lock:
            self._records.pop(self._key(identifier), None)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


_ACCOUNT_LOCKOUT = AccountLockout()


def get_account_lockout() -> AccountLockout:
    return _ACCOUNT_LOCKOUT
