"""Pydantic v2 schemas for VerifAI verification requests and domain entities."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerificationStatus(StrEnum):
    """Lifecycle status of a verification job."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"


class ContentType(StrEnum):
    """PRD Section 6 claim and content classifications."""

    FACTUAL = "FACTUAL"
    OPINION = "OPINION"
    PREDICTION = "PREDICTION"
    HYPOTHETICAL = "HYPOTHETICAL"
    CREATIVE = "CREATIVE"
    INSTRUCTION = "INSTRUCTION"
    MIXED = "MIXED"


class VerdictType(StrEnum):
    """PRD Section 6 & Section 10 factual verdict outcomes.

    The factual verdict contract is strictly three values:
    SUPPORTED, CONTRADICTED, UNKNOWN.
    Non-factual content types are recorded separately in ContentType
    and receive verdict = None.
    """

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class UnknownReason(StrEnum):
    """Explicit UNKNOWN reason classifications."""

    CONTEXT_UNKNOWN = "CONTEXT_UNKNOWN"
    SEARCH_UNKNOWN = "SEARCH_UNKNOWN"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class JudgeDecision(StrEnum):
    """Individual judge evaluation output states."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"


class VerificationOptions(BaseModel):
    """Execution options for verification pipeline."""

    model_config = ConfigDict(extra="forbid")

    enable_live_search: bool = Field(
        default=False,
        description="Whether to attempt live search (requires network/provider).",
    )
    max_claims: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum atomic claims to extract and verify.",
    )
    strict_consensus: bool = Field(
        default=True,
        description="Contradictory signals immediately flag hallucination risk.",
    )


class VerificationCreateRequest(BaseModel):
    """Request payload for starting a verification job."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="AI-generated text response to be decomposed and verified.",
    )
    query: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional original user prompt or query context.",
    )
    options: VerificationOptions = Field(
        default_factory=VerificationOptions,
        description="Verification execution options.",
    )

    @field_validator("text", mode="after")
    @classmethod
    def validate_non_whitespace(cls, v: str) -> str:
        """Reject empty or whitespace-only input."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Input text cannot be empty or whitespace only.")
        return v


class EvidenceSchema(BaseModel):
    """Retrieved evidence passage with source provenance."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str | None = None
    source_title: str | None = None
    publisher: str | None = None
    publication_date: str | None = None
    snippet: str
    retriever_name: str
    relevance_score: float | None = None
    authority_score: float | None = None


class JudgeEvaluationSchema(BaseModel):
    """Evaluation produced by an independent judge."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judge_name: str
    judgment: str
    confidence: float | None = None
    rationale: str | None = None
    evidence_references: list[str] | None = None


class ClaimResultSchema(BaseModel):
    """Verification result for an individual atomic claim."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_index: int
    claim_text: str
    start_offset: int
    end_offset: int
    content_type: str
    verdict: VerdictType | None = None
    is_verifiable: bool = True
    confidence: float | None = None
    is_calibrated: bool = False
    calibration_status: str = "NOT_CALIBRATED"
    unknown_reason: str | None = None
    explanation: str | None = None
    degraded_evaluation: bool = False
    arbitration_reason: str | None = None
    evidence: list[EvidenceSchema] = Field(default_factory=list)
    judges: list[JudgeEvaluationSchema] = Field(default_factory=list)


class AuditRecordSchema(BaseModel):
    """Audit log entry for a verification lifecycle event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stage: str
    event_type: str
    status: str
    message: str
    timestamp: datetime


class VerificationResponse(BaseModel):
    """Full verification envelope returned by API."""

    model_config = ConfigDict(from_attributes=True)

    verification_id: uuid.UUID
    status: str
    input_text: str
    query: str | None = None
    content_type: str
    total_claims: int = 0
    supported_claims: int = 0
    contradicted_claims: int = 0
    unknown_claims: int = 0
    non_factual_claims: int = 0
    trust_score: float | None = None
    calibrated_confidence: float | None = None
    is_calibrated: bool = False
    calibration_status: str = "NOT_CALIBRATED"
    degraded_evaluation: bool = False
    summary: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    claims: list[ClaimResultSchema] = Field(default_factory=list)
    audit_trail: list[AuditRecordSchema] = Field(default_factory=list)
