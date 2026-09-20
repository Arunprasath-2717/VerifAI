"""Unit tests for benchmark.quality_gate — PRD Section 23.4 state machine.

Tests cover the full lifecycle:
  SECOND_PASS  → PASS (kappa >= 0.60)
  SECOND_PASS  → REMEDIATION_1 (kappa < 0.60)
  REMEDIATION_1 → PASS
  REMEDIATION_1 → REMEDIATION_2
  REMEDIATION_2 → PASS
  REMEDIATION_2 → FAIL (cap exhausted)
  Invalid / empty → INSUFFICIENT_DATA
"""

from benchmark.metrics import KappaResult
from benchmark.quality_gate import QualityGateEvaluation, evaluate_quality_gate
from benchmark.schemas import AnnotationPass, QualityGateStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kappa(kappa: float | None, valid: bool = True, n: int = 10) -> KappaResult:
    """Construct a minimal KappaResult fixture."""
    return KappaResult(
        kappa=kappa,
        observed_agreement=kappa if kappa is not None else 0.0,
        expected_agreement=0.0,
        n_items=n,
        agreement_count=int(n * kappa) if kappa is not None else 0,
        disagreement_count=n - int(n * kappa) if kappa is not None else n,
        confusion_matrix={},
        categories=[],
        is_valid=valid,
        message="Test fixture",
    )


_INVALID = KappaResult(
    kappa=None,
    observed_agreement=0.0,
    expected_agreement=0.0,
    n_items=0,
    agreement_count=0,
    disagreement_count=0,
    confusion_matrix={},
    categories=[],
    is_valid=False,
    message="No annotations found.",
)

THRESHOLD = 0.60


# ---------------------------------------------------------------------------
# INSUFFICIENT_DATA branch
# ---------------------------------------------------------------------------


class TestInsufficientData:
    def test_invalid_kappa_result_gives_insufficient_data(self):
        result = evaluate_quality_gate(_INVALID, pass_type=AnnotationPass.SECOND_PASS)
        assert result.status == QualityGateStatus.INSUFFICIENT_DATA
        assert result.passed is False
        assert result.observed_kappa is None

    def test_none_kappa_with_is_valid_false(self):
        kr = _make_kappa(None, valid=False, n=0)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert result.status == QualityGateStatus.INSUFFICIENT_DATA
        assert result.passed is False


# ---------------------------------------------------------------------------
# SECOND_PASS → PASS
# ---------------------------------------------------------------------------


class TestSecondPassPasses:
    def test_above_threshold_second_pass(self):
        kr = _make_kappa(0.75)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert result.status == QualityGateStatus.PASS
        assert result.passed is True
        assert result.shortfall is None
        assert result.remediation_cycle == 0

    def test_exactly_at_threshold_passes(self):
        kr = _make_kappa(0.60)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert result.status == QualityGateStatus.PASS
        assert result.passed is True

    def test_observed_kappa_in_result(self):
        kr = _make_kappa(0.82)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert result.observed_kappa == 0.82


# ---------------------------------------------------------------------------
# SECOND_PASS → REMEDIATION_1
# ---------------------------------------------------------------------------


class TestSecondPassFails:
    def test_below_threshold_triggers_remediation_1(self):
        kr = _make_kappa(0.45)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert result.status == QualityGateStatus.REMEDIATION_1
        assert result.passed is False
        assert result.shortfall is not None
        assert result.shortfall > 0.0

    def test_shortfall_calculation_correct(self):
        kr = _make_kappa(0.45)
        result = evaluate_quality_gate(
            kr, pass_type=AnnotationPass.SECOND_PASS, threshold=0.60
        )
        assert result.shortfall is not None
        assert abs(result.shortfall - 0.15) < 1e-3

    def test_first_pass_also_triggers_remediation_1(self):
        kr = _make_kappa(0.40)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.FIRST_PASS)
        assert result.status == QualityGateStatus.REMEDIATION_1
        assert result.passed is False


# ---------------------------------------------------------------------------
# REMEDIATION_1 → PASS
# ---------------------------------------------------------------------------


class TestRemediation1Passes:
    def test_remediation_1_pass(self):
        kr = _make_kappa(0.68)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.REMEDIATION_1)
        assert result.status == QualityGateStatus.PASS
        assert result.passed is True
        assert result.remediation_cycle == 1


# ---------------------------------------------------------------------------
# REMEDIATION_1 → REMEDIATION_2
# ---------------------------------------------------------------------------


class TestRemediation1Fails:
    def test_remediation_1_fail_triggers_remediation_2(self):
        kr = _make_kappa(0.50)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.REMEDIATION_1)
        assert result.status == QualityGateStatus.REMEDIATION_2
        assert result.passed is False
        assert result.remediation_cycle == 1


# ---------------------------------------------------------------------------
# REMEDIATION_2 → PASS
# ---------------------------------------------------------------------------


class TestRemediation2Passes:
    def test_remediation_2_pass(self):
        kr = _make_kappa(0.62)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.REMEDIATION_2)
        assert result.status == QualityGateStatus.PASS
        assert result.passed is True
        assert result.remediation_cycle == 2


# ---------------------------------------------------------------------------
# REMEDIATION_2 → FAIL (cap exhausted)
# ---------------------------------------------------------------------------


class TestRemediation2Fails:
    def test_remediation_2_fail_is_hard_fail(self):
        kr = _make_kappa(0.30)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.REMEDIATION_2)
        assert result.status == QualityGateStatus.FAIL
        assert result.passed is False
        assert result.shortfall is not None
        assert result.remediation_cycle == 2

    def test_fail_shortfall_documented(self):
        kr = _make_kappa(0.10)
        result = evaluate_quality_gate(
            kr, pass_type=AnnotationPass.REMEDIATION_2, threshold=0.60
        )
        assert result.shortfall is not None
        assert abs(result.shortfall - 0.50) < 1e-3


# ---------------------------------------------------------------------------
# Return type and immutability
# ---------------------------------------------------------------------------


class TestReturnType:
    def test_returns_quality_gate_evaluation_dataclass(self):
        kr = _make_kappa(0.75)
        result = evaluate_quality_gate(kr, pass_type=AnnotationPass.SECOND_PASS)
        assert isinstance(result, QualityGateEvaluation)

    def test_threshold_stored_correctly(self):
        kr = _make_kappa(0.75)
        result = evaluate_quality_gate(
            kr, pass_type=AnnotationPass.SECOND_PASS, threshold=0.70
        )
        assert result.threshold == 0.70

    def test_custom_threshold_respected(self):
        """kappa=0.65 should PASS with threshold=0.60 but FAIL with threshold=0.70."""
        kr = _make_kappa(0.65)
        pass_result = evaluate_quality_gate(
            kr, pass_type=AnnotationPass.SECOND_PASS, threshold=0.60
        )
        fail_result = evaluate_quality_gate(
            kr, pass_type=AnnotationPass.SECOND_PASS, threshold=0.70
        )
        assert pass_result.passed is True
        assert fail_result.passed is False
