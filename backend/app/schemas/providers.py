"""Schemas for AI provider management and secure key configuration."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AIProviderItem(BaseModel):
    """Safe metadata representation of an AI provider."""

    id: str
    name: str
    category: Literal["cloud", "local", "router"]
    status: Literal["Connected", "Saved", "Not Connected", "Unavailable", "Error"]
    models: list[str] = Field(default_factory=list)
    configuredAt: str | None = None
    keyMasked: str | None = None
    baseUrl: str | None = None
    organizationId: str | None = None
    keyLabel: str | None = None
    docsUrl: str | None = None


class ProviderSaveKeyRequest(BaseModel):
    """Payload for linking an API key to an inference provider."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    apiKey: str = Field(
        min_length=1,
        max_length=512,
        validation_alias=AliasChoices("apiKey", "api_key"),
    )
    keyMasked: str | None = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices("keyMasked", "key_masked"),
    )
    baseUrl: str | None = Field(
        default=None,
        max_length=512,
        validation_alias=AliasChoices("baseUrl", "base_url"),
    )
    organizationId: str | None = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices("organizationId", "organization_id"),
    )
    keyLabel: str | None = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices("keyLabel", "key_label"),
    )
    name: str | None = Field(default=None, max_length=128)
    models: list[str] = Field(default_factory=list)
    category: Literal["cloud", "local", "router"] = "cloud"


class ProviderTestResponse(BaseModel):
    """Response payload when pinging or validating an AI provider."""

    id: str
    success: bool
    status: str
    message: str
    latency_ms: int = 0
