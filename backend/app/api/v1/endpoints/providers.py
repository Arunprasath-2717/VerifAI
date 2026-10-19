"""AI provider configuration and BYOK credential management endpoints.

All routes require an authenticated user. Credentials are stored encrypted per
owner (``user_provider_credentials``) and are never returned in plaintext.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from datetime import UTC

import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models.provider_credential import UserProviderCredential
from app.models.user import User
from app.modules.providers import connection_validator as validator
from app.modules.providers.credential_crypto import (
    decrypt_credential,
    encrypt_credential,
)
from app.repositories.provider_credential import ProviderCredentialRepository
from app.schemas.providers import (
    AIProviderItem,
    ProviderSaveKeyRequest,
    ProviderTestResponse,
)

logger = logging.getLogger("verifai.api.providers")

# Test seam: lets tests route provider checks through an httpx MockTransport
# so the suite never performs live network calls.
_CHECK_TRANSPORT: ContextVar[httpx.AsyncBaseTransport | None] = ContextVar(
    "provider_check_transport", default=None
)
router = APIRouter(prefix="/providers", tags=["AI Providers"])

# Catalogue of providers the application knows about. Model lists here are
# display hints only; the model registry governs selectable models.
PROVIDER_CATALOGUE: dict[str, dict[str, str | list[str]]] = {
    "prov-openai": {
        "name": "OpenAI",
        "category": "cloud",
        "docsUrl": "https://platform.openai.com/api-keys",
    },
    "prov-anthropic": {
        "name": "Anthropic",
        "category": "cloud",
        "docsUrl": "https://console.anthropic.com/settings/keys",
    },
    "prov-google": {
        "name": "Google Gemini",
        "category": "cloud",
        "docsUrl": "https://aistudio.google.com/apikey",
    },
    "prov-groq": {
        "name": "Groq Cloud",
        "category": "cloud",
        "docsUrl": "https://console.groq.com/keys",
    },
    "prov-mistral": {
        "name": "Mistral AI",
        "category": "cloud",
        "docsUrl": "https://console.mistral.ai/api-keys",
    },
    "prov-deepseek": {
        "name": "DeepSeek",
        "category": "cloud",
        "docsUrl": "https://platform.deepseek.com/api_keys",
    },
    "prov-openrouter": {
        "name": "OpenRouter Gateway",
        "category": "router",
        "docsUrl": "https://openrouter.ai/docs#models",
    },
}


def _mask_key(raw_key: str) -> str:
    """Mask an API key for display, keeping only a short prefix and suffix."""
    clean = raw_key.strip()
    if len(clean) <= 8:
        return "••••••••"
    return f"{clean[:4]}••••••••{clean[-4:]}"


_FAILED_STATUSES = frozenset(
    {"INVALID_KEY", "UPSTREAM_ERROR", "TIMEOUT", "RATE_LIMITED"}
)


def _to_item(provider_id: str, row: UserProviderCredential | None) -> AIProviderItem:
    meta = PROVIDER_CATALOGUE.get(
        provider_id, {"name": provider_id, "category": "cloud"}
    )
    docs_url = str(meta["docsUrl"]) if meta.get("docsUrl") else None
    if row is None:
        return AIProviderItem(
            id=provider_id,
            name=str(meta["name"]),
            category=str(meta["category"]),  # type: ignore[arg-type]
            status="Not Connected",
            docsUrl=docs_url,
        )
    status_value = (
        "Unavailable" if row.validation_status in _FAILED_STATUSES else "Connected"
    )
    configured = row.created_at.astimezone(UTC).strftime("%b %d, %Y")
    return AIProviderItem(
        id=provider_id,
        name=str(meta["name"]),
        category=str(meta["category"]),  # type: ignore[arg-type]
        status=status_value,  # type: ignore[arg-type]
        configuredAt=configured,
        keyMasked=row.key_hint,
        baseUrl=row.base_url,
        organizationId=row.organization_id,
        docsUrl=docs_url,
    )


def _require_known_provider(provider_id: str) -> None:
    if provider_id not in PROVIDER_CATALOGUE:
        raise NotFoundError(
            message="Unknown AI provider.",
            details={"provider_id": provider_id},
        )


@router.get(
    "",
    response_model=list[AIProviderItem],
    summary="List AI Providers and Connectivity Statuses",
    description="Returns providers with the caller's masked credential status.",
)
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[AIProviderItem]:
    repo = ProviderCredentialRepository(db)
    rows = {r.provider_id: r for r in await repo.list_for_user(current_user.id)}
    return [_to_item(pid, rows.get(pid)) for pid in PROVIDER_CATALOGUE]


@router.post(
    "/{provider_id}/key",
    response_model=AIProviderItem,
    status_code=status.HTTP_200_OK,
    summary="Save an encrypted API key for an AI provider",
    description="Encrypts and stores the caller's key. Only a masked hint is returned.",
)
async def save_provider_key(
    provider_id: str,
    payload: ProviderSaveKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> AIProviderItem:
    _require_known_provider(provider_id)
    # Encryption runs before any write. A missing or invalid key raises here
    # (503) so no plaintext or unusable credential is ever persisted.
    ciphertext = encrypt_credential(settings, payload.apiKey.strip())
    repo = ProviderCredentialRepository(db)
    row = await repo.upsert(
        user_id=current_user.id,
        provider_id=provider_id,
        encrypted_api_key=ciphertext,
        key_hint=_mask_key(payload.apiKey),
        base_url=payload.baseUrl,
        organization_id=payload.organizationId,
    )
    logger.info("Provider key saved: provider=%s user=%s", provider_id, current_user.id)
    return _to_item(provider_id, row)


@router.delete(
    "/{provider_id}/key",
    status_code=status.HTTP_200_OK,
    summary="Remove the caller's API key for an AI provider",
)
async def unlink_provider_key(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    _require_known_provider(provider_id)
    repo = ProviderCredentialRepository(db)
    removed = await repo.delete(current_user.id, provider_id)
    return {"unlinked": removed, "provider_id": provider_id}


@router.post(
    "/{provider_id}/test",
    response_model=ProviderTestResponse,
    summary="Validate the caller's stored API key with the provider",
    description="Performs one real, authenticated request using the stored key.",
)
async def test_provider_connection(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> ProviderTestResponse:
    _require_known_provider(provider_id)
    repo = ProviderCredentialRepository(db)
    row = await repo.get(current_user.id, provider_id)
    if row is None:
        raise NotFoundError(
            message="No API key is saved for this provider.",
            details={"provider_id": provider_id},
        )
    api_key = decrypt_credential(settings, row.encrypted_api_key)
    result = await validator.validate_api_key(
        provider_id, api_key, transport=_CHECK_TRANSPORT.get()
    )
    await repo.mark_validated(row, result.status)
    return ProviderTestResponse(
        id=provider_id,
        success=result.status == validator.VALID,
        status=result.status,
        message=result.message,
        latency_ms=result.latency_ms,
    )
