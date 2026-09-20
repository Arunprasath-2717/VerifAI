"""PRD Section 23.4 Annotation Quality Gate & Two-Cycle Remediation State Machine."""

from dataclasses import dataclass
from typing import Any

from benchmark.metrics import KappaResult
from benchmark.schemas import AnnotationPass, QualityGateStatus


@dataclass(frozen=True)
class QualityGateEvaluation:
    """Outcome of quality gate evaluation."""

    status: QualityGateStatus
    passed: bool
    threshold: float
    observed_kappa: float | None
    current_pass: AnnotationPass
    remediation_cycle: int
    shortfall: float | None
    summary: str
    details: dict[str, Any]


def evaluate_quality_gate(
    kappa_result: KappaResult,
    pass_type: AnnotationPass = AnnotationPass.SECOND_PASS,
    threshold: float = 0.60,
) -> QualityGateEvaluation:
    """Evaluate annotation agreement against the PRD kappa >= 0.60 quality gate.

    Enforces the two-cycle remediation protocol:
    1. SECOND_PASS: Initial dual-annotation check. If kappa >= 0.60 -> PASS.
       If kappa < 0.60 -> triggers REMEDIATION_1.
    2. REMEDIATION_1: First remediation cycle. If kappa >= 0.60 -> PASS.
       If kappa < 0.60 -> triggers REMEDIATION_2.
    3. REMEDIATION_2: Second remediation cycle. If kappa >= 0.60 -> PASS.
       If kappa < 0.60 -> FAIL (capped at 2 cycles; shortfall documented).
    """
    if not kappa_result.is_valid or kappa_result.kappa is None:
        return QualityGateEvaluation(
            status=QualityGateStatus.INSUFFICIENT_DATA,
            passed=False,
            threshold=threshold,
            observed_kappa=None,
            current_pass=pass_type,
            remediation_cycle=0,
            shortfall=None,
            summary="Quality gate check blocked: Insufficient annotation data.",
            details={"message": kappa_result.message, "n_items": kappa_result.n_items},
        )

    kappa = kappa_result.kappa
    shortfall = round(max(0.0, threshold - kappa), 4) if kappa < threshold else None

    # Determine remediation cycle index
    cycle_map = {
        AnnotationPass.FIRST_PASS: 0,
        AnnotationPass.SECOND_PASS: 0,
        AnnotationPass.REMEDIATION_1: 1,
        AnnotationPass.REMEDIATION_2: 2,
    }
    cycle = cycle_map.get(pass_type, 0)

    if kappa >= threshold:
        return QualityGateEvaluation(
            status=QualityGateStatus.PASS,
            passed=True,
            threshold=threshold,
            observed_kappa=kappa,
            current_pass=pass_type,
            remediation_cycle=cycle,
            shortfall=None,
            summary=(
                f"Quality gate PASSED: Cohen's kappa {kappa:.4f} satisfies "
                f"threshold >= {threshold:.2f}."
            ),
            details={
                "n_items": kappa_result.n_items,
                "observed_agreement": kappa_result.observed_agreement,
                "expected_agreement": kappa_result.expected_agreement,
            },
        )

    # Sub-threshold: determine remediation state based on cycle
    if pass_type in (AnnotationPass.FIRST_PASS, AnnotationPass.SECOND_PASS):
        next_status = QualityGateStatus.REMEDIATION_1
        summary = (
            f"Quality gate sub-threshold (kappa={kappa:.4f} < {threshold:.2f}). "
            "Shortfall of {shortfall:.4f}. Entering Remediation Cycle 1."
        )
    elif pass_type == AnnotationPass.REMEDIATION_1:
        next_status = QualityGateStatus.REMEDIATION_2
        summary = (
            f"Remediation Cycle 1 sub-threshold (kappa={kappa:.4f} < {threshold:.2f}). "
            "Shortfall of {shortfall:.4f}. Entering Final Remediation Cycle 2."
        )
    else:  # pass_type == AnnotationPass.REMEDIATION_2
        # Capped at two cycles per PRD Section 23.4
        next_status = QualityGateStatus.FAIL
        summary = (
            f"Quality gate FAILED: Remediation cap exhausted (2 cycles). "
            f"Final kappa={kappa:.4f} < {threshold:.2f}, "
            f"shortfall={shortfall:.4f}."
        )

    return QualityGateEvaluation(
        status=next_status,
        passed=False,
        threshold=threshold,
        observed_kappa=kappa,
        current_pass=pass_type,
        remediation_cycle=cycle,
        shortfall=shortfall,
        summary=summary,
        details={
            "n_items": kappa_result.n_items,
            "observed_agreement": kappa_result.observed_agreement,
            "expected_agreement": kappa_result.expected_agreement,
            "confusion_matrix": kappa_result.confusion_matrix,
        },
    )
