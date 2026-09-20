"""Multi-judge consensus and disagreement analysis engine."""

from app.modules.judging.models import DisagreementResult, JudgeEvaluationData
from app.schemas.verification import JudgeDecision, UnknownReason, VerdictType


class DisagreementEngine:
    """Arbitrates multiple independent judge evaluations conservatively."""

    def arbitrate(
        self,
        evaluations: list[JudgeEvaluationData],
        strict_consensus: bool = True,
    ) -> DisagreementResult:
        """Arbitrate judge judgments into a consensus verdict and conflict log."""
        if not evaluations:
            return DisagreementResult(
                consensus_verdict=VerdictType.UNKNOWN,
                has_disagreement=False,
                disagreement_details=None,
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                judge_evaluations=[],
            )

        # Filter active judgments (excluding UNAVAILABLE if at least one active
        # judge exists)
        active = [e for e in evaluations if e.judgment != JudgeDecision.UNAVAILABLE]

        # If all judges are UNAVAILABLE, report honest INSUFFICIENT_EVIDENCE
        if not active:
            return DisagreementResult(
                consensus_verdict=VerdictType.UNKNOWN,
                has_disagreement=False,
                disagreement_details="All configured judges reported UNAVAILABLE.",
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                judge_evaluations=evaluations,
            )

        judgments = [e.judgment for e in active]
        unique_judgments = set(judgments)

        # Rule 1: Contradiction safety priority (Hallucination Risk)
        # If ANY judge found a contradiction, immediately flag contradiction
        if JudgeDecision.CONTRADICTED in unique_judgments:
            has_conflict = len(unique_judgments) > 1
            details = None
            if has_conflict:
                details = (
                    f"Conflict detected: judges reported {judgments}. "
                    f"Conservative safety rule prioritized CONTRADICTED."
                )

            return DisagreementResult(
                consensus_verdict=VerdictType.CONTRADICTED,
                has_disagreement=has_conflict,
                disagreement_details=details,
                unknown_reason=None,
                judge_evaluations=evaluations,
            )

        # Rule 2: Full Consensus Support
        if unique_judgments == {JudgeDecision.SUPPORTED}:
            return DisagreementResult(
                consensus_verdict=VerdictType.SUPPORTED,
                has_disagreement=False,
                disagreement_details=None,
                unknown_reason=None,
                judge_evaluations=evaluations,
            )

        # Rule 3: Disagreement between SUPPORTED and INSUFFICIENT/UNKNOWN
        if JudgeDecision.SUPPORTED in unique_judgments:
            return DisagreementResult(
                consensus_verdict=VerdictType.UNKNOWN,
                has_disagreement=True,
                disagreement_details=(
                    f"Judge disagreement: one judge reported SUPPORTED while "
                    f"another reported {unique_judgments - {JudgeDecision.SUPPORTED}}. "
                    f"Conservative policy resolved to UNKNOWN."
                ),
                unknown_reason=UnknownReason.CONFLICTING_EVIDENCE,
                judge_evaluations=evaluations,
            )

        # Rule 4: All active judges reported INSUFFICIENT_EVIDENCE or UNKNOWN
        return DisagreementResult(
            consensus_verdict=VerdictType.UNKNOWN,
            has_disagreement=False,
            disagreement_details=None,
            unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
            judge_evaluations=evaluations,
        )
