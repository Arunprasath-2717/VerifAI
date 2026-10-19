"""Tenant-isolated cache for completed analyses preventing redundant LLM expenditure."""

import hashlib
import json
import time
from typing import Any

from app.schemas.verification import VerificationResponse


class AnalysisCacheService:
    """Provides safe, tenant-isolated caching of verified responses.

    Enforces:
    - Isolation: Results are strictly keyed by (owner_id, hash(payload)).
    - Privacy: User B can never retrieve User A's cached verification.
    - Expiration: TTL-bounded caching.
    """

    _instance: "AnalysisCacheService | None" = None

    def __init__(self) -> None:
        # Key: (owner_id, cache_hash) -> (VerificationResponse, expires_at)
        self._store: dict[tuple[str, str], tuple[VerificationResponse, float]] = {}

    @classmethod
    def get_instance(cls) -> "AnalysisCacheService":
        if cls._instance is None:
            cls._instance = AnalysisCacheService()
        return cls._instance

    @classmethod
    def reset_for_test(cls) -> None:
        cls._instance = AnalysisCacheService()

    @staticmethod
    def compute_hash(
        text: str,
        query: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Generate deterministic SHA256 digest of normalized input payload."""
        payload = {
            "text": text.strip(),
            "query": (query or "").strip(),
            "options": options or {},
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(
        self,
        owner_id: str,
        cache_hash: str,
    ) -> VerificationResponse | None:
        """Retrieve cached analysis if valid and owned by the requesting owner_id."""
        key = (owner_id, cache_hash)
        entry = self._store.get(key)
        if not entry:
            return None

        response, expires_at = entry
        if time.time() > expires_at:
            # Expired
            self._store.pop(key, None)
            return None

        return response

    def set(
        self,
        owner_id: str,
        cache_hash: str,
        response: VerificationResponse,
        ttl_seconds: int = 3600,
    ) -> None:
        """Store completed analysis result with strict tenant boundary and TTL."""
        key = (owner_id, cache_hash)
        expires_at = time.time() + ttl_seconds
        self._store[key] = (response, expires_at)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()
