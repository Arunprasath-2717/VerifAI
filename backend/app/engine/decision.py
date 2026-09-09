"""Confidence calculation and final verdict decision — Phase 2D.

Formulas (approved by project specification):

    confidence = ((e - k) / N + 1) / 2
    support_ratio = e / N
    signal_quality = (e + k) / N

where:
    e = ENTAILMENT count
    k = CONTRADICTION count
    N = informative judge samples (ENTAILMENT + CONTRADICTION)
      ABSENT and REFUSED do not contribute to N

When N = 0:
    confidence = 0.5   ← no signal; must NOT be described as "50% true"
    signal_quality = 0.0

Verdict mapping (strong-evidence-first principle):

    Both strong SUPPORT and strong CONTRADICT signals → UNKNOWN (CONFLICTING_SOURCES)
    Strong SUPPORT (quality + confidence ≥ threshold) → SUPPORT
    Strong CONTRADICT (quality + confidence ≥ threshold) → CONTRADICT
    Everything else → UNKNOWN

Strong evidence thresholds (configurable):
    source_quality ≥ QUALITY_THRESHOLD
    judge confidence ≥ CONFIDENCE_THRESHOLD

TODO(calibration): Validate these thresholds against ECE and a labeled benchmark.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.engine.models import (
    ClaimVerificationResult,
    Domain,
    ExtractedClaim,
    JudgeLabel,
    JudgeResult,
    ScoredSource,
    Verdict,
)

logger = logging.getLogger("verifai.engine.decision")

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

# A source must score at least this quality to be considered "strong".
QUALITY_THRESHOLD: float = 0.70

# A judge must report at least this confidence to be considered "strong".
CONFIDENCE_THRESHOLD: float = 0.70


@dataclass
class DecisionInput:
    """All the data the decision layer needs for a single claim."""

    claim: ExtractedClaim
    domain: Domain
    scored_sources: List[ScoredSource]
    judge_results: List[JudgeResult]
    judge_error_count: int


def _count_labels(results: List[JudgeResult]) -> Tuple[int, int, int, int]:
    """Return (entailment, contradiction, absent, refused) counts."""
    e = sum(1 for r in results if r.label == JudgeLabel.ENTAILMENT)
    k = sum(1 for r in results if r.label == JudgeLabel.CONTRADICTION)
    a = sum(1 for r in results if r.label == JudgeLabel.ABSENT)
    r = sum(1 for r in results if r.label == JudgeLabel.REFUSED)
    return e, k, a, r


def compute_confidence(
    entailment_count: int,
    contradiction_count: int,
) -> Tuple[float, float, float]:
    """Compute confidence, support_ratio, and signal_quality.

    Returns (confidence, support_ratio, signal_quality).
    All values are in [0.0, 1.0].
    """
    N = entailment_count + contradiction_count
    if N == 0:
        return 0.5, 0.0, 0.0
    e, k = entailment_count, contradiction_count
    confidence = ((e - k) / N + 1) / 2
    support_ratio = e / N
    signal_quality = (e + k) / N  # always 1.0 when N > 0 by definition
    return (
        min(1.0, max(0.0, confidence)),
        min(1.0, max(0.0, support_ratio)),
        min(1.0, max(0.0, signal_quality)),
    )


def _is_strong(
    judge_result: JudgeResult,
    scored_sources: List[ScoredSource],
) -> bool:
    """Return True when this judge result and its source both meet thresholds."""
    source_quality = next(
        (s.quality_score for s in scored_sources if s.source.url == judge_result.source_url),
        0.0,
    )
    return (
        source_quality >= QUALITY_THRESHOLD
        and judge_result.confidence >= CONFIDENCE_THRESHOLD
    )


def decide(inp: DecisionInput) -> ClaimVerificationResult:
    """Produce the final ClaimVerificationResult for a single claim.

    Decision policy (strong-evidence-first):
    1. Identify strong ENTAILMENT and strong CONTRADICTION signals.
    2. If BOTH exist → UNKNOWN (CONFLICTING_SOURCES).
    3. If only strong ENTAILMENT → SUPPORT.
    4. If only strong CONTRADICT → CONTRADICT.
    5. Otherwise → UNKNOWN.
    """
    e, k, a, r = _count_labels(inp.judge_results)
    confidence, support_ratio, signal_quality = compute_confidence(e, k)

    # Identify strong signals
    strong_support = [
        jr for jr in inp.judge_results
        if jr.label == JudgeLabel.ENTAILMENT and _is_strong(jr, inp.scored_sources)
    ]
    strong_contradict = [
        jr for jr in inp.judge_results
        if jr.label == JudgeLabel.CONTRADICTION and _is_strong(jr, inp.scored_sources)
    ]

    # --- Apply decision policy ---
    if strong_support and strong_contradict:
        verdict = Verdict.UNKNOWN
        reason = "CONFLICTING_SOURCES"
    elif strong_support:
        verdict = Verdict.SUPPORT
        reason = f"Strong entailment from {len(strong_support)} source(s)"
    elif strong_contradict:
        verdict = Verdict.CONTRADICT
        reason = f"Strong contradiction from {len(strong_contradict)} source(s)"
    else:
        verdict = Verdict.UNKNOWN
        if e + k == 0:
            reason = "No informative evidence found"
        elif signal_quality < 0.3:
            reason = "Insufficient signal quality"
        else:
            reason = "Evidence below strong-evidence threshold"

    sources_dicts = [
        {
            "url": ss.source.url,
            "title": ss.source.title,
            "domain": ss.source.domain,
            "quality_score": ss.quality_score,
            "rank": ss.source.rank,
            "query": ss.source.query,
            "publication_date": ss.source.publication_date,
        }
        for ss in inp.scored_sources
    ]
    judge_dicts = [
        {
            "claim_id": jr.claim_id,
            "source_url": jr.source_url,
            "label": jr.label.value,
            "reason": jr.reason,
            "confidence": jr.confidence,
        }
        for jr in inp.judge_results
    ]

    return ClaimVerificationResult(
        claim_id=inp.claim.claim_id,
        claim_text=inp.claim.text,
        domain=inp.domain,
        verdict=verdict,
        confidence=confidence,
        signal_quality=signal_quality,
        support_ratio=support_ratio,
        reason=reason,
        sources=sources_dicts,
        judge_results=judge_dicts,
        entailment_count=e,
        contradiction_count=k,
        absent_count=a,
        refused_count=r,
        judge_error_count=inp.judge_error_count,
    )
