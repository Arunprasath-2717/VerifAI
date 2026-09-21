"""Document-level decision aggregation and trust-score calculation engine."""

from dataclasses import dataclass
from typing import Any

from app.schemas.verification import ContentType, VerdictType


@dataclass(frozen=True)
class DocumentDecisionSummary:
    """Aggregated document-level verification outcome."""

    total_claims: int
    supported_claims: int
    contradicted_claims: int
    unknown_claims: int
    non_factual_claims: int
    content_type: ContentType
    trust_score: float | None
    calibrated_confidence: float | None
    is_calibrated: bool
    calibration_status: str
    summary_text: str


class DecisionEngine:
    """Computes document-level trust score and verdict summary."""

    def aggregate(
        self,
        claims: list[dict[str, Any]],
    ) -> DocumentDecisionSummary:
        """Aggregate claim outcomes into an overall trust score and summary."""
        total = len(claims)
        if total == 0:
            return DocumentDecisionSummary(
                total_claims=0,
                supported_claims=0,
                contradicted_claims=0,
                unknown_claims=0,
                non_factual_claims=0,
                content_type=ContentType.FACTUAL,
                trust_score=None,
                calibrated_confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                summary_text="No claims extracted from input text.",
            )

        supported = sum(1 for c in claims if c.get("verdict") == VerdictType.SUPPORTED)
        contradicted = sum(
            1 for c in claims if c.get("verdict") == VerdictType.CONTRADICTED
        )
        unknown = sum(1 for c in claims if c.get("verdict") == VerdictType.UNKNOWN)
        non_factual = sum(
            1
            for c in claims
            if c.get("verdict") is None or not c.get("is_verifiable", True)
        )

        factual_count = supported + contradicted + unknown

        # Overall content classification
        if non_factual == total:
            overall_type = ContentType.OPINION  # or dominant non-factual type
        elif non_factual > 0 and factual_count > 0:
            overall_type = ContentType.MIXED
        else:
            overall_type = ContentType.FACTUAL

        # Trust score calculation
        if factual_count == 0:
            trust_score = None
            summary = (
                f"Input contains {non_factual} non-verifiable claims "
                "(opinions, scenarios, or predictions). Empirical trust score "
                "is not applicable."
            )
        elif contradicted > 0:
            # Conservative safety penalty: any contradiction flags hallucination risk
            trust_score = 0.0
            summary = (
                f"Hallucination risk detected: {contradicted} of {factual_count} "
                "factual claims contradicted by verified evidence. "
                "Trust score set to 0.0%."
            )
        elif supported == factual_count:
            trust_score = 100.0
            summary = (
                f"All {supported} factual claims were fully supported by "
                "verified evidence. Trust score: 100.0%."
            )
        else:
            # Partial support, remainder unknown
            trust_score = round((supported / factual_count) * 100.0, 1)
            summary = (
                f"{supported} of {factual_count} factual claims supported; "
                f"{unknown} claims had insufficient or inconclusive evidence. "
                f"Trust score: {trust_score}%."
            )

        return DocumentDecisionSummary(
            total_claims=total,
            supported_claims=supported,
            contradicted_claims=contradicted,
            unknown_claims=unknown,
            non_factual_claims=non_factual,
            content_type=overall_type,
            trust_score=trust_score,
            calibrated_confidence=None,
            is_calibrated=False,
            calibration_status="NOT_CALIBRATED",
            summary_text=summary,
        )
