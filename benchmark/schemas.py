"""Pydantic data models and enums for the VerifAI Benchmark Suite."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkCategory(StrEnum):
    """PRD Section 8 benchmark categories."""

    VERIFIED_FACT = "VERIFIED_FACT"
    CONTROLLED_HALLUCINATION = "CONTROLLED_HALLUCINATION"
    TRUE_UNKNOWN = "TRUE_UNKNOWN"


class ContentType(StrEnum):
    """PRD Section 6 claim and content classifications."""

    FACTUAL = "FACTUAL"
    VIEWPOINT = "VIEWPOINT"
    FUTURE_LOOKING = "FUTURE_LOOKING"
    SCENARIO = "SCENARIO"
    CREATIVE = "CREATIVE"
    INSTRUCTION = "INSTRUCTION"
    MIXED = "MIXED"


class VerdictType(StrEnum):
    """PRD Section 6 & Section 10 verdict types."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"
    VIEWPOINT = "VIEWPOINT"
    FUTURE_LOOKING = "FUTURE_LOOKING"
    SCENARIO = "SCENARIO"
    CREATIVE = "CREATIVE"
    INSTRUCTION = "INSTRUCTION"
    INCONCLUSIVE = "INCONCLUSIVE"


class UnknownReason(StrEnum):
    """PRD Section 4 & Section 10 explicit UNKNOWN reason categories."""

    CONTEXT_UNKNOWN = "CONTEXT_UNKNOWN"
    SEARCH_UNKNOWN = "SEARCH_UNKNOWN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class ClaimLabel(StrEnum):
    """Gold and annotation labels for individual atomic claims."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class DatasetSplit(StrEnum):
    """Dataset partition splits for reproducible benchmarking."""

    TRAIN = "train"
    DEV = "dev"
    TEST = "test"


class DatasetStatus(StrEnum):
    """Lifecycle state of the benchmark dataset."""

    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    PASSED_QUALITY_GATE = "PASSED_QUALITY_GATE"
    FROZEN = "FROZEN"


class AnnotationPass(StrEnum):
    """Review cycle pass for annotation."""

    FIRST_PASS = "FIRST_PASS"
    SECOND_PASS = "SECOND_PASS"
    REMEDIATION_1 = "REMEDIATION_1"
    REMEDIATION_2 = "REMEDIATION_2"


class QualityGateStatus(StrEnum):
    """PRD Section 23.4 quality gate statuses."""

    INITIAL_REVIEW = "INITIAL_REVIEW"
    SECOND_PASS = "SECOND_PASS"
    REMEDIATION_1 = "REMEDIATION_1"
    REMEDIATION_2 = "REMEDIATION_2"
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class AtomicClaim(BaseModel):
    """An atomic, independently verifiable factual statement extracted from text."""

    claim_id: str = Field(description="Unique claim identifier within the case.")
    claim_text: str = Field(description="Normalized atomic proposition.")
    start_offset: int = Field(ge=0, description="Start character offset in response.")
    end_offset: int = Field(gt=0, description="End character offset in response.")
    gold_label: ClaimLabel = Field(description="Gold ground truth verification label.")
    expected_evidence: list[str] = Field(
        default_factory=list, description="Reference evidence queries or excerpts."
    )

    model_config = ConfigDict(extra="forbid")


class BenchmarkCase(BaseModel):
    """Single benchmark evaluation case conforming to PRD Section 8 requirements."""

    case_id: str = Field(description="Stable unique case identifier (e.g. CASE-001).")
    query: str = Field(description="Original user prompt or task.")
    response: str = Field(description="AI-generated text evaluated for hallucinations.")
    category: BenchmarkCategory = Field(
        description="Benchmark category (VERIFIED_FACT, CONTROLLED_HALLUCINATION, TRUE_UNKNOWN).",  # noqa: E501
    )
    content_type: ContentType = Field(
        default=ContentType.FACTUAL,
        description="Content classification (FACTUAL, VIEWPOINT, etc.).",
    )
    expected_verdict: VerdictType = Field(
        description="Overall expected verification verdict."
    )
    unknown_reason: UnknownReason | None = Field(
        default=None,
        description="Specific reason when verdict is UNKNOWN.",
    )
    atomic_claims: list[AtomicClaim] = Field(
        default_factory=list,
        description="List of atomic claims extracted from the response.",
    )
    split: DatasetSplit = Field(
        default=DatasetSplit.TRAIN,
        description="Dataset partition (train, dev, test).",
    )
    dataset_version: str = Field(
        default="dataset_v1", description="Dataset semantic version."
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Metadata on source generation."
    )
    notes: str = Field(
        default="", description="Annotation notes, rationale, or ambiguity details."
    )

    model_config = ConfigDict(extra="forbid")


class ClaimAnnotation(BaseModel):
    """Individual annotator judgment for an atomic claim."""

    case_id: str
    claim_id: str
    annotator_id: str
    label: ClaimLabel
    pass_type: AnnotationPass = AnnotationPass.FIRST_PASS
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class DatasetManifest(BaseModel):
    """Metadata manifest emitted upon dataset validation and freeze."""

    dataset_name: str
    version: str
    status: DatasetStatus
    checksum_sha256: str
    total_cases: int
    category_breakdown: dict[str, int]
    claim_count: int
    split_counts: dict[str, int]
    kappa_score: float | None = None
    created_at: str
    frozen_at: str | None = None

    model_config = ConfigDict(extra="forbid")
