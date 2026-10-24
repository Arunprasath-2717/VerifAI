"""Unit tests for benchmark.freeze — SHA-256 manifest & integrity verification.

Tests:
- freeze_dataset blocked unless quality gate status is PASS
- freeze_dataset writes a valid manifest JSON
- compute_file_sha256 is deterministic
- verify_frozen_manifest detects tampering
- verify_frozen_manifest passes on untouched dataset
"""

import json
from pathlib import Path

from benchmark.freeze import (
    compute_file_sha256,
    freeze_dataset,
    verify_frozen_manifest,
)
from benchmark.quality_gate import QualityGateEvaluation
from benchmark.schemas import (
    AnnotationPass,
    AtomicClaim,
    BenchmarkCase,
    BenchmarkCategory,
    ClaimLabel,
    ContentType,
    DatasetSplit,
    DatasetStatus,
    QualityGateStatus,
    VerdictType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pass_gate(kappa: float = 0.75) -> QualityGateEvaluation:
    return QualityGateEvaluation(
        status=QualityGateStatus.PASS,
        passed=True,
        threshold=0.60,
        observed_kappa=kappa,
        current_pass=AnnotationPass.SECOND_PASS,
        remediation_cycle=0,
        shortfall=None,
        summary="Gate passed.",
        details={"n_items": 100},
    )


def _make_fail_gate(
    status: QualityGateStatus = QualityGateStatus.REMEDIATION_1,
) -> QualityGateEvaluation:
    return QualityGateEvaluation(
        status=status,
        passed=False,
        threshold=0.60,
        observed_kappa=0.40,
        current_pass=AnnotationPass.SECOND_PASS,
        remediation_cycle=0,
        shortfall=0.20,
        summary="Gate failed.",
        details={"n_items": 100},
    )


def _make_minimal_cases() -> list[BenchmarkCase]:
    """Build two minimal valid BenchmarkCase objects for freeze tests."""
    claim = AtomicClaim(
        claim_id="c1",
        claim_text="Test claim.",
        start_offset=0,
        end_offset=11,
        gold_label=ClaimLabel.SUPPORTED,
    )
    case = BenchmarkCase(
        case_id="CASE-001",
        query="Test query?",
        response="Test claim.",
        category=BenchmarkCategory.VERIFIED_FACT,
        content_type=ContentType.FACTUAL,
        expected_verdict=VerdictType.SUPPORTED,
        atomic_claims=[claim],
        split=DatasetSplit.TRAIN,
    )
    return [case]


# ---------------------------------------------------------------------------
# SHA-256 helpers
# ---------------------------------------------------------------------------


class TestComputeSha256:
    def test_same_file_twice_gives_same_hash(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('["test"]', encoding="utf-8")
        h1 = compute_file_sha256(f)
        h2 = compute_file_sha256(f)
        assert h1 == h2

    def test_different_content_gives_different_hash(self, tmp_path):
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f1.write_text('["a"]', encoding="utf-8")
        f2.write_text('["b"]', encoding="utf-8")
        assert compute_file_sha256(f1) != compute_file_sha256(f2)

    def test_hash_is_64_hex_chars(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text("hello", encoding="utf-8")
        h = compute_file_sha256(f)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# freeze_dataset — blocked without PASS
# ---------------------------------------------------------------------------


class TestFreezeBlocked:
    def test_freeze_blocked_when_gate_not_passed(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_fail_gate(QualityGateStatus.REMEDIATION_1)
        success, message, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta"
        )
        assert success is False
        assert manifest is None
        assert "Quality gate has not PASSED" in message

    def test_freeze_blocked_for_fail_status(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_fail_gate(QualityGateStatus.FAIL)
        success, _, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta"
        )
        assert success is False
        assert manifest is None

    def test_freeze_blocked_for_insufficient_data(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_fail_gate(QualityGateStatus.INSUFFICIENT_DATA)
        success, _, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta"
        )
        assert success is False
        assert manifest is None


# ---------------------------------------------------------------------------
# freeze_dataset — successful freeze
# ---------------------------------------------------------------------------


class TestFreezeSuccessful:
    def test_freeze_with_pass_gate_succeeds(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_pass_gate(kappa=0.75)
        success, _message, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta", version_label="dataset_v1"
        )
        assert success is True
        assert manifest is not None
        assert manifest.status == DatasetStatus.FROZEN

    def test_manifest_json_written_to_disk(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_pass_gate()
        freeze_dataset(dataset_file, cases, gate, tmp_path / "meta", "dataset_v1")
        manifest_file = tmp_path / "meta" / "dataset_v1_manifest.json"
        assert manifest_file.exists()

    def test_manifest_checksum_matches_file(self, tmp_path):
        cases = _make_minimal_cases()
        content = json.dumps([c.model_dump(mode="json") for c in cases])
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(content)

        gate = _make_pass_gate()
        _, _, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta", "dataset_v1"
        )
        assert manifest is not None
        actual_hash = compute_file_sha256(dataset_file)
        assert manifest.checksum_sha256 == actual_hash

    def test_manifest_kappa_stored(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_pass_gate(kappa=0.82)
        _, _, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta", "dataset_v1"
        )
        assert manifest is not None
        assert manifest.kappa_score == 0.82

    def test_manifest_total_cases_correct(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_pass_gate()
        _, _, manifest = freeze_dataset(
            dataset_file, cases, gate, tmp_path / "meta", "dataset_v1"
        )
        assert manifest is not None
        assert manifest.total_cases == len(cases)


# ---------------------------------------------------------------------------
# verify_frozen_manifest
# ---------------------------------------------------------------------------


class TestVerifyFrozenManifest:
    def _create_frozen(self, tmp_path) -> tuple[Path, Path]:
        cases = _make_minimal_cases()
        content = json.dumps([c.model_dump(mode="json") for c in cases])
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(content)

        gate = _make_pass_gate()
        freeze_dataset(dataset_file, cases, gate, tmp_path / "meta", "dataset_v1")
        manifest_file = tmp_path / "meta" / "dataset_v1_manifest.json"
        return dataset_file, manifest_file

    def test_integrity_check_passes_on_untampered_file(self, tmp_path):
        dataset_file, manifest_file = self._create_frozen(tmp_path)
        ok, msg = verify_frozen_manifest(manifest_file, dataset_file)
        assert ok is True
        assert "integrity verified" in msg

    def test_integrity_check_fails_after_tampering(self, tmp_path):
        dataset_file, manifest_file = self._create_frozen(tmp_path)
        # Tamper with the dataset file
        with open(dataset_file, "a") as f:
            f.write("\n# TAMPERED")
        ok, msg = verify_frozen_manifest(manifest_file, dataset_file)
        assert ok is False
        assert "Checksum mismatch" in msg

    def test_missing_manifest_returns_failure(self, tmp_path):
        ok, msg = verify_frozen_manifest(
            tmp_path / "nonexistent_manifest.json",
            tmp_path / "data.json",
        )
        assert ok is False
        assert "not found" in msg

    def test_missing_dataset_returns_failure(self, tmp_path):
        cases = _make_minimal_cases()
        dataset_file = tmp_path / "data.json"
        dataset_file.write_text(json.dumps([c.model_dump(mode="json") for c in cases]))

        gate = _make_pass_gate()
        freeze_dataset(dataset_file, cases, gate, tmp_path / "meta", "dataset_v1")
        manifest_file = tmp_path / "meta" / "dataset_v1_manifest.json"

        ok, msg = verify_frozen_manifest(manifest_file, tmp_path / "no_such_file.json")
        assert ok is False
        assert "not found" in msg
