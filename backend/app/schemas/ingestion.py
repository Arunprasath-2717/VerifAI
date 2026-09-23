"""Pydantic v2 schemas for payload ingestion and browser extension integration."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.verification import (
    VerificationOptions,
    VerificationResponse,
)


class IngestionSource(StrEnum):
    """Origin source of the ingested content payload."""

    CHROME_EXTENSION = "CHROME_EXTENSION"
    WEB_CHAT = "WEB_CHAT"
    API_CLIENT = "API_CLIENT"
    MCP = "MCP"
    OTHER = "OTHER"


class IngestionStatus(StrEnum):
    """Lifecycle status of an ingested payload."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class IngestionPayloadRequest(BaseModel):
    """Request schema for ingesting AI-generated content."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="Captured AI-generated text response to be verified.",
        examples=["The Eiffel Tower is in Paris, France."],
    )
    prompt: str | None = Field(
        default=None,
        max_length=5000,
        description="Original user prompt that generated this response.",
        examples=["Where is the Eiffel Tower located?"],
    )
    source_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Web URL where the response was captured.",
        examples=["https://chatgpt.com/c/12345"],
    )
    model_name: str | None = Field(
        default=None,
        max_length=128,
        description="Reported or detected LLM model name.",
        examples=["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"],
    )
    source: IngestionSource = Field(
        default=IngestionSource.CHROME_EXTENSION,
        description="Ingestion channel or client type.",
    )
    session_id: str | None = Field(
        default=None,
        max_length=128,
        description="Optional client session or conversation identifier.",
    )
    client_version: str | None = Field(
        default=None,
        max_length=32,
        description="Version of the ingestion client or extension.",
        examples=["1.0.0"],
    )
    capture_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional capture context (browser, OS, viewport).",
    )
    options: VerificationOptions = Field(
        default_factory=VerificationOptions,
        description="Verification execution options.",
    )
    verify_immediately: bool = Field(
        default=True,
        description="Run verification pipeline immediately and return results.",
    )

    @field_validator("text", mode="after")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        """Ensure ingested text contains non-whitespace content."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Ingested text cannot be empty or whitespace-only.")
        return stripped

    @field_validator("source_url", mode="after")
    @classmethod
    def validate_url_scheme(cls, v: str | None) -> str | None:
        """Validate URL scheme if provided."""
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not (trimmed.startswith("http://") or trimmed.startswith("https://")):
            raise ValueError("source_url must use http or https scheme.")
        return trimmed


class IngestionResponse(BaseModel):
    """Response schema for payload ingestion."""

    model_config = ConfigDict(from_attributes=True)

    ingestion_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the ingested payload record.",
    )
    source: IngestionSource = Field(
        ...,
        description="Origin source of the payload.",
    )
    status: IngestionStatus = Field(
        ...,
        description="Processing status of the ingested payload.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the payload was received.",
    )
    model_name: str | None = Field(
        default=None,
        description="Detected or reported LLM model name.",
    )
    source_url: str | None = Field(
        default=None,
        description="Sanitized source URL where the text was captured.",
    )
    verification_id: uuid.UUID | None = Field(
        default=None,
        description="ID of the associated verification job, if verified.",
    )
    verification: VerificationResponse | None = Field(
        default=None,
        description="Complete verification outcome if verify_immediately was True.",
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if ingestion or verification failed.",
    )
