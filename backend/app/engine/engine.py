"""Verification engine orchestrator — Phase 2D.

Entry point:

    result = await verification_engine.verify(claim_text, verification_id)

Orchestration flow:

    1. Extract claims (LLM or single-claim fallback)
    2. For each claim:
        a. Classify domain
        b. Build search query and fetch sources
        c. Normalize and score sources
        d. Judge each source vs the claim
        e. Compute confidence and verdict for this claim
    3. Aggregate across all claims
    4. Return EngineResult (ready for persistence)

Partial failure policy:
    - Extraction failure  → single-claim fallback
    - Classification failure → Domain.GENERAL fallback
    - Search failure → UNKNOWN for that claim, counted in search_failure_count
    - Individual judge call failure → tracked in judge_error_count, skipped
    - All judge calls fail → UNKNOWN result, no fabricated verdict
    - Engine-level exception → propagated to VerificationProcessingService
      which handles processing → failed transition
"""

from __future__ import annotations

import logging
import time
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.engine.classifier import DomainClassifier
from app.engine.decision import DecisionInput, decide
from app.engine.extractor import ClaimExtractor
from app.engine.judge import Judge, JudgeCallError
from app.engine.models import (
    ClaimVerificationResult,
    EngineResult,
    ScoredSource,
    Verdict,
)
from app.engine.providers import LLMProvider, SearchProvider, build_llm_provider, build_search_provider
from app.engine.scorer import score_source
from app.engine.searcher import SourceSearcher

logger = logging.getLogger("verifai.engine")


def _aggregate_verdict(claim_results: List[ClaimVerificationResult]) -> tuple[Verdict, str]:
    """Aggregate per-claim verdicts into a single top-level verdict.

    Rules (for multi-claim inputs):
    - Any UNKNOWN claim → overall UNKNOWN
    - All SUPPORT → SUPPORT
    - All CONTRADICT → CONTRADICT
    - Mix of SUPPORT and CONTRADICT → UNKNOWN (conflicting)
    - Empty → UNKNOWN
    """
    if not claim_results:
        return Verdict.UNKNOWN, "No claims processed"

    verdicts = {r.verdict for r in claim_results}

    if Verdict.UNKNOWN in verdicts:
        # Find the reason from the UNKNOWN claim(s)
        unknown_reasons = [r.reason for r in claim_results if r.verdict == Verdict.UNKNOWN]
        return Verdict.UNKNOWN, unknown_reasons[0] if unknown_reasons else "Inconclusive evidence"

    if verdicts == {Verdict.SUPPORT}:
        return Verdict.SUPPORT, "All claims supported by evidence"

    if verdicts == {Verdict.CONTRADICT}:
        return Verdict.CONTRADICT, "All claims contradicted by evidence"

    # Mix of SUPPORT and CONTRADICT
    return Verdict.UNKNOWN, "CONFLICTING_SOURCES across claims"


def _average_confidence(claim_results: List[ClaimVerificationResult]) -> float:
    """Simple average confidence across all claims."""
    if not claim_results:
        return 0.5
    return sum(r.confidence for r in claim_results) / len(claim_results)


def _build_evidence_payload(
    claim_results: List[ClaimVerificationResult],
) -> List[Dict[str, Any]]:
    """Build the JSONB-ready evidence list for persistence.

    Each item represents one claim's complete verification breakdown.
    """
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
    """Orchestrates the full verification pipeline for a single claim text.

    Designed for independence: the engine does not touch the database directly.
    Persistence is handled by the caller (VerificationProcessingService) using
    the existing update_verification() repository method.
    """

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
        """Run the full verification pipeline and return an EngineResult.

        Never returns a confident verdict without actual verification signal.
        Raises on unrecoverable errors (propagated to the processing service).
        """
        start_time = time.monotonic()

        logger.info("Engine starting for verification %s", verification_id)

        # ── 1. Extract claims ─────────────────────────────────────────────
        claims = await self._extractor.extract(claim_text)
        logger.info(
            "Extracted %d claim(s) from verification %s", len(claims), verification_id
        )

        # ── 2. Process each claim ─────────────────────────────────────────
        claim_results: List[ClaimVerificationResult] = []
        total_source_count = 0
        total_search_failures = 0
        total_judge_attempts = 0
        total_judge_failures = 0

        for claim in claims:
            # a. Domain classification
            domain = await self._classifier.classify(claim)

            # b. Search for sources
            try:
                raw_sources = await self._searcher.search_for_claim(claim)
            except Exception as exc:
                logger.warning(
                    "Search failed for claim %s in verification %s: %s",
                    claim.claim_id, verification_id, exc,
                )
                raw_sources = []
                total_search_failures += 1

            if not raw_sources:
                total_search_failures += 1
                # No sources → UNKNOWN for this claim
                claim_results.append(
                    ClaimVerificationResult(
                        claim_id=claim.claim_id,
                        claim_text=claim.text,
                        domain=domain,
                        verdict=Verdict.UNKNOWN,
                        confidence=0.5,
                        signal_quality=0.0,
                        support_ratio=0.0,
                        reason="No sources found for this claim",
                    )
                )
                continue

            # c. Score sources
            scored_sources: List[ScoredSource] = [score_source(s) for s in raw_sources]
            total_source_count += len(scored_sources)

            # d. Judge each source
            from app.engine.judge import JudgeResult
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

            # e. Compute verdict for this claim
            decision_input = DecisionInput(
                claim=claim,
                domain=domain,
                scored_sources=scored_sources,
                judge_results=judge_results,
                judge_error_count=judge_error_count,
            )
            claim_result = decide(decision_input)
            claim_results.append(claim_result)

        # ── 3. Aggregate ───────────────────────────────────────────────────
        top_verdict, top_reason = _aggregate_verdict(claim_results)
        avg_confidence = _average_confidence(claim_results)
        trust_score = Decimal(str(round(avg_confidence, 3)))
        evidence_payload = _build_evidence_payload(claim_results)

        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Engine completed verification %s in %.1fms: verdict=%s confidence=%.3f "
            "claims=%d sources=%d judge_attempts=%d judge_failures=%d",
            verification_id,
            duration_ms,
            top_verdict.value,
            avg_confidence,
            len(claims),
            total_source_count,
            total_judge_attempts,
            total_judge_failures,
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
