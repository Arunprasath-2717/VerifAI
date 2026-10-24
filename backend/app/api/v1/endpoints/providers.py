"""AI provider configuration and BYOK credential management endpoints.

All routes require an authenticated user. Credentials are stored encrypted per
owner (``user_provider_credentials``) and are never returned in plaintext.
"""

from __future__ import annotations

import asyncio
import logging
from contextvars import ContextVar
from datetime import UTC

import httpx
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.core.errors import BadRequestError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.models.provider_credential import UserProviderCredential
from app.models.user import User
from app.modules.chat.service import ChatService
from app.modules.providers import connection_validator as validator
from app.modules.providers.chat_specs import (
    SPECS,
    credential_provider_id,
    is_supported_provider,
)
from app.modules.providers.credential_crypto import (
    decrypt_credential,
    encrypt_credential,
)
from app.modules.providers.model_discovery import (
    ModelDiscoveryError,
    fetch_chat_models,
)
from app.modules.providers.openai_compatible import (
    is_nvidia_connection,
    resolve_openai_base_url,
)
from app.repositories.provider_credential import ProviderCredentialRepository
from app.schemas.chat import ChatPromptRequest, LLMModelSelection
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
_DISCOVERY_TRANSPORT: ContextVar[httpx.AsyncBaseTransport | None] = ContextVar(
    "provider_discovery_transport", default=None
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
    "prov-nvidia": {
        "name": "NVIDIA NIM",
        "category": "cloud",
        "docsUrl": "https://build.nvidia.com/",
    },
    "prov-openrouter": {
        "name": "OpenRouter Gateway",
        "category": "router",
        "docsUrl": "https://openrouter.ai/docs#models",
    },
    "prov-custom": {
        "name": "Custom OpenAI-Compatible API",
        "category": "cloud",
        "docsUrl": "",
    },
}


# Single capability catalogue for provider management and chat. Custom
# OpenAI-compatible providers remain owner-created, not universal aliases.
PROVIDER_CATALOGUE.update(
    {
        pid: {
            "name": spec.name,
            "category": "cloud",
            "docsUrl": spec.docs_url,
        }
        for pid, spec in SPECS.items()
        if pid not in PROVIDER_CATALOGUE
    }
)


def _mask_key(raw_key: str) -> str:
    """Mask an API key for display, keeping only a short prefix and suffix."""
    clean = raw_key.strip()
    if len(clean) <= 8:
        return "••••••••"
    return f"{clean[:4]}••••••••{clean[-4:]}"


_FAILED_STATUSES = frozenset(
    {"INVALID_KEY", "UPSTREAM_ERROR", "TIMEOUT", "RATE_LIMITED"}
)


def _to_item(
    provider_id: str,
    row: UserProviderCredential | None,
    custom_name: str | None = None,
    custom_category: str | None = None,
) -> AIProviderItem:
    resolved_custom_name = custom_name
    if (
        not resolved_custom_name
        and row
        and provider_id.startswith("prov-custom")
        and row.organization_id
    ):
        resolved_custom_name = row.organization_id

    meta = PROVIDER_CATALOGUE.get(
        provider_id,
        {
            "name": resolved_custom_name
            or (
                "Custom OpenAI-Compatible API"
                if provider_id.startswith("prov-custom")
                else provider_id
            ),
            "category": custom_category or "cloud",
        },
    )
    name = resolved_custom_name or str(meta["name"])
    category = custom_category or str(meta["category"])
    docs_url = str(meta["docsUrl"]) if meta.get("docsUrl") else None
    if row is None:
        return AIProviderItem(
            id=provider_id,
            name=name,
            category=category,  # type: ignore[arg-type]
            status="Not Connected",
            docsUrl=docs_url,
        )
    # Saved credentials are NOT live until explicitly verified.
    status_value = (
        "Connected"
        if row.validation_status == validator.VALID
        else "Unavailable"
        if row.validation_status in _FAILED_STATUSES
        else "Saved"
    )
    configured = row.created_at.astimezone(UTC).strftime("%b %d, %Y")
    return AIProviderItem(
        id=provider_id,
        name=name,
        category=category,  # type: ignore[arg-type]
        status=status_value,  # type: ignore[arg-type]
        configuredAt=configured,
        keyMasked=row.key_hint,
        baseUrl=row.base_url,
        organizationId=row.organization_id,
        docsUrl=docs_url,
    )


def _require_known_provider(provider_id: str) -> None:
    if provider_id not in PROVIDER_CATALOGUE and not provider_id.startswith(
        "prov-custom-"
    ):
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
    user_rows = await repo.list_for_user(current_user.id)
    rows = {r.provider_id: r for r in user_rows}
    items = [_to_item(pid, rows.get(pid)) for pid in PROVIDER_CATALOGUE]
    for r in user_rows:
        if r.provider_id not in PROVIDER_CATALOGUE:
            items.append(_to_item(r.provider_id, r))
    return items


@router.get(
    "/chat-models",
    summary="Discover user-owned verified chat models from supported BYOK APIs",
)
async def list_connected_chat_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Only verified, owner-scoped credentials may yield selectable models.

    A model listed here is authenticated and catalogued, not proof that a
    completion will succeed: quota and upstream availability can change.
    """
    repo = ProviderCredentialRepository(db)
    owned = {row.provider_id: row for row in await repo.list_for_user(current_user.id)}
    custom_ids = sorted(
        provider_id for provider_id in owned if provider_id.startswith("prov-custom-")
    )
    providers = (*SPECS, *custom_ids)
    # Concurrent bounded discovery: twenty saved provider keys must not turn
    # into minutes of serialized network timeouts. Ordering is deterministic.
    limiter = asyncio.Semaphore(6)

    async def discover_one(
        provider_id: str,
    ) -> tuple[dict[str, object], list[dict[str, str | int | bool]]]:
        row = owned.get(provider_id)
        provider_name = (
            row.organization_id if row and row.organization_id else None
        ) or str(PROVIDER_CATALOGUE.get(provider_id, {}).get("name") or provider_id)
        entry: dict[str, object] = {
            "providerId": provider_id,
            "name": provider_name,
            "status": "Not Connected"
            if row is None
            else (
                "Connected"
                if row.validation_status == validator.VALID
                else "Unavailable"
                if row.validation_status in _FAILED_STATUSES
                else "Saved"
            ),
            "keyMasked": row.key_hint if row else None,
            "modelsCount": 0,
        }
        available: list[dict[str, str | int | bool]] = []
        if row and row.validation_status == validator.VALID:
            try:
                key = decrypt_credential(settings, row.encrypted_api_key)
            except Exception:
                entry["status"] = "Unavailable"
                entry["message"] = "Saved credential cannot be read. Reconnect this provider."
                return entry, available
            try:
                async with limiter:
                    discovered = await fetch_chat_models(
                        provider_id,
                        key,
                        transport=_DISCOVERY_TRANSPORT.get(),
                        base_url=row.base_url,
                        provider_name=provider_name,
                    )
                available = [item.as_json() for item in discovered]
                entry["modelsCount"] = len(available)
                if not available:
                    entry["message"] = "No eligible text-chat models were discovered."
            except ModelDiscoveryError as exc:
                entry["status"] = "Unavailable"
                entry["message"] = str(exc)
        elif row:
            entry["message"] = (
                "Test the stored key before selecting models."
                if row.validation_status == "NOT_TESTED"
                else "Provider connection check failed. Test again."
            )
        return entry, available

    data = await asyncio.gather(
        *(discover_one(provider_id) for provider_id in providers)
    )
    return {
        "providers": [item for item, _ in data],
        "models": [model for _, batch in data for model in batch],
    }


class ChatModelProbeRequest(BaseModel):
    provider: str = Field(
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    model_name: str = Field(min_length=1, max_length=128)


@router.post("/chat-models/probe", summary="Perform a real BYOK completion smoke test")
async def probe_connected_chat_model(
    selection: ChatModelProbeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Only a successful nonempty completion qualifies for working-model status.

    Provider catalog presence and a verified key are necessary but not sufficient.
    This call consumes a small amount of the user's provider allowance.
    """
    if settings.RATE_LIMIT_ENABLED:
        enforce_rate_limit(
            http_request,
            action="model_probe",
            limit=12,
            window_seconds=60.0,
            user_id=str(current_user.id),
            settings=settings,
        )
    provider_id = credential_provider_id(selection.provider)
    if not is_supported_provider(provider_id):
        raise BadRequestError("Unknown BYOK model provider.")
    repo = ProviderCredentialRepository(db)
    row = await repo.get(current_user.id, provider_id)
    if not row or row.validation_status != validator.VALID:
        raise BadRequestError("Test and verify your own provider key first.")
    if selection.provider == "openrouter" and not selection.model_name.endswith(
        ":free"
    ):
        raise BadRequestError("Only explicit free OpenRouter routes are supported.")

    try:
        key = decrypt_credential(settings, row.encrypted_api_key)
    except Exception:
        return {"provider": selection.provider, "model": selection.model_name,
                "working": False, "status": "CREDENTIAL_UNREADABLE",
                "message": "Saved credential cannot be read. Reconnect this provider."}
    try:
        catalog = await fetch_chat_models(
            provider_id,
            key,
            transport=_DISCOVERY_TRANSPORT.get(),
            base_url=row.base_url,
            provider_name=row.organization_id,
        )
    except ModelDiscoveryError as exc:
        return {
            "provider": selection.provider,
            "model": selection.model_name,
            "working": False,
            "status": "CATALOG_UNAVAILABLE",
            "message": str(exc),
        }
    if selection.model_name not in {model.id for model in catalog}:
        raise BadRequestError("Model is not in the current eligible provider catalog.")

    model_selection = LLMModelSelection(
        provider=selection.provider,
        model_name=selection.model_name,
    )
    # This uses the same fully owner-scoped and native-protocol capable
    # executor as normal multi-model chat (no global key substitution).
    executor = await ChatService(
        db_session=db,
        settings=settings,
    )._owner_model_executor(
        str(current_user.id),
        ChatPromptRequest(
            prompt="Reply with one word: READY.",
            models=[model_selection],
            verify=False,
        ),
    )
    result = await executor.execute_models(
        prompt="Reply with one word: READY.",
        models=[model_selection],
        max_tokens=256,
    )
    tested = result[0]
    working = tested.status == "COMPLETED" and bool((tested.response or "").strip())
    return {
        "provider": selection.provider,
        "model": selection.model_name,
        "working": working,
        "status": "WORKING" if working else "UNAVAILABLE",
        "latency_ms": tested.latency_ms,
        "message": (
            "Completion test succeeded."
            if working
            else {
                "HTTP_400": "This model rejected the request settings. Try another chat model.",
                "HTTP_401": "Provider rejected your key. Reconnect this provider.",
                "HTTP_402": "This provider has insufficient credit or quota.",
                "HTTP_403": "Your key is not permitted to use this model.",
                "HTTP_404": "Model was not found or has been retired. Refresh models.",
                "HTTP_408": "Provider request timed out.",
                "HTTP_429": "Rate limit reached. Retry when your quota resets.",
                "HTTP_500": "Provider service error. Try another model.",
                "HTTP_502": "Provider service unavailable. Try another model.",
                "HTTP_503": "Provider service unavailable. Try another model.",
                "HTTP_504": "Provider service timed out. Try another model.",
                "NETWORK_FAILURE": "Backend could not reach the provider.",
                "EMPTY_RESPONSE": "No visible text was generated by this model.",
                "EMPTY_OUTPUT_BUDGET": "Model used its output budget before producing visible text.",
                "UNSAFE_ENDPOINT": "Configure a valid public HTTPS provider URL.",
            }.get(tested.error_code or "", "Model could not complete a text reply. Try another verified model.")
        ),
        "error_code": None if working else tested.error_code,
    }


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
    # A custom endpoint cannot be used to forward a key to local metadata,
    # VerifAI itself, or any internal network service.
    base_url = payload.baseUrl
    if provider_id in SPECS or provider_id.startswith("prov-custom-"):
        base_url = resolve_openai_base_url(
            provider_id, base_url, payload.name, resolve_dns=False
        )
    ciphertext = encrypt_credential(settings, payload.apiKey.strip())
    repo = ProviderCredentialRepository(db)
    org_id = (
        payload.name
        if (provider_id.startswith("prov-custom") and payload.name)
        else payload.organizationId
    )
    row = await repo.upsert(
        user_id=current_user.id,
        provider_id=provider_id,
        encrypted_api_key=ciphertext,
        key_hint=_mask_key(payload.apiKey),
        base_url=base_url,
        organization_id=org_id,
    )
    logger.info("Provider key saved: provider=%s user=%s", provider_id, current_user.id)
    return _to_item(
        provider_id, row, custom_name=payload.name, custom_category=payload.category
    )


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
    resolved_url = row.base_url
    if provider_id in SPECS or is_nvidia_connection(provider_id, row.organization_id):
        resolved_url = resolve_openai_base_url(
            provider_id,
            row.base_url,
            row.organization_id,
            resolve_dns=_CHECK_TRANSPORT.get() is None,
        )
    result = await validator.validate_api_key(
        provider_id,
        api_key,
        transport=_CHECK_TRANSPORT.get(),
        base_url=resolved_url,
    )
    if result.status == validator.VALID and resolved_url != row.base_url:
        row.base_url = resolved_url
    await repo.mark_validated(row, result.status)
    return ProviderTestResponse(
        id=provider_id,
        success=result.status == validator.VALID,
        status=result.status,
        message=result.message,
        latency_ms=result.latency_ms,
    )
