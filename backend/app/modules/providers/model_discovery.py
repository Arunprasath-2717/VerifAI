"""Discover provider-supported chat models using the current user's BYOK credential.

No model IDs are hardcoded into the UI and upstream credentials never leave the
backend. Only OpenRouter's explicitly free `:free` routes are offered in
BYOK free mode; Groq availability is account/quota dependent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.modules.providers.chat_specs import SPECS, provider_protocol
from app.modules.providers.openai_compatible import resolve_openai_base_url

logger = logging.getLogger("verifai.providers.model_discovery")

MODEL_ENDPOINTS = {
    "prov-groq": "https://api.groq.com/openai/v1/models",
    "prov-openrouter": "https://openrouter.ai/api/v1/models",
}
_BLOCKED_GROQ_MARKERS = (
    "whisper",
    "speech",
    "tts",
    "audio",
    "guard",
    "moderation",
    "embedding",
    "transcribe",
    "distil",
)


@dataclass(frozen=True)
class ConnectedChatModel:
    id: str
    name: str
    provider: str
    provider_id: str
    context_window: int
    is_free: bool
    description: str

    def as_json(self) -> dict[str, str | int | bool]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "providerId": self.provider_id,
            "contextWindow": self.context_window,
            "isFree": self.is_free,
            "description": self.description,
        }


class ModelDiscoveryError(Exception):
    """A bounded, non-secret provider discovery failure."""


def parse_chat_models(provider_id: str, payload: object) -> list[ConnectedChatModel]:
    field_name = "models" if provider_id == "prov-google" else "data"
    if not isinstance(payload, dict) or not isinstance(payload.get(field_name), list):
        raise ModelDiscoveryError("Provider returned an invalid model catalog.")
    provider = (
        provider_id[5:]
        if provider_id.startswith("prov-")
        and not provider_id.startswith("prov-custom-")
        else provider_id
    )
    models: list[ConnectedChatModel] = []
    for item in payload[field_name]:
        if not isinstance(item, dict):
            continue
        if provider_id == "prov-google":
            methods = item.get("supportedGenerationMethods") or []
            if "generateContent" not in methods:
                continue
            model_id = str(item.get("name") or "")
            if model_id.startswith("models/"):
                model_id = model_id[len("models/") :]
        else:
            model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id or len(model_id) > 128:
            continue
        # Exclude obviously non-conversational models. A successful smoke
        # test, not the model name, is still authoritative for chat support.
        blocked_markers = (
            "whisper",
            "audio",
            "tts",
            "transcrib",
            "embed",
            "rerank",
            "moderation",
            "image",
            "video",
            "speech",
            "realtime",
            "guard",
            "dall-e",
            "sora",
            "voxtral",
            "orpheus",
            "safety",
            "prompt-guard",
            "allam-2-7b",
        )
        if any(marker in model_id.lower() for marker in blocked_markers):
            continue
        if item.get("active") is False:
            continue
        if provider == "openrouter":
            # A free model is explicitly :free. Never return paid routing IDs.
            if not model_id.endswith(":free"):
                continue
            output_modes = (
                item.get("architecture", {}).get("output_modalities")
                if isinstance(item.get("architecture"), dict)
                else None
            )
            if isinstance(output_modes, list) and "text" not in output_modes:
                continue
            # A :free suffix alone is not a sufficient pricing guarantee.
            # Provider metadata must explicitly confirm zero input/output cost.
            pricing = item.get("pricing")
            if not isinstance(pricing, dict):
                continue
            try:
                prompt_price = float(pricing["prompt"])
                completion_price = float(pricing["completion"])
            except (KeyError, ValueError, TypeError):
                continue
            if not (prompt_price == 0 and completion_price == 0):
                continue
        else:
            if any(marker in model_id.lower() for marker in _BLOCKED_GROQ_MARKERS):
                continue
        context = item.get("context_length", item.get("context_window", 0))
        try:
            context_window = max(0, int(context or 0))
        except (TypeError, ValueError):
            context_window = 0
        name = item.get("name") or model_id
        if not isinstance(name, str):
            name = model_id
        description = (
            "Free OpenRouter route · subject to provider rate limits."
            if provider == "openrouter"
            else "Groq hosted model · availability depends on your account."
            if provider == "groq"
            else "NVIDIA NIM hosted chat · quota and costs vary by account."
            if provider == "nvidia" or "nvidia" in provider
            else "User-owned OpenAI-compatible provider · quota and pricing vary."
        )
        models.append(
            ConnectedChatModel(
                id=model_id,
                name=name[:150],
                provider=provider,
                provider_id=provider_id,
                context_window=context_window,
                is_free=provider == "openrouter",
                description=description,
            )
        )
    # Rank modern general-purpose text models; never assume a catalog entry works.
    # A real completion probe with the owner's key remains authoritative.
    preferred = {"openai/gpt-oss-120b": 0, "openai/gpt-oss-20b": 1}
    known_retired = {"llama-3.1-8b-instant", "llama-3.3-70b-versatile"}
    return sorted(
        models,
        key=lambda m: (
            m.provider == "groq" and m.id.lower() in known_retired,
            preferred.get(m.id.lower(), 50),
            -m.context_window,
            m.name.lower(),
        ),
    )[:100]


async def fetch_chat_models(
    provider_id: str,
    api_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
    base_url: str | None = None,
    provider_name: str | None = None,
) -> list[ConnectedChatModel]:
    definition = SPECS.get(provider_id)
    url = (
        definition.base_url + "/models"
        if definition
        else MODEL_ENDPOINTS.get(provider_id)
    )
    if not url and provider_id.startswith("prov-custom-"):
        try:
            url = (
                resolve_openai_base_url(
                    provider_id,
                    base_url,
                    provider_name,
                    resolve_dns=transport is None,
                )
                + "/models"
            )
        except Exception as exc:
            raise ModelDiscoveryError(
                "Configure a safe public HTTPS endpoint. For NVIDIA hosted NIM "
                "use https://integrate.api.nvidia.com/v1."
            ) from exc
    if not url:
        raise ModelDiscoveryError(
            "Chat model discovery is not supported for this provider."
        )
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(9.0),
            transport=transport,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            protocol = provider_protocol(provider_id)
            headers = (
                {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
                if protocol == "anthropic"
                else {"x-goog-api-key": api_key}
                if protocol == "gemini"
                else {"Authorization": f"Bearer {api_key}"}
            )
            response = await client.get(url, headers=headers)
            if response.status_code == 401 or response.status_code == 403:
                raise ModelDiscoveryError(
                    "Credential was rejected. Test the provider connection."
                )
            if response.status_code == 429:
                raise ModelDiscoveryError(
                    "Provider rate limit reached; refresh models later."
                )
            if response.status_code != 200:
                raise ModelDiscoveryError(
                    f"Model discovery unavailable (HTTP {response.status_code})."
                )
            return parse_chat_models(provider_id, response.json())
    except httpx.TimeoutException as exc:
        raise ModelDiscoveryError("Model discovery timed out.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "Model discovery error provider=%s type=%s", provider_id, type(exc).__name__
        )
        raise ModelDiscoveryError(
            "Could not reach the provider model catalog."
        ) from exc
