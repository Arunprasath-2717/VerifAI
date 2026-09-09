"""Internal data structures shared across the verification engine.

These are pure Python dataclasses — no external dependencies.
They define the shapes that flow between engine components.
Phase 2E adds AuthorityTier, SourceCluster, and rich adversarial diagnostics.
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
# Source Authority Tiers (Phase 2E)
# ---------------------------------------------------------------------------


class AuthorityTier(str, Enum):
    """Classification of source authority as an initial prior.

    Note: Domain tier is a strong prior, NOT an absolute proof of factual truth.
    """

    TIER_1_INSTITUTIONAL = "TIER_1_INSTITUTIONAL"  # Peer-reviewed, gov, academic, IFCN fact-checkers (0.85-0.95 prior)
    TIER_2_MAJOR_NEWS = "TIER_2_MAJOR_NEWS"          # Established news with editorial boards (0.75-0.82 prior)
    TIER_3_COLLABORATIVE = "TIER_3_COLLABORATIVE"    # Wikipedia, StackOverflow, GitHub (0.60-0.70 prior)
    TIER_4_GENERAL_WEB = "TIER_4_GENERAL_WEB"        # General web (default 0.40 prior)
    TIER_5_UNRELIABLE = "TIER_5_UNRELIABLE"          # Content farms, tabloids, known spam (0.10-0.20 prior)


# ---------------------------------------------------------------------------
# Judge vocabulary
# ---------------------------------------------------------------------------


class JudgeLabel(str, Enum):
    """LLM-as-judge consistency labels.

    ENTAILMENT    — evidence supports the claim.
    CONTRADICTION — evidence conflicts with the claim.
    ABSENT        — evidence does not determine support or contradiction.
    REFUSED       — judge cannot reliably perform the comparison.

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
    UNKNOWN      — insufficient, conflicting, or unverified evidence.
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
    is_negated: bool = False
    is_numerical: bool = False
    is_temporal: bool = False
    is_causal: bool = False


@dataclass
class NormalizedSource:
    """A single web source after normalization, identity resolution, and metadata extraction."""

    url: str
    title: str
    snippet: str             # search-returned excerpt / content summary
    domain: str              # hostname, e.g. "news.bbc.co.uk"
    rank: int                # 1-indexed search rank
    query: str               # the search query that produced this source
    publication_date: Optional[str] = None

    # Phase 2E Identity & Fingerprint Metadata
    root_domain: Optional[str] = None         # e.g. "bbc.co.uk"
    publisher: Optional[str] = None           # e.g. "BBC News"
    author: Optional[str] = None
    original_publisher: Optional[str] = None  # e.g. "Reuters" if republished by Yahoo
    wire_attribution: Optional[str] = None    # "Reuters", "AP", "AFP", etc.
    article_fingerprint: Optional[str] = None # lexical / token fingerprint
    cluster_id: Optional[str] = None          # group ID for syndicated / duplicate copies


@dataclass
class SourceCluster:
    """A cluster of sources sharing the same origin, wire attribution, or duplicate content."""

    cluster_id: str
    primary_source_url: str
    member_urls: List[str]
    root_domain: str
    wire_attribution: Optional[str] = None
    representative_quality: float = 0.5
    effective_weight: float = 1.0             # Cluster weight (down-weights redundant syndicated copies to 1 signal)


@dataclass
class ScoredSource:
    """A NormalizedSource with authority, relevance, freshness, and independence scores."""

    source: NormalizedSource
    quality_score: float                      # deterministic composite, bounded [0.0, 1.0]

    # Phase 2E sub-scores
    authority_tier: AuthorityTier = AuthorityTier.TIER_4_GENERAL_WEB
    authority_score: float = 0.40             # prior based on publisher / domain tier
    relevance_score: float = 0.50             # claim-to-snippet semantic/entity overlap
    freshness_score: float = 0.50             # temporal validity & publication recency
    independence_score: float = 1.0           # discount factor if part of redundant syndication cluster
    cluster_id: Optional[str] = None


@dataclass
class JudgeResult:
    """Result of one LLM-as-judge call comparing a claim against one source."""

    label: JudgeLabel
    reason: str
    confidence: float        # model-reported confidence in [0.0, 1.0]
    source_url: str
    claim_id: str
    evidence_snippet: Optional[str] = None
    evidence_type: Optional[str] = None       # e.g. "direct_quote", "correlation", "statistical_data"
    is_causal_support: Optional[bool] = None


@dataclass
class ClaimVerificationResult:
    """Full verification result for a single claim with rich diagnostics."""

    claim_id: str
    claim_text: str
    domain: Domain
    verdict: Verdict
    confidence: float        # formula-derived, [0.0, 1.0]; 0.5 = no signal
    signal_quality: float    # (e + k) / N; 0.0 when N = 0
    support_ratio: float     # e / N; 0.0 when N = 0
    reason: str

    # Source and judge details
    sources: List[Dict[str, Any]] = field(default_factory=list)
    judge_results: List[Dict[str, Any]] = field(default_factory=list)
    entailment_count: int = 0
    contradiction_count: int = 0
    absent_count: int = 0
    refused_count: int = 0
    judge_error_count: int = 0

    # Phase 2E Hardening & Diagnostics
    is_disputed: bool = False
    conflict_type: Optional[str] = None       # CONFLICTING_AUTHORITATIVE_SOURCES, CONFLICTING_EVIDENCE, etc.
    conflicting_authorities: bool = False
    reason_category: str = "NORMAL"          # NORMAL, LACK_OF_EVIDENCE, CONFLICTING_EVIDENCE, VERIFICATION_ERROR
    independent_sources_count: int = 0
    source_clusters_count: int = 0
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """Top-level result produced by VerificationEngine.verify()."""

    # Aggregated across all claims
    verdict: Verdict
    trust_score: Decimal                      # from confidence, rounded to 3dp
    evidence: List[Dict[str, Any]]            # serialisable for JSONB persistence
    reason: str

    # Per-claim breakdown (for provenance)
    claim_results: List[ClaimVerificationResult] = field(default_factory=list)

    # Observability counters
    claim_count: int = 0
    source_count: int = 0
    search_failure_count: int = 0
    judge_attempt_count: int = 0
    judge_failure_count: int = 0

    # Phase 2E High-level Diagnostics
    is_disputed: bool = False
    conflict_type: Optional[str] = None
    reason_category: str = "NORMAL"          # NORMAL, LACK_OF_EVIDENCE, CONFLICTING_EVIDENCE, VERIFICATION_ERROR
    conflicting_authorities: bool = False
    independent_sources_count: int = 0
