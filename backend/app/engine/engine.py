"""Verification Engine orchestrator — Phase 2E Hardening.

Integrates the full verification pipeline:
    Claim Extractor
      ↓
    Domain Classifier
      ↓
    Source Searcher
      ↓
    Source Normalization & Identity
      ↓
    Authority + Independence Clustering
      ↓
    Source Quality Scoring
      ↓
    LLM Judge (Evidence Interpretation)
      ↓
    Deterministic Calibration & Decision Matrix
      ↓
    Final Verdict & Rich Diagnostics

Key Invariants:
1. Multi-claim isolation: Each claim is independently verified; failure of one claim
   does not corrupt or invalidate another.
2. The LLM is strictly an evidence interpreter, NOT the final authority.
3. Does not write to DB directly; caller persists via VerificationRepository.
"""

from __future__ import annotations

import logging
import time
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.engine.classifier import DomainClassifier
from app.engine.decision import DecisionInput, decide
from app.engine.extractor import ClaimExtractor
from app.engine.independence import cluster_sources
from app.engine.judge import Judge, JudgeCallError
from app.engine.models import (
    ClaimVerificationResult,
    Domain,
    EngineResult,
    ExtractedClaim,
    JudgeResult,
    ScoredSource,
    Verdict,
)
from app.engine.providers import (
    LLMProvider,
    SearchProvider,
    build_llm_provider,
    build_search_provider,
)
from app.engine.scorer import score_source
from app.engine.searcher import SourceSearcher

logger = logging.getLogger("verifai.engine")


def _aggregate_verdict(
    claim_results: List[ClaimVerificationResult],
) -> Tuple[Verdict, str]:
    """Aggregate per-claim verdicts into a single top-level verdict."""
    if not claim_results:
        return Verdict.UNKNOWN, "No claims processed"

    verdicts = {r.verdict for r in claim_results}

    if Verdict.UNKNOWN in verdicts:
        unknown_reasons = [r.reason for r in claim_results if r.verdict == Verdict.UNKNOWN]
        return Verdict.UNKNOWN, unknown_reasons[0] if unknown_reasons else "Inconclusive evidence"

    if verdicts == {Verdict.SUPPORT}:
        return Verdict.SUPPORT, "All claims supported by evidence"

    if verdicts == {Verdict.CONTRADICT}:
        return Verdict.CONTRADICT, "All claims contradicted by evidence"

    return Verdict.UNKNOWN, "CONFLICTING_SOURCES across claims"


def _aggregate_diagnostics(
    claim_results: List[ClaimVerificationResult],
) -> Tuple[bool, Optional[str], str, bool, int]:
    """Aggregate diagnostic flags across all claim results.

    Returns:
        (is_disputed, conflict_type, reason_category, conflicting_authorities, total_independent)
    """
    if not claim_results:
        return False, None, "LACK_OF_EVIDENCE", False, 0

    is_disputed = any(r.is_disputed for r in claim_results)
    conflicting_authorities = any(r.conflicting_authorities for r in claim_results)
    total_independent = sum(r.independent_sources_count for r in claim_results)
    conflict_type = next((r.conflict_type for r in claim_results if r.conflict_type), None)

    if any(r.reason_category == "VERIFICATION_ERROR" for r in claim_results):
        reason_category = "VERIFICATION_ERROR"
    elif any(r.reason_category == "CONFLICTING_EVIDENCE" for r in claim_results) or is_disputed:
        reason_category = "CONFLICTING_EVIDENCE"
    elif all(r.verdict == Verdict.SUPPORT for r in claim_results) or all(r.verdict == Verdict.CONTRADICT for r in claim_results):
        reason_category = "NORMAL"
    else:
        reason_category = "LACK_OF_EVIDENCE"

    return is_disputed, conflict_type, reason_category, conflicting_authorities, total_independent


def _average_confidence(claim_results: List[ClaimVerificationResult]) -> float:
    """Simple average confidence across all claims."""
    if not claim_results:
        return 0.5
    return sum(r.confidence for r in claim_results) / len(claim_results)


def _build_evidence_payload(
    claim_results: List[ClaimVerificationResult],
) -> List[Dict[str, Any]]:
    """Build the JSONB-ready evidence list for persistence with rich Phase 2E diagnostics."""
    return [
        {
            "claim_id": cr.claim_id,
            "claim_text": cr.claim_text,
            "domain": cr.domain.value,
            "verdict": cr.verdict.value,
            "confidence": cr.confidence,
            "signal_quality": cr.signal_quality,
            "support_ratio": cr.support_ratio,
            "reason": cr.reason,
            "is_disputed": cr.is_disputed,
            "conflict_type": cr.conflict_type,
            "conflicting_authorities": cr.conflicting_authorities,
            "reason_category": cr.reason_category,
            "independent_sources_count": cr.independent_sources_count,
            "source_clusters_count": cr.source_clusters_count,
            "diagnostics": cr.diagnostics,
            "entailment_count": cr.entailment_count,
            "contradiction_count": cr.contradiction_count,
            "absent_count": cr.absent_count,
            "refused_count": cr.refused_count,
            "judge_error_count": cr.judge_error_count,
            "sources": cr.sources,
            "judge_results": cr.judge_results,
        }
        for cr in claim_results
    ]


class VerificationEngine:
    """Orchestrates the full verification pipeline for a claim text."""

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        search_provider: Optional[SearchProvider] = None,
        max_sources_per_claim: int = 5,
    ) -> None:
        self._extractor = ClaimExtractor(llm=llm)
        self._classifier = DomainClassifier(llm=llm)
        self._searcher = SourceSearcher(
            provider=search_provider or build_search_provider(),
            max_results_per_query=max_sources_per_claim,
        )
        self._judge = Judge(llm=llm)

    async def verify(
        self,
        claim_text: str,
        verification_id: uuid.UUID,
    ) -> EngineResult:
        """Run the full verification pipeline and return an EngineResult."""
        start_time = time.monotonic()
        logger.info("Engine starting for verification %s", verification_id)

        # ── 1. Extract claims ─────────────────────────────────────────────
        claims = await self._extractor.extract(claim_text)
        logger.info(
            "Extracted %d claim(s) from verification %s", len(claims), verification_id
        )

        # ── 2. Process each claim with isolation ──────────────────────────
        claim_results: List[ClaimVerificationResult] = []
        total_source_count = 0
        total_search_failures = 0
        total_judge_attempts = 0
        total_judge_failures = 0

        for claim in claims:
            # a. Domain classification
            domain = await self._classifier.classify(claim)

            # b. Search for sources
            search_failed = False
            try:
                raw_sources = await self._searcher.search_for_claim(claim)
                if getattr(self._searcher, "last_search_error", None):
                    search_failed = True
            except Exception as exc:
                logger.warning(
                    "Search failed for claim %s in verification %s: %s",
                    claim.claim_id, verification_id, exc,
                )
                raw_sources = []
                search_failed = True
                total_search_failures += 1

            if not raw_sources:
                total_search_failures += 1
                reason_cat = "VERIFICATION_ERROR" if search_failed else "LACK_OF_EVIDENCE"
                reason_msg = (
                    "Search provider error during evidence retrieval"
                    if search_failed
                    else "No sources found for this claim"
                )
                claim_results.append(
                    ClaimVerificationResult(
                        claim_id=claim.claim_id,
                        claim_text=claim.text,
                        domain=domain,
                        verdict=Verdict.UNKNOWN,
                        confidence=0.5,
                        signal_quality=0.0,
                        support_ratio=0.0,
                        reason=reason_msg,
                        reason_category=reason_cat,
                        conflict_type="VERIFICATION_ERROR" if search_failed else None,
                    )
                )
                continue

            # c. Score sources (with claim-level relevance)
            initial_scored: List[ScoredSource] = [
                score_source(s, claim_text=claim.text) for s in raw_sources
            ]

            # d. Source Independence & Syndication Clustering
            scored_sources, source_clusters = cluster_sources(initial_scored)
            total_source_count += len(scored_sources)

            # e. Judge each source
            judge_results: List[JudgeResult] = []
            judge_error_count = 0

            for ss in scored_sources:
                total_judge_attempts += 1
                try:
                    result = await self._judge.judge(claim, ss)
                    judge_results.append(result)
                except JudgeCallError as exc:
                    logger.warning(
                        "Judge call failed for claim %s / source %s: %s",
                        claim.claim_id, ss.source.url[:80], exc,
                    )
                    judge_error_count += 1
                    total_judge_failures += 1

            # f. Deterministic Calibration & Verdict Decision
            decision_input = DecisionInput(
                claim=claim,
                domain=domain,
                scored_sources=scored_sources,
                judge_results=judge_results,
                judge_error_count=judge_error_count,
                source_clusters=source_clusters,
                search_failure=search_failed,
            )
            claim_result = decide(decision_input)
            claim_results.append(claim_result)

        # ── 3. Aggregate ───────────────────────────────────────────────────
        top_verdict, top_reason = _aggregate_verdict(claim_results)
        (
            is_disputed,
            conflict_type,
            reason_category,
            conflicting_authorities,
            independent_count,
        ) = _aggregate_diagnostics(claim_results)

        avg_confidence = _average_confidence(claim_results)
        trust_score = Decimal(str(round(avg_confidence, 3)))
        evidence_payload = _build_evidence_payload(claim_results)

        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Engine completed verification %s in %.1fms: verdict=%s confidence=%.3f "
            "claims=%d sources=%d is_disputed=%s reason_cat=%s",
            verification_id,
            duration_ms,
            top_verdict.value,
            avg_confidence,
            len(claims),
            total_source_count,
            is_disputed,
            reason_category,
        )

        return EngineResult(
            verdict=top_verdict,
            trust_score=trust_score,
            evidence=evidence_payload,
            reason=top_reason,
            claim_results=claim_results,
            claim_count=len(claims),
            source_count=total_source_count,
            search_failure_count=total_search_failures,
            judge_attempt_count=total_judge_attempts,
            judge_failure_count=total_judge_failures,
            is_disputed=is_disputed,
            conflict_type=conflict_type,
            reason_category=reason_category,
            conflicting_authorities=conflicting_authorities,
            independent_sources_count=independent_count,
        )


# ---------------------------------------------------------------------------
# Singleton — built lazily from Settings at first import
# ---------------------------------------------------------------------------

def _build_engine() -> VerificationEngine:
    """Build the engine singleton from the current Settings."""
    llm = build_llm_provider()
    search = build_search_provider()
    return VerificationEngine(llm=llm, search_provider=search)


verification_engine: VerificationEngine = _build_engine()
