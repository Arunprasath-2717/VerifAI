"""Confidence calculation, conflict detection, and final verdict decision — Phase 2E Hardening.

Key Principles:
1. LLM provides evidence interpretation, NOT final authority.
2. Authority + Independence + Agreement determine trust.
3. Internal DISPUTED state: detects conflicting authoritative sources without majority-vote bias.
4. Distinguishes:
   A. LACK_OF_EVIDENCE
   B. CONFLICTING_EVIDENCE
   C. VERIFICATION_ERROR
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from app.engine.models import (
    AuthorityTier,
    ClaimVerificationResult,
    Domain,
    ExtractedClaim,
    JudgeLabel,
    JudgeResult,
    ScoredSource,
    SourceCluster,
    Verdict,
)

logger = logging.getLogger("verifai.engine.decision")

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

QUALITY_THRESHOLD: float = 0.65
CONFIDENCE_THRESHOLD: float = 0.65

_CAUSAL_INDICATORS = {
    "caused", "causes", "causing", "led to", "leads to", "induces",
    "induce", "resulted in", "results in", "triggered", "triggers",
}


@dataclass
class DecisionInput:
    """All the data the decision layer needs for a single claim."""

    claim: ExtractedClaim
    domain: Domain
    scored_sources: List[ScoredSource]
    judge_results: List[JudgeResult]
    judge_error_count: int
    source_clusters: Optional[List[SourceCluster]] = None
    search_failure: bool = False


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
    """Compute confidence, support_ratio, and signal_quality."""
    N = entailment_count + contradiction_count
    if N == 0:
        return 0.5, 0.0, 0.0
    e, k = entailment_count, contradiction_count
    confidence = ((e - k) / N + 1) / 2
    support_ratio = e / N
    signal_quality = (e + k) / N
    return (
        min(1.0, max(0.0, confidence)),
        min(1.0, max(0.0, support_ratio)),
        min(1.0, max(0.0, signal_quality)),
    )


def _is_strong(
    judge_result: JudgeResult,
    source_map: Dict[str, ScoredSource],
) -> bool:
    """Check if both source quality and judge confidence meet thresholds."""
    source = source_map.get(judge_result.source_url)
    if not source:
        return False
    return (
        source.quality_score >= QUALITY_THRESHOLD
        and judge_result.confidence >= CONFIDENCE_THRESHOLD
    )


def _is_causal_claim(claim_text: str) -> bool:
    """Check if the claim text explicitly asserts a causal relationship."""
    tokens = re.findall(r"\b[a-z0-9\s-]+\b", claim_text.lower())
    words = set(claim_text.lower().split())
    return any(c in words or c in claim_text.lower() for c in _CAUSAL_INDICATORS)


def decide(inp: DecisionInput) -> ClaimVerificationResult:
    """Produce the final ClaimVerificationResult enforcing Phase 2E hardening."""
    e, k, a, r = _count_labels(inp.judge_results)
    confidence, support_ratio, signal_quality = compute_confidence(e, k)

    source_map: Dict[str, ScoredSource] = {
        s.source.url: s for s in inp.scored_sources
    }

    # Track independent clusters
    cluster_map: Dict[str, str] = {}
    for s in inp.scored_sources:
        cluster_map[s.source.url] = s.cluster_id or s.source.domain

    diagnostics: Dict[str, Any] = {}
    is_disputed = False
    conflicting_authorities = False
    conflict_type: Optional[str] = None
    reason_category = "NORMAL"

    # 1. Check for Verification Infrastructure Failure
    if inp.judge_error_count > 0 and (e + k == 0):
        return ClaimVerificationResult(
            claim_id=inp.claim.claim_id,
            claim_text=inp.claim.text,
            domain=inp.domain,
            verdict=Verdict.UNKNOWN,
            confidence=0.5,
            signal_quality=0.0,
            support_ratio=0.0,
            reason="Verification infrastructure error during judging",
            reason_category="VERIFICATION_ERROR",
            conflict_type="VERIFICATION_ERROR",
            judge_error_count=inp.judge_error_count,
            sources=[s.source.__dict__ for s in inp.scored_sources],
            judge_results=[jr.__dict__ for jr in inp.judge_results],
        )

    # 2. Strong signals identification
    strong_support_judges = [
        jr for jr in inp.judge_results
        if jr.label == JudgeLabel.ENTAILMENT and _is_strong(jr, source_map)
    ]
    strong_contradict_judges = [
        jr for jr in inp.judge_results
        if jr.label == JudgeLabel.CONTRADICTION and _is_strong(jr, source_map)
    ]

    support_clusters = {
        cluster_map.get(jr.source_url, jr.source_url) for jr in strong_support_judges
    }
    contradict_clusters = {
        cluster_map.get(jr.source_url, jr.source_url) for jr in strong_contradict_judges
    }
    all_informative_clusters = {
        cluster_map.get(jr.source_url, jr.source_url)
        for jr in inp.judge_results
        if jr.label in (JudgeLabel.ENTAILMENT, JudgeLabel.CONTRADICTION)
    }

    independent_sources_count = len(all_informative_clusters)
    source_clusters_count = len(inp.source_clusters) if inp.source_clusters else len(all_informative_clusters)

    # Check Tier-1 / Tier-2 presence among strong signals
    support_authorities = {
        source_map[jr.source_url].source.domain
        for jr in strong_support_judges
        if source_map[jr.source_url].authority_tier in (
            AuthorityTier.TIER_1_INSTITUTIONAL, AuthorityTier.TIER_2_MAJOR_NEWS
        )
    }
    contradict_authorities = {
        source_map[jr.source_url].source.domain
        for jr in strong_contradict_judges
        if source_map[jr.source_url].authority_tier in (
            AuthorityTier.TIER_1_INSTITUTIONAL, AuthorityTier.TIER_2_MAJOR_NEWS
        )
    }

    # 3. Check for Causal Claim vs Correlation Evidence
    claim_is_causal = inp.claim.is_causal or _is_causal_claim(inp.claim.text)
    if claim_is_causal:
        diagnostics["causal_claim"] = True
        # If all entailment evidence indicates correlation rather than causal proof
        correlation_only = any(
            jr.evidence_type == "correlation" or jr.is_causal_support is False
            for jr in inp.judge_results
            if jr.label == JudgeLabel.ENTAILMENT
        )
        if correlation_only or not strong_support_judges:
            diagnostics["evidence_type"] = "correlation"
            diagnostics["causal_support"] = False
            return ClaimVerificationResult(
                claim_id=inp.claim.claim_id,
                claim_text=inp.claim.text,
                domain=inp.domain,
                verdict=Verdict.UNKNOWN,
                confidence=0.5,
                signal_quality=signal_quality,
                support_ratio=0.0,
                reason="Evidence demonstrates correlation, but fails to establish causation",
                reason_category="LACK_OF_EVIDENCE",
                diagnostics=diagnostics,
                independent_sources_count=independent_sources_count,
                source_clusters_count=source_clusters_count,
                sources=[s.source.__dict__ for s in inp.scored_sources],
                judge_results=[jr.__dict__ for jr in inp.judge_results],
                entailment_count=e,
                contradiction_count=k,
                absent_count=a,
                refused_count=r,
                judge_error_count=inp.judge_error_count,
            )

    # 4. Conflicting Authoritative Sources Check (DISPUTED STATE)
    if support_authorities and contradict_authorities:
        is_disputed = True
        conflicting_authorities = True
        conflict_type = "CONFLICTING_AUTHORITATIVE_SOURCES"
        reason_category = "CONFLICTING_EVIDENCE"
        verdict = Verdict.UNKNOWN
        reason = (
            f"Conflicting authoritative sources: support from {', '.join(sorted(support_authorities))} "
            f"vs contradiction from {', '.join(sorted(contradict_authorities))}"
        )

    # 5. General Conflicting Sources Check
    elif strong_support_judges and strong_contradict_judges:
        is_disputed = True
        conflict_type = "CONFLICTING_EVIDENCE"
        reason_category = "CONFLICTING_EVIDENCE"
        verdict = Verdict.UNKNOWN
        reason = "CONFLICTING_SOURCES"

    # 6. Strong Support Evaluation
    elif strong_support_judges:
        # Check authority / corroboration requirement
        has_tier1 = bool(support_authorities)
        has_multi_independent = len(support_clusters) >= 2

        if has_tier1 or has_multi_independent or len(support_clusters) >= 1:
            verdict = Verdict.SUPPORT
            reason = f"Strong entailment from {len(support_clusters)} independent source cluster(s)"
            reason_category = "NORMAL"
        else:
            verdict = Verdict.UNKNOWN
            reason = "Evidence below strong-evidence threshold"
            reason_category = "LACK_OF_EVIDENCE"

    # 7. Strong Contradiction Evaluation
    elif strong_contradict_judges:
        verdict = Verdict.CONTRADICT
        reason = f"Strong contradiction from {len(contradict_clusters)} independent source cluster(s)"
        reason_category = "NORMAL"

    # 8. Uninformative or Inconclusive Evidence
    else:
        verdict = Verdict.UNKNOWN
        reason_category = "LACK_OF_EVIDENCE"
        if e + k == 0:
            reason = "No informative evidence found"
        elif signal_quality < 0.3:
            reason = "Insufficient signal quality"
        else:
            reason = "Evidence below strong-evidence threshold"

    # Diagnostic metadata
    diagnostics.update({
        "is_disputed": is_disputed,
        "conflicting_authorities": conflicting_authorities,
        "conflict_type": conflict_type,
        "independent_clusters_count": len(all_informative_clusters),
    })

    return ClaimVerificationResult(
        claim_id=inp.claim.claim_id,
        claim_text=inp.claim.text,
        domain=inp.domain,
        verdict=verdict,
        confidence=confidence,
        signal_quality=signal_quality,
        support_ratio=support_ratio,
        reason=reason,
        is_disputed=is_disputed,
        conflict_type=conflict_type,
        conflicting_authorities=conflicting_authorities,
        reason_category=reason_category,
        independent_sources_count=independent_sources_count,
        source_clusters_count=source_clusters_count,
        diagnostics=diagnostics,
        sources=[s.source.__dict__ for s in inp.scored_sources],
        judge_results=[jr.__dict__ for jr in inp.judge_results],
        entailment_count=e,
        contradiction_count=k,
        absent_count=a,
        refused_count=r,
        judge_error_count=inp.judge_error_count,
    )
