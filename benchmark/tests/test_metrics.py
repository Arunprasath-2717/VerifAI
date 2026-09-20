"""Unit tests for benchmark.metrics — Cohen's kappa computation.

All tests use known, hand-computed expected values so that the implementation
remains deterministic and reproducible.  No external dependencies required.
"""

import dataclasses

import pytest

from benchmark.metrics import KappaResult, compute_cohens_kappa

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ann(pairs: list[tuple[str, str, str]]) -> tuple[dict, dict]:
    """Build two annotation dicts from a list of (claim_id, label_A, label_B)."""
    a1 = {p[0]: p[1] for p in pairs}
    a2 = {p[0]: p[2] for p in pairs}
    return a1, a2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_input_returns_invalid(self):
        result = compute_cohens_kappa({}, {})
        assert result.is_valid is False
        assert result.kappa is None
        assert result.n_items == 0

    def test_no_overlap_returns_invalid(self):
        a1 = {"c1": "SUPPORTED", "c2": "CONTRADICTED"}
        a2 = {"c3": "SUPPORTED", "c4": "UNKNOWN"}
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is False
        assert result.n_items == 0

    def test_single_item_agreement(self):
        a1, a2 = _ann([("c1", "SUPPORTED", "SUPPORTED")])
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.n_items == 1
        assert result.agreement_count == 1
        # kappa is either 1.0 or None when denominator is 0
        assert result.kappa == 1.0

    def test_single_item_disagreement(self):
        a1, a2 = _ann([("c1", "SUPPORTED", "CONTRADICTED")])
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.n_items == 1
        assert result.agreement_count == 0
        # Single item: annotator 1 uses only SUPPORTED, annotator 2 uses only CONTRADICTED.
        # Marginals: p(SUPPORTED|A1)=1, p(SUPPORTED|A2)=0  → P_e = 0
        # P_o = 0, P_e = 0  → kappa = (0 - 0) / (1 - 0) = 0.0
        assert result.kappa is not None
        assert abs(result.kappa - 0.0) < 1e-3


# ---------------------------------------------------------------------------
# Perfect agreement
# ---------------------------------------------------------------------------


class TestPerfectAgreement:
    def test_perfect_agreement_kappa_one(self):
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "SUPPORTED"),
            ("c3", "CONTRADICTED", "CONTRADICTED"),
            ("c4", "UNKNOWN", "UNKNOWN"),
            ("c5", "UNKNOWN", "UNKNOWN"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.kappa == 1.0
        assert result.observed_agreement == 1.0
        assert result.agreement_count == 5
        assert result.disagreement_count == 0

    def test_perfect_agreement_one_category(self):
        """When both annotators use only one category, kappa = 1.0 (denominator edge case)."""
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "SUPPORTED"),
            ("c3", "SUPPORTED", "SUPPORTED"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.kappa == 1.0


# ---------------------------------------------------------------------------
# High agreement (kappa >= 0.60, quality gate should PASS)
# ---------------------------------------------------------------------------


class TestHighAgreement:
    def test_high_agreement_passes_threshold(self):
        # 9 of 10 agree → P_o = 0.9; kappa formula well above 0.60
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "SUPPORTED"),
            ("c3", "SUPPORTED", "SUPPORTED"),
            ("c4", "CONTRADICTED", "CONTRADICTED"),
            ("c5", "CONTRADICTED", "CONTRADICTED"),
            ("c6", "CONTRADICTED", "CONTRADICTED"),
            ("c7", "UNKNOWN", "UNKNOWN"),
            ("c8", "UNKNOWN", "UNKNOWN"),
            ("c9", "UNKNOWN", "UNKNOWN"),
            ("c10", "SUPPORTED", "CONTRADICTED"),  # one disagreement
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.kappa is not None
        assert result.kappa >= 0.60

    def test_result_is_frozen_dataclass(self):
        a1, a2 = _ann([("c1", "SUPPORTED", "SUPPORTED")])
        result = compute_cohens_kappa(a1, a2)
        assert isinstance(result, KappaResult)
        with pytest.raises(dataclasses.FrozenInstanceError):
            # KappaResult is frozen; assigning should raise FrozenInstanceError
            result.kappa = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Low agreement (kappa < 0.60, quality gate should FAIL / remediate)
# ---------------------------------------------------------------------------


class TestLowAgreement:
    def test_low_agreement_below_threshold(self):
        # Each annotator uses different labels for every item → kappa ≈ -0.5
        pairs = [
            ("c1", "SUPPORTED", "CONTRADICTED"),
            ("c2", "CONTRADICTED", "UNKNOWN"),
            ("c3", "UNKNOWN", "SUPPORTED"),
            ("c4", "SUPPORTED", "UNKNOWN"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.kappa is not None
        assert result.kappa < 0.60

    def test_random_half_agreement(self):
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "CONTRADICTED"),
            ("c3", "CONTRADICTED", "CONTRADICTED"),
            ("c4", "CONTRADICTED", "UNKNOWN"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        assert result.is_valid is True
        assert result.n_items == 4
        assert result.agreement_count == 2
        assert result.disagreement_count == 2


# ---------------------------------------------------------------------------
# Confusion matrix shape
# ---------------------------------------------------------------------------


class TestConfusionMatrix:
    def test_confusion_matrix_keys(self):
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "CONTRADICTED"),
            ("c3", "CONTRADICTED", "UNKNOWN"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        # All three labels should appear in matrix
        assert "SUPPORTED" in result.confusion_matrix
        assert "CONTRADICTED" in result.confusion_matrix
        assert "UNKNOWN" in result.confusion_matrix

    def test_confusion_matrix_totals_equal_n(self):
        pairs = [
            ("c1", "SUPPORTED", "SUPPORTED"),
            ("c2", "SUPPORTED", "CONTRADICTED"),
            ("c3", "CONTRADICTED", "CONTRADICTED"),
            ("c4", "UNKNOWN", "UNKNOWN"),
        ]
        a1, a2 = _ann(pairs)
        result = compute_cohens_kappa(a1, a2)
        total = sum(v for row in result.confusion_matrix.values() for v in row.values())
        assert total == result.n_items


# ---------------------------------------------------------------------------
# Partial overlap (extra keys in one annotator set)
# ---------------------------------------------------------------------------


class TestPartialOverlap:
    def test_only_common_keys_counted(self):
        a1 = {"c1": "SUPPORTED", "c2": "CONTRADICTED", "c_extra": "UNKNOWN"}
        a2 = {"c1": "SUPPORTED", "c2": "CONTRADICTED", "c_only_in_2": "SUPPORTED"}
        result = compute_cohens_kappa(a1, a2)
        assert result.n_items == 2  # only c1, c2 in common
        assert result.agreement_count == 2

    def test_kappa_equals_one_for_full_overlap_perfect_agreement(self):
        a1 = {"c1": "SUPPORTED", "c2": "UNKNOWN"}
        a2 = {"c1": "SUPPORTED", "c2": "UNKNOWN"}
        result = compute_cohens_kappa(a1, a2)
        assert result.kappa == 1.0
