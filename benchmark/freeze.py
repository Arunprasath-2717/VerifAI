"""Dataset freeze workflow and SHA-256 manifest verification."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from benchmark.quality_gate import QualityGateEvaluation
from benchmark.schemas import (
    BenchmarkCase,
    DatasetManifest,
    DatasetStatus,
    QualityGateStatus,
)


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute deterministic SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def freeze_dataset(
    dataset_file: Path | str,
    cases: list[BenchmarkCase],
    quality_gate_eval: QualityGateEvaluation,
    manifest_dir: Path | str,
    version_label: str = "dataset_v1",
) -> tuple[bool, str, DatasetManifest | None]:
    """Freeze benchmark dataset into a locked, immutable release manifest.

    Enforces that freezing is strictly prohibited unless the quality gate
    has status PASS.
    """
    if quality_gate_eval.status != QualityGateStatus.PASS:
        return (
            False,
            (
                f"Cannot freeze {version_label}: Quality gate has not PASSED. "
                f"Current status is '{quality_gate_eval.status.value}'."
            ),
            None,
        )

    file_path = Path(dataset_file)
    if not file_path.exists():
        return False, f"Dataset file does not exist: {file_path}", None

    checksum = compute_file_sha256(file_path)

    # Compute category and split summaries
    category_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    total_claims = 0

    for case in cases:
        cat = case.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1
        sp = case.split.value
        split_counts[sp] = split_counts.get(sp, 0) + 1
        total_claims += len(case.atomic_claims)

    now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = DatasetManifest(
        dataset_name="verifai_hallucination_benchmark",
        version=version_label,
        status=DatasetStatus.FROZEN,
        checksum_sha256=checksum,
        total_cases=len(cases),
        category_breakdown=category_counts,
        claim_count=total_claims,
        split_counts=split_counts,
        kappa_score=quality_gate_eval.observed_kappa,
        created_at=now_iso,
        frozen_at=now_iso,
    )

    manifest_path = Path(manifest_dir) / f"{version_label}_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    return (
        True,
        f"Dataset {version_label} successfully frozen. Manifest: {manifest_path}",
        manifest,
    )


def verify_frozen_manifest(
    manifest_file: Path | str,
    dataset_file: Path | str,
) -> tuple[bool, str]:
    """Verify that a frozen dataset's content matches its immutable manifest."""
    manifest_path = Path(manifest_file)
    dataset_path = Path(dataset_file)

    if not manifest_path.exists():
        return False, f"Manifest file not found: {manifest_path}"
    if not dataset_path.exists():
        return False, f"Dataset file not found: {dataset_path}"

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    manifest = DatasetManifest.model_validate(data)

    current_checksum = compute_file_sha256(dataset_path)
    if current_checksum != manifest.checksum_sha256:
        return (
            False,
            (
                f"Checksum mismatch! Manifest expects {manifest.checksum_sha256}, "
                f"but file computed {current_checksum}. Dataset has been modified!"
            ),
        )

    return True, f"Dataset {manifest.version} integrity verified (SHA-256 match)."
