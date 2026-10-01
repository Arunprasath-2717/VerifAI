"""Command-line interface for VerifAI benchmark dataset management and research."""

import argparse
import json
import sys
from pathlib import Path

from benchmark.freeze import freeze_dataset, verify_frozen_manifest
from benchmark.metrics import compute_cohens_kappa
from benchmark.quality_gate import evaluate_quality_gate
from benchmark.schemas import AnnotationPass
from benchmark.validator import load_and_validate_dataset_file


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate dataset structure and semantic constraints."""
    path = Path(args.dataset_path)
    print(f"[*] Validating benchmark dataset at: {path}")
    _cases, report = load_and_validate_dataset_file(
        path, require_full_100=not args.allow_partial
    )

    if not report.is_valid:
        print(f"[FAIL] Dataset validation failed with {len(report.errors)} error(s):")
        for err in report.errors:
            print(f"  - {err}")
        return 1

    print("[PASS] Benchmark dataset validated successfully!")
    print(f"  Total Cases: {report.total_cases}")
    print(f"  Category Breakdown: {report.category_counts}")
    print(f"  Split Counts: {report.split_counts}")
    print(f"  Total Atomic Claims: {report.total_claims}")
    return 0


def cmd_agreement(args: argparse.Namespace) -> int:
    """Compute Cohen's kappa agreement between two annotation sets."""
    print(f"[*] Loading annotations from: {args.annotations_file}")
    path = Path(args.annotations_file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 1

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Allow selecting a sample key or top-level annotator dicts
    if args.sample_key and args.sample_key in data:
        pair_data = data[args.sample_key]
    else:
        pair_data = data

    ann1 = pair_data.get("annotator_1", {})
    ann2 = pair_data.get("annotator_2", {})

    result = compute_cohens_kappa(ann1, ann2)
    if not result.is_valid or result.kappa is None:
        print(f"[FAIL] {result.message}")
        return 1

    print("=" * 60)
    print("Cohen's Kappa Agreement Evaluation")
    print("=" * 60)
    print(f"  Comparable Items:     {result.n_items}")
    print(f"  Agreement Count:      {result.agreement_count}")
    print(f"  Disagreement Count:   {result.disagreement_count}")
    print(f"  Observed Agreement:   {result.observed_agreement:.4f}")
    print(f"  Expected Agreement:   {result.expected_agreement:.4f}")
    print(f"  Cohen's Kappa:        {result.kappa:.4f}")
    print("=" * 60)
    return 0


def cmd_quality_gate(args: argparse.Namespace) -> int:
    """Evaluate annotation agreement against PRD Section 23.4 quality gate."""
    print(f"[*] Evaluating quality gate from: {args.annotations_file}")
    path = Path(args.annotations_file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 1

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if args.sample_key and args.sample_key in data:
        pair_data = data[args.sample_key]
    else:
        pair_data = data

    ann1 = pair_data.get("annotator_1", {})
    ann2 = pair_data.get("annotator_2", {})

    kappa_res = compute_cohens_kappa(ann1, ann2)
    pass_enum = AnnotationPass(args.pass_type)
    gate_eval = evaluate_quality_gate(
        kappa_res, pass_type=pass_enum, threshold=args.threshold
    )

    print("=" * 60)
    print("PRD Section 23.4 Quality Gate Evaluation")
    print("=" * 60)
    print(f"  Current Pass:         {gate_eval.current_pass.value}")
    print(f"  Remediation Cycle:    {gate_eval.remediation_cycle}/2")
    print(f"  Threshold Required:   kappa >= {gate_eval.threshold:.2f}")
    if gate_eval.observed_kappa is not None:
        print(f"  Observed Kappa:       {gate_eval.observed_kappa:.4f}")
    else:
        print("  Observed Kappa:       None (Insufficient Data)")
    print(f"  Gate Status:          {gate_eval.status.value}")
    print(f"  Summary:              {gate_eval.summary}")
    print("=" * 60)

    return 0 if gate_eval.passed else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Report honest status of the benchmark dataset and manifests."""
    data_path = Path("benchmark/data/dataset_v1_cases.json")
    manifest_path = Path("benchmark/metadata/dataset_v1_manifest.json")

    print("=" * 60)
    print("VerifAI Benchmark Status Report")
    print("=" * 60)

    if not data_path.exists():
        print(f"  Dataset File:         MISSING ({data_path})")
        return 1

    _cases, report = load_and_validate_dataset_file(data_path, require_full_100=True)
    print(f"  Dataset File:         PRESENT ({data_path})")
    print(f"  Structure Valid:      {report.is_valid}")
    print(f"  Total Cases:          {report.total_cases}/100")
    print(f"  Categories:           {report.category_counts}")
    print(f"  Splits:               {report.split_counts}")

    if manifest_path.exists():
        is_intact, msg = verify_frozen_manifest(manifest_path, data_path)
        print(f"  Freeze Manifest:      PRESENT ({manifest_path})")
        print(f"  Integrity Status:     {'VERIFIED' if is_intact else 'MODIFIED'}")
        print(f"  Manifest Message:     {msg}")
    else:
        print(f"  Freeze Manifest:      NOT FROZEN (No manifest at {manifest_path})")
        print("  Benchmark Status:     DRAFT / AWAITING REAL HUMAN ANNOTATION & GATE")

    print("=" * 60)
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    """Attempt to freeze dataset_v1 with quality-gate verification."""
    data_path = Path(args.dataset_path)
    ann_path = Path(args.annotations_file)

    if not data_path.exists():
        print(f"[ERROR] Dataset file not found: {data_path}")
        return 1
    if not ann_path.exists():
        print(f"[ERROR] Annotation file not found: {ann_path}")
        return 1

    cases, report = load_and_validate_dataset_file(data_path, require_full_100=True)
    if not report.is_valid or not cases:
        print("[FAIL] Cannot freeze: Dataset failed validation.")
        return 1

    with open(ann_path, encoding="utf-8") as f:
        data = json.load(f)

    if args.sample_key and args.sample_key in data:
        pair_data = data[args.sample_key]
    else:
        pair_data = data

    ann1 = pair_data.get("annotator_1", {})
    ann2 = pair_data.get("annotator_2", {})

    kappa_res = compute_cohens_kappa(ann1, ann2)
    gate_eval = evaluate_quality_gate(
        kappa_res, pass_type=AnnotationPass(args.pass_type), threshold=args.threshold
    )

    success, msg, manifest = freeze_dataset(
        dataset_file=data_path,
        cases=cases,
        quality_gate_eval=gate_eval,
        manifest_dir=Path("benchmark/metadata"),
        version_label=args.version_label,
    )

    if not success:
        print(f"[REJECTED] {msg}")
        return 1

    print(f"[SUCCESS] {msg}")
    if manifest:
        print(f"  Checksum SHA-256: {manifest.checksum_sha256}")
        print(f"  Total Cases:      {manifest.total_cases}")
        print(f"  Kappa:            {manifest.kappa_score}")
    return 0


def main() -> None:
    """CLI entry point for benchmark tooling."""
    parser = argparse.ArgumentParser(description="VerifAI Benchmark CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate benchmark dataset")
    p_val.add_argument(
        "--dataset-path",
        default="benchmark/data/dataset_v1_cases.json",
        help="Path to dataset JSON file",
    )
    p_val.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow fewer than 100 cases for testing",
    )
    p_val.set_defaults(func=cmd_validate)

    # agreement
    p_agr = subparsers.add_parser("agreement", help="Compute Cohen's kappa agreement")
    p_agr.add_argument(
        "--annotations-file",
        default="benchmark/data/sample_annotations.json",
        help="Path to annotation pairs JSON",
    )
    p_agr.add_argument(
        "--sample-key",
        default="high_agreement_pass",
        help="Key inside JSON containing annotator_1 and annotator_2",
    )
    p_agr.set_defaults(func=cmd_agreement)

    # quality-gate
    p_gate = subparsers.add_parser(
        "quality-gate", help="Run PRD Section 23.4 quality gate"
    )
    p_gate.add_argument(
        "--annotations-file",
        default="benchmark/data/sample_annotations.json",
        help="Path to annotation pairs JSON",
    )
    p_gate.add_argument(
        "--sample-key",
        default="high_agreement_pass",
        help="Key inside JSON containing annotator_1 and annotator_2",
    )
    p_gate.add_argument(
        "--pass-type",
        default="SECOND_PASS",
        choices=["FIRST_PASS", "SECOND_PASS", "REMEDIATION_1", "REMEDIATION_2"],
        help="Annotation review cycle pass",
    )
    p_gate.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Cohen's kappa threshold (default: 0.60)",
    )
    p_gate.set_defaults(func=cmd_quality_gate)

    # status
    p_stat = subparsers.add_parser("status", help="Inspect benchmark dataset status")
    p_stat.set_defaults(func=cmd_status)

    # freeze
    p_frz = subparsers.add_parser(
        "freeze", help="Freeze dataset_v1 upon quality gate approval"
    )
    p_frz.add_argument(
        "--dataset-path",
        default="benchmark/data/dataset_v1_cases.json",
        help="Path to dataset JSON",
    )
    p_frz.add_argument(
        "--annotations-file",
        default="benchmark/data/sample_annotations.json",
        help="Path to annotation pairs JSON",
    )
    p_frz.add_argument(
        "--sample-key",
        default="high_agreement_pass",
        help="Key inside JSON for annotator pairs",
    )
    p_frz.add_argument(
        "--pass-type",
        default="SECOND_PASS",
        choices=["FIRST_PASS", "SECOND_PASS", "REMEDIATION_1", "REMEDIATION_2"],
    )
    p_frz.add_argument("--threshold", type=float, default=0.60)
    p_frz.add_argument("--version-label", default="dataset_v1")
    p_frz.set_defaults(func=cmd_freeze)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
