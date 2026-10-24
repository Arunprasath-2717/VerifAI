"""Live connection checks for BYOK provider credentials.

Each check performs one bounded, authenticated HTTP request. Results are
reduced to a small status vocabulary; upstream bodies and the key itself are
never returned or logged.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from app.modules.providers.chat_specs import SPECS
from app.modules.providers.openai_compatible import resolve_openai_base_url

logger = logging.getLogger("verifai.providers.validator")

VALID = "VALID"
INVALID_KEY = "INVALID_KEY"
RATE_LIMITED = "RATE_LIMITED"
UPSTREAM_ERROR = "UPSTREAM_ERROR"
TIMEOUT = "TIMEOUT"
UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class ProviderCheckSpec:
    """Describes how to validate one provider's credential."""

    url: str
    auth_header: str  # header name for the credential
    auth_prefix: str  # e.g. "Bearer " or ""
    extra_headers: tuple[tuple[str, str], ...] = ()


# Endpoints are configuration, not code paths: adjust here if a provider changes.
CHECK_SPECS: dict[str, ProviderCheckSpec] = {
    "prov-openai": ProviderCheckSpec(
        url="https://api.openai.com/v1/models",
        auth_header="Authorization",
        auth_prefix="Bearer ",
    ),
    "prov-anthropic": ProviderCheckSpec(
        url="https://api.anthropic.com/v1/models",
        auth_header="x-api-key",
        auth_prefix="",
        extra_headers=(("anthropic-version", "2023-06-01"),),
    ),
    "prov-google": ProviderCheckSpec(
        url="https://generativelanguage.googleapis.com/v1beta/models",
        auth_header="x-goog-api-key",
        auth_prefix="",
    ),
    "prov-groq": ProviderCheckSpec(
        url="https://api.groq.com/openai/v1/models",
        auth_header="Authorization",
        auth_prefix="Bearer ",
    ),
    "prov-openrouter": ProviderCheckSpec(
        url="https://openrouter.ai/api/v1/models",
        auth_header="Authorization",
        auth_prefix="Bearer ",
    ),
    "prov-deepseek": ProviderCheckSpec(
        url="https://api.deepseek.com/models",
        auth_header="Authorization",
        auth_prefix="Bearer ",
    ),
    "prov-mistral": ProviderCheckSpec(
        url="https://api.mistral.ai/v1/models",
        auth_header="Authorization",
        auth_prefix="Bearer ",
    ),
}


@dataclass(frozen=True)
class ConnectionCheckResult:
    status: str
    latency_ms: int
    message: str


async def validate_api_key(
    provider_id: str,
    api_key: str,
    timeout_seconds: float = 10.0,
    transport: httpx.AsyncBaseTransport | None = None,
    base_url: str | None = None,
) -> ConnectionCheckResult:
    """Run one authenticated request and classify the outcome."""
    spec = CHECK_SPECS.get(provider_id)
    if provider_id in SPECS and provider_id not in CHECK_SPECS:
        definition = SPECS[provider_id]
        if definition.protocol == "anthropic":
            spec = ProviderCheckSpec(
                url=definition.base_url + "/models",
                auth_header="x-api-key",
                auth_prefix="",
                extra_headers=(("anthropic-version", "2023-06-01"),),
            )
        elif definition.protocol == "gemini":
            spec = ProviderCheckSpec(
                url=definition.base_url + "/models",
                auth_header="x-goog-api-key",
                auth_prefix="",
            )
        else:
            spec = ProviderCheckSpec(
                url=definition.base_url + "/models",
                auth_header="Authorization",
                auth_prefix="Bearer ",
            )
    if spec is None:
        if provider_id == "prov-nvidia" or provider_id.startswith("prov-custom"):
            try:
                safe_url = resolve_openai_base_url(
                    provider_id,
                    base_url,
                    resolve_dns=transport is None,
                )
                spec = ProviderCheckSpec(
                    url=safe_url + "/models",
                    auth_header="Authorization",
                    auth_prefix="Bearer ",
                )
            except Exception:
                return ConnectionCheckResult(
                    UNSUPPORTED,
                    0,
                    "Set a safe HTTPS provider endpoint. NVIDIA NIM hosted "
                    "API: https://integrate.api.nvidia.com/v1.",
                )
        else:
            return ConnectionCheckResult(
                status=UNSUPPORTED,
                latency_ms=0,
                message="Live connection testing is not available for this provider.",
            )

    headers = {spec.auth_header: f"{spec.auth_prefix}{api_key}"}
    headers.update(dict(spec.extra_headers))
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            resp = await client.get(spec.url, headers=headers)
    except httpx.TimeoutException:
        return ConnectionCheckResult(
            TIMEOUT, 0, "The provider did not respond in time."
        )
    except httpx.HTTPError as exc:
        # Log only the exception class; the request contained the credential.
        logger.warning(
            "Provider check transport failure: provider=%s type=%s",
            provider_id,
            type(exc).__name__,
        )
        return ConnectionCheckResult(
            UPSTREAM_ERROR, 0, "The provider could not be reached."
        )

    latency = int((time.monotonic() - started) * 1000)
    code = resp.status_code
    if 200 <= code < 300:
        if provider_id == "prov-nvidia" or provider_id.startswith("prov-custom"):
            try:
                payload = resp.json()
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("data"), list
                ):
                    return ConnectionCheckResult(
                        UPSTREAM_ERROR,
                        latency,
                        "Endpoint did not return an OpenAI-compatible model list.",
                    )
            except (ValueError, TypeError):
                return ConnectionCheckResult(
                    UPSTREAM_ERROR,
                    latency,
                    "Endpoint did not return a valid JSON model list.",
                )
        return ConnectionCheckResult(
            VALID, latency, "Credential accepted by the provider."
        )
    if code in (401, 403):
        return ConnectionCheckResult(
            INVALID_KEY, latency, "The provider rejected this API key."
        )
    if code == 429:
        return ConnectionCheckResult(
            RATE_LIMITED,
            latency,
            "The provider rate-limited the check. Try again later.",
        )
    return ConnectionCheckResult(
        UPSTREAM_ERROR, latency, f"The provider returned an unexpected status ({code})."
    )
