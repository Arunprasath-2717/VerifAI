"""Multi-judge consensus and disagreement analysis engine."""

from app.modules.judging.models import DisagreementResult, JudgeEvaluationData
from app.schemas.verification import JudgeDecision, UnknownReason, VerdictType


class DisagreementEngine:
    """Arbitrates multiple independent judge evaluations conservatively.

    Implements the PRD FR-14 Multi-Judge Arbitration Protocol:
    - Case A (Two Judges Agree): Common verdict, degraded_evaluation=False.
    - Case B (Two Judges Disagree & Third Judge Available): 2-of-3 majority verdict,
      degraded_evaluation=False.
    - Case C (All Three Judges Disagree): UNKNOWN verdict, degraded_evaluation=True.
    - Case D (Third Judge Unavailable): UNKNOWN verdict, degraded_evaluation=True.
    - Case E (Invalid or Unusable Output): Recorded safely, degraded_evaluation=True,
      never fabricating consensus.
    """

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
                disagreement_details="No judge evaluations provided.",
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                judge_evaluations=[],
                degraded_evaluation=True,
                judges_used=0,
                third_judge_invoked=False,
                arbitration_reason="No judge evaluations provided.",
            )

        # Separate active valid evaluations from UNAVAILABLE evaluations
        active = [e for e in evaluations if e.judgment != JudgeDecision.UNAVAILABLE]
        n_total = len(evaluations)
        third_invoked = n_total >= 3

        # Case E: All judges reported UNAVAILABLE or no active judges
        if not active:
            return DisagreementResult(
                consensus_verdict=VerdictType.UNKNOWN,
                has_disagreement=False,
                disagreement_details="All configured judges reported UNAVAILABLE.",
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                judge_evaluations=evaluations,
                degraded_evaluation=True,
                judges_used=n_total,
                third_judge_invoked=third_invoked,
                arbitration_reason="All configured judges reported UNAVAILABLE.",
            )

        # Case E: Partial judge failure with fewer than 2 active judges
        if len(active) < 2 and n_total >= 2:
            return DisagreementResult(
                consensus_verdict=VerdictType.UNKNOWN,
                has_disagreement=True,
                disagreement_details=(
                    f"Insufficient active judges: only {len(active)} of {n_total} "
                    f"judges produced usable outputs."
                ),
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                judge_evaluations=evaluations,
                degraded_evaluation=True,
                judges_used=n_total,
                third_judge_invoked=third_invoked,
                arbitration_reason=(
                    f"Partial judge failure ({len(active)}/{n_total} active); "
                    "multi-judge consensus cannot be established."
                ),
            )

        # Helper to normalize JudgeDecision into VerdictType
        def normalize_judgment(jd: JudgeDecision) -> VerdictType:
            if jd == JudgeDecision.SUPPORTED:
                return VerdictType.SUPPORTED
            elif jd == JudgeDecision.CONTRADICTED:
                return VerdictType.CONTRADICTED
            return VerdictType.UNKNOWN

        # ---------------------------------------------------------------------
        # Scenario 1: Exactly 2 Judges Evaluated (Initial Phase)
        # ---------------------------------------------------------------------
        if n_total == 2:
            j1, j2 = active[0], active[1]
            v1, v2 = normalize_judgment(j1.judgment), normalize_judgment(j2.judgment)

            if v1 == v2:
                # CASE A: TWO JUDGES AGREE
                return DisagreementResult(
                    consensus_verdict=v1,
                    has_disagreement=False,
                    disagreement_details=None,
                    unknown_reason=None
                    if v1 != VerdictType.UNKNOWN
                    else UnknownReason.INSUFFICIENT_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=False,
                    judges_used=2,
                    third_judge_invoked=False,
                    arbitration_reason=(
                        f"Consensus reached: both judges agreed on {v1.value}."
                    ),
                )
            else:
                # CASE D: TWO JUDGES DISAGREE AND THIRD JUDGE NOT PROVIDED / UNAVAILABLE
                return DisagreementResult(
                    consensus_verdict=VerdictType.UNKNOWN,
                    has_disagreement=True,
                    disagreement_details=(
                        f"Judge disagreement: {j1.judge_name} reported {v1.value}, "
                        f"{j2.judge_name} reported {v2.value}. "
                        "Tie-breaker judge was unavailable or not invoked."
                    ),
                    unknown_reason=UnknownReason.CONFLICTING_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=True,
                    judges_used=2,
                    third_judge_invoked=False,
                    arbitration_reason=(
                        f"Judges disagreed ({v1.value} vs {v2.value}) and third-judge "
                        "tie-breaker is unavailable."
                    ),
                )

        # ---------------------------------------------------------------------
        # Scenario 2: Three Judges Evaluated (Tie-Breaker Invoked)
        # ---------------------------------------------------------------------
        norm_verdicts = [normalize_judgment(e.judgment) for e in active]

        # Check if the third judge was unavailable among the 3 provided
        if len(active) == 2 and n_total >= 3:
            # CASE D: THIRD JUDGE REPORTED UNAVAILABLE
            v1, v2 = norm_verdicts[0], norm_verdicts[1]
            if v1 == v2:
                # Primary two already agreed, third was just unavailable
                return DisagreementResult(
                    consensus_verdict=v1,
                    has_disagreement=False,
                    disagreement_details=(
                        "Third judge was UNAVAILABLE, but primary judges reached "
                        "consensus."
                    ),
                    unknown_reason=None
                    if v1 != VerdictType.UNKNOWN
                    else UnknownReason.INSUFFICIENT_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=False,
                    judges_used=n_total,
                    third_judge_invoked=True,
                    arbitration_reason=(
                        f"Primary consensus accepted: {v1.value} "
                        "(tie-breaker unavailable)."
                    ),
                )
            else:
                return DisagreementResult(
                    consensus_verdict=VerdictType.UNKNOWN,
                    has_disagreement=True,
                    disagreement_details=(
                        f"Primary judges disagreed ({v1.value} vs {v2.value}) "
                        "and designated tie-breaker judge was UNAVAILABLE."
                    ),
                    unknown_reason=UnknownReason.CONFLICTING_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=True,
                    judges_used=n_total,
                    third_judge_invoked=True,
                    arbitration_reason=(
                        "Primary judges disagreed and tie-breaker judge was "
                        "UNAVAILABLE."
                    ),
                )

        # All 3 judges active: count verdict occurrences
        counts: dict[VerdictType, int] = {
            VerdictType.SUPPORTED: norm_verdicts.count(VerdictType.SUPPORTED),
            VerdictType.CONTRADICTED: norm_verdicts.count(VerdictType.CONTRADICTED),
            VerdictType.UNKNOWN: norm_verdicts.count(VerdictType.UNKNOWN),
        }

        # Check for unanimous agreement across all 3
        for v, cnt in counts.items():
            if cnt == 3:
                return DisagreementResult(
                    consensus_verdict=v,
                    has_disagreement=False,
                    disagreement_details=None,
                    unknown_reason=None
                    if v != VerdictType.UNKNOWN
                    else UnknownReason.INSUFFICIENT_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=False,
                    judges_used=3,
                    third_judge_invoked=True,
                    arbitration_reason=(
                        f"Unanimous consensus: all 3 judges agreed on {v.value}."
                    ),
                )

        # Check for 2-out-of-3 majority (Case B)
        for v, cnt in counts.items():
            if cnt == 2:
                # CASE B: TWO-OUT-OF-THREE MAJORITY
                dissenting = [nv.value for nv in norm_verdicts if nv != v]
                return DisagreementResult(
                    consensus_verdict=v,
                    has_disagreement=True,
                    disagreement_details=(
                        f"Majority decision (2-of-3): {v.value}. "
                        f"Dissenting judgment: {dissenting}."
                    ),
                    unknown_reason=None
                    if v != VerdictType.UNKNOWN
                    else UnknownReason.INSUFFICIENT_EVIDENCE,
                    judge_evaluations=evaluations,
                    degraded_evaluation=False,
                    judges_used=3,
                    third_judge_invoked=True,
                    arbitration_reason=f"Majority decision (2-of-3): {v.value}.",
                )

        # CASE C: ALL THREE JUDGES DISAGREE (counts are 1, 1, 1)
        return DisagreementResult(
            consensus_verdict=VerdictType.UNKNOWN,
            has_disagreement=True,
            disagreement_details=(
                "All three judges produced conflicting judgments: "
                "1 SUPPORTED, 1 CONTRADICTED, 1 UNKNOWN. "
                "No majority could be formed."
            ),
            unknown_reason=UnknownReason.CONFLICTING_EVIDENCE,
            judge_evaluations=evaluations,
            degraded_evaluation=True,
            judges_used=3,
            third_judge_invoked=True,
            arbitration_reason=(
                "All three judges disagreed; no majority consensus formed."
            ),
        )
