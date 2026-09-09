"""Internal data structures shared across the verification engine.

These are pure Python dataclasses — no external dependencies.
They define the shapes that flow between engine components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Domain classification vocabulary
# ---------------------------------------------------------------------------


class Domain(str, Enum):
    """Controlled set of claim domains used for search/source routing."""

    GENERAL = "GENERAL"
    SCIENCE = "SCIENCE"
    TECHNOLOGY = "TECHNOLOGY"
    MEDICAL = "MEDICAL"
    FINANCE = "FINANCE"
    POLITICS = "POLITICS"
    HISTORY = "HISTORY"
    LAW = "LAW"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Judge vocabulary
# ---------------------------------------------------------------------------


class JudgeLabel(str, Enum):
    """LLM-as-judge consistency labels.

    ENTAILMENT   — evidence supports the claim.
    CONTRADICTION — evidence conflicts with the claim.
    ABSENT       — evidence does not determine support or contradiction.
    REFUSED      — judge cannot reliably perform the comparison.

    These are distinct from the final SUPPORT/CONTRADICT/UNKNOWN verdict.
    ABSENT != REFUSED != a judge exception (which is tracked separately).
    """

    ENTAILMENT = "ENTAILMENT"
    CONTRADICTION = "CONTRADICTION"
    ABSENT = "ABSENT"
    REFUSED = "REFUSED"


# ---------------------------------------------------------------------------
# Final verdict vocabulary
# ---------------------------------------------------------------------------


class Verdict(str, Enum):
    """Evidence-level final verdict returned to the user.

    SUPPORT      — strong evidence supports the claim.
    CONTRADICT   — strong evidence contradicts the claim.
    UNKNOWN      — insufficient or conflicting evidence.
    """

    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Engine data structures
# ---------------------------------------------------------------------------


@dataclass
class ExtractedClaim:
    """A single factual claim extracted from the user's input."""

    claim_id: str            # e.g. "claim_1"
    text: str                # the factual statement text
    position: int            # 1-indexed position in the input


@dataclass
class NormalizedSource:
    """A single web source after normalization and deduplication."""

    url: str
    title: str
    snippet: str             # search-returned excerpt / content summary
    domain: str              # hostname, e.g. "bbc.com"
    rank: int                # 1-indexed search rank
    query: str               # the search query that produced this source
    publication_date: Optional[str] = None


@dataclass
class ScoredSource:
    """A NormalizedSource with a computed quality score."""

    source: NormalizedSource
    quality_score: float     # deterministic, bounded [0.0, 1.0]


@dataclass
class JudgeResult:
    """Result of one LLM-as-judge call comparing a claim against one source."""

    label: JudgeLabel
    reason: str
    confidence: float        # model-reported confidence in [0.0, 1.0]
    source_url: str
    claim_id: str


@dataclass
class ClaimVerificationResult:
    """Full verification result for a single claim."""

    claim_id: str
    claim_text: str
    domain: Domain
    verdict: Verdict
    confidence: float        # formula-derived, [0.0, 1.0]; 0.5 = no signal
    signal_quality: float    # (e + k) / N; 0.0 when N = 0
    support_ratio: float     # e / N; 0.0 when N = 0
    reason: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    judge_results: List[Dict[str, Any]] = field(default_factory=list)
    entailment_count: int = 0
    contradiction_count: int = 0
    absent_count: int = 0
    refused_count: int = 0
    judge_error_count: int = 0


@dataclass
class EngineResult:
    """Top-level result produced by VerificationEngine.verify()."""

    # Aggregated across all claims
    verdict: Verdict
    trust_score: Decimal          # from confidence, rounded to 3dp
    evidence: List[Dict[str, Any]]  # serialisable for JSONB persistence
    reason: str

    # Per-claim breakdown (for provenance)
    claim_results: List[ClaimVerificationResult] = field(default_factory=list)

    # Observability counters
    claim_count: int = 0
    source_count: int = 0
    search_failure_count: int = 0
    judge_attempt_count: int = 0
    judge_failure_count: int = 0
