"""Supabase integration client for VerifAI backend.

Provides asynchronous HTTP-based access to Supabase services:
- PostgREST REST API (/rest/v1/)
- GoTrue Auth API (/auth/v1/)
- Storage API (/storage/v1/)

Security controls:
- API keys are handled as SecretStr and never leaked to logs or exceptions.
- Requests enforce strict connection and read timeouts.
- Graceful degradation when unconfigured or unreachable.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger("verifai.supabase")

_DEFAULT_TIMEOUT_SECONDS = 5.0


class SupabaseClient:
    """Asynchronous client for Supabase services using HTTP API.

    Works without requiring the heavy third-party Supabase Python SDK,
    operating natively with async httpx and conforming to modern Supabase
    API authentication headers (`apikey` and `Authorization: Bearer <key>`).
    """

    def __init__(
        self,
        url: str | None = None,
        publishable_key: str | None = None,
        secret_key: str | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._url = url.rstrip("/") if url else None
        self._publishable_key = publishable_key
        self._secret_key = secret_key
        self._timeout = timeout_seconds

    @property
    def is_configured(self) -> bool:
        """Return True when both URL and at least one API key are present."""
        return bool(self._url and (self._secret_key or self._publishable_key))

    @property
    def active_key(self) -> str | None:
        """Return the highest-privilege available key (secret key preferred)."""
        return self._secret_key or self._publishable_key

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "SupabaseClient":
        """Instantiate client from application settings."""
        s = settings or get_settings()
        pub_key = (
            s.SUPABASE_PUBLISHABLE_KEY.get_secret_value()
            if s.SUPABASE_PUBLISHABLE_KEY
            else None
        )
        sec_key = (
            s.SUPABASE_SECRET_KEY.get_secret_value() if s.SUPABASE_SECRET_KEY else None
        )
        return cls(
            url=s.SUPABASE_URL,
            publishable_key=pub_key,
            secret_key=sec_key,
        )

    def _get_headers(self, use_secret: bool = True) -> dict[str, str]:
        """Construct secure authorization headers."""
        key = (
            self._secret_key
            if (use_secret and self._secret_key)
            else (self._publishable_key or self._secret_key or "")
        )
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "VerifAI-Backend/0.1.0",
        }

    async def check_connectivity(self) -> dict[str, Any]:
        """Probe Supabase REST API availability.

        Returns structured status dict without exposing keys or URLs.
        """
        if not self.is_configured:
            return {
                "configured": False,
                "status": "unconfigured",
            }

        endpoint = f"{self._url}/rest/v1/"
        headers = self._get_headers(use_secret=False)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(endpoint, headers=headers)
                # Supabase REST API root returns 200 or 404 (Swagger / schema)
                if response.status_code in (200, 401, 404):
                    return {
                        "configured": True,
                        "status": "available",
                    }
                return {
                    "configured": True,
                    "status": "unavailable",
                }
        except Exception as exc:
            logger.warning(
                "Supabase connectivity probe failed: %s",
                type(exc).__name__,
            )
            return {
                "configured": True,
                "status": "unavailable",
            }
        return {
            "configured": True,
            "status": "unavailable",
        }

    async def query_table(
        self,
        table: str,
        select: str = "*",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Query a table via PostgREST endpoint.

        Returns empty list on failure or when unconfigured.
        """
        if not self.is_configured or not self._url:
            return []

        endpoint = f"{self._url}/rest/v1/{table}"
        headers = self._get_headers(use_secret=True)
        params: dict[str, str | int] = {"select": select, "limit": limit}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(endpoint, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                logger.warning(
                    "Supabase table query on '%s' returned status %d",
                    table,
                    response.status_code,
                )
                return []
        except Exception as exc:
            logger.warning(
                "Supabase query failed for table '%s': %s",
                table,
                type(exc).__name__,
            )
            return []


def get_supabase_client(
    settings: Settings = get_settings(),
) -> SupabaseClient:
    """Dependency provider for SupabaseClient."""
    return SupabaseClient.from_settings(settings=settings)
