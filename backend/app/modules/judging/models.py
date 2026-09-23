"""Data models for independent judge evaluations and disagreement analysis."""

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.schemas.verification import JudgeDecision, UnknownReason, VerdictType


@dataclass(frozen=True)
class JudgeEvaluationData:
    """Individual evaluation of a claim by a single judge."""

    judge_id: uuid.UUID = field(default_factory=uuid.uuid4)
    judge_name: str = "Judge"
    model_version: str | None = None
    judgment: JudgeDecision = JudgeDecision.UNKNOWN
    confidence: float | None = None
    rationale: str | None = None
    evidence_references: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DisagreementResult:
    """Outcome of multi-judge consensus and conflict arbitration."""

    consensus_verdict: VerdictType
    has_disagreement: bool
    disagreement_details: str | None
    unknown_reason: UnknownReason | None
    judge_evaluations: list[JudgeEvaluationData]
    degraded_evaluation: bool = False
    judges_used: int = 2
    third_judge_invoked: bool = False
    arbitration_reason: str | None = None
