"""Pydantic v2 schemas for Chat, Conversations, Multi-LLM Execution, and History."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.verification import VerificationOptions, VerificationResponse


class ConversationCreateRequest(BaseModel):
    """Payload to create a new conversation thread."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=256,
        description="Descriptive title for the conversation.",
    )


class LLMModelSelection(BaseModel):
    """Configuration for an individual LLM target."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(
        min_length=1,
        max_length=64,
        description="Provider identifier: openai, anthropic, google, ollama, local",
    )
    model_name: str = Field(
        min_length=1,
        max_length=128,
        description="Model name, e.g. gpt-4o, claude-3-5-sonnet, gemini-1.5, llama3",
    )


class LLMRunResponse(BaseModel):
    """Schema representing an individual model execution result."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    message_id: uuid.UUID | None = None
    owner_id: str
    provider: str
    model_name: str
    model_version: str | None = None
    prompt: str
    response: str | None = None
    status: str = Field(
        description="PENDING, STREAMING, COMPLETED, FAILED, UNAVAILABLE"
    )
    started_at: datetime
    completed_at: datetime | None = None
    latency_ms: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    verification: VerificationResponse | None = None


class MessageResponse(BaseModel):
    """Schema representing a single message in a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    owner_id: str
    role: str
    content: str
    sequence_number: int
    created_at: datetime
    llm_runs: list[LLMRunResponse] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    """Summary representation of a conversation thread."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetailResponse(BaseModel):
    """Detailed conversation representation including message history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    """Paginated collection of conversation summaries."""

    total: int
    limit: int
    offset: int
    items: list[ConversationResponse]


class ChatPromptRequest(BaseModel):
    """User prompt dispatched to 1 to 3 LLMs with verification options."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        min_length=1,
        max_length=20000,
        description="The prompt or question to send to the selected models.",
    )
    models: list[LLMModelSelection] = Field(
        min_length=1,
        max_length=3,
        description="Selection of up to 3 LLMs to execute for this prompt.",
    )
    verify: bool = Field(
        default=True,
        description="Whether to run full VerifAI verification on model responses.",
    )
    options: VerificationOptions | None = Field(
        default=None,
        description="Optional verification tuning parameters.",
    )

    @field_validator("models")
    @classmethod
    def validate_models_count(
        cls, v: list[LLMModelSelection]
    ) -> list[LLMModelSelection]:
        if not (1 <= len(v) <= 3):
            raise ValueError("Exactly 1 to 3 models must be selected per prompt.")
        return v


class ChatPromptResponse(BaseModel):
    """Aggregated response containing runs for all selected models and verification."""

    conversation_id: uuid.UUID
    user_message_id: uuid.UUID
    prompt: str
    runs: list[LLMRunResponse]
    cross_model_disagreement: bool = False
    disagreement_summary: str | None = None


class UserDeleteDataResponse(BaseModel):
    """Response confirming purge of all user-owned data."""

    success: bool = True
    deleted_conversations: int = 0
    deleted_verifications: int = 0
    deleted_documents: int = 0
    message: str = "All user-owned data has been successfully deleted."


class AuditHistoryItem(BaseModel):
    """Schema representing an audit trail event."""

    id: uuid.UUID
    verification_id: uuid.UUID
    stage: str
    event_type: str
    status: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime


class AuditHistoryResponse(BaseModel):
    """Paginated list of audit events."""

    total: int
    limit: int
    offset: int
    items: list[AuditHistoryItem]
