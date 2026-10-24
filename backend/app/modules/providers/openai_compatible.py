"""Secure OpenAI-compatible BYOK endpoint normalization and model provider identity."""

from __future__ import annotations

from urllib.parse import urlsplit

from app.core.errors import BadRequestError
from app.modules.evidence.security import is_safe_url
from app.modules.providers.chat_specs import SPECS

NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# This historical frontend default is actually VerifAI's own development API,
# not an NVIDIA NIM server. Never forward a key to it.
_LEGACY_WRONG_NIM_URLS = frozenset(
    {
        "http://localhost:8000/v1",
        "http://127.0.0.1:8000/v1",
    }
)


def is_nvidia_connection(provider_id: str, name: str | None = None) -> bool:
    ident = provider_id.lower()
    label = (name or "").lower()
    return ident == "prov-nvidia" or (
        ident.startswith("prov-custom-")
        and ("nvidia" in ident or "nvidia" in label or "nim" in label)
    )


def resolve_openai_base_url(
    provider_id: str,
    configured_url: str | None,
    name: str | None = None,
    *,
    resolve_dns: bool = True,
) -> str:
    """Fail closed for unsafe destinations; migrate the stale NVIDIA placeholder.

    Real hosted provider credentials are transmitted only over public HTTPS.
    Users wishing to reach self-hosted private NIM deployments need an explicitly
    configured, trusted proxy; never silently send keys to local application
    backends or arbitrary private IPs.
    """
    raw = (configured_url or "").strip().rstrip("/")
    if provider_id in SPECS:
        # Built-in keys can NEVER be redirected to another host.
        return SPECS[provider_id].base_url
    nvidia = is_nvidia_connection(provider_id, name)
    if nvidia and (not raw or raw.lower() in _LEGACY_WRONG_NIM_URLS):
        return NVIDIA_NIM_BASE_URL
    if not raw:
        raise BadRequestError("Specify the provider's public HTTPS /v1 API base URL.")
    parsed = urlsplit(raw)
    if (
        parsed.scheme.lower() != "https"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/").endswith(("/models", "/chat/completions"))
        or not is_safe_url(raw, resolve_dns=resolve_dns)
    ):
        raise BadRequestError(
            "Use a public HTTPS OpenAI-compatible base URL ending in /v1. "
            "Localhost, private addresses and unsafe destinations are not allowed."
        )
    return raw
