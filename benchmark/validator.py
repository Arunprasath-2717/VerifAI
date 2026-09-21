"""Validation suite for VerifAI benchmark datasets."""

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from benchmark.schemas import (
    BenchmarkCase,
    BenchmarkCategory,
    VerdictType,
)


@dataclass
class ValidationReport:
    """Detailed dataset validation report."""

    is_valid: bool = True
    total_cases: int = 0
    category_counts: dict[str, int] = field(default_factory=dict)
    split_counts: dict[str, int] = field(default_factory=dict)
    total_claims: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_benchmark_case(case: BenchmarkCase) -> list[str]:
    """Validate semantic constraints for an individual benchmark case."""
    errors: list[str] = []

    # Verify atomic claim offsets against the actual response string
    resp_len = len(case.response)
    for claim in case.atomic_claims:
        if claim.start_offset >= claim.end_offset:
            errors.append(
                f"Case {case.case_id}: Claim {claim.claim_id} has invalid offsets "
                f"[{claim.start_offset}:{claim.end_offset}]."
            )
        if claim.end_offset > resp_len:
            errors.append(
                f"Case {case.case_id}: Claim {claim.claim_id} end_offset "
                f"({claim.end_offset}) exceeds response length ({resp_len})."
            )

    # Verify category and expected verdict correlation
    if case.category == BenchmarkCategory.VERIFIED_FACT:
        if case.expected_verdict != VerdictType.SUPPORTED:
            errors.append(
                f"Case {case.case_id}: VERIFIED_FACT expects verdict SUPPORTED, "
                f"got {case.expected_verdict}."
            )
    elif case.category == BenchmarkCategory.CONTROLLED_HALLUCINATION:
        if case.expected_verdict != VerdictType.CONTRADICTED:
            errors.append(
                f"Case {case.case_id}: CONTROLLED_HALLUCINATION expects verdict "
                f"CONTRADICTED, got {case.expected_verdict}."
            )
    elif case.category == BenchmarkCategory.TRUE_UNKNOWN:
        if case.expected_verdict != VerdictType.UNKNOWN:
            errors.append(
                f"Case {case.case_id}: TRUE_UNKNOWN expects verdict UNKNOWN, "
                f"got {case.expected_verdict}."
            )
        if not case.unknown_reason:
            errors.append(
                f"Case {case.case_id}: TRUE_UNKNOWN case missing unknown_reason."
            )

    return errors


def validate_benchmark_dataset(
    cases: list[BenchmarkCase],
    require_full_100: bool = True,
) -> ValidationReport:
    """Perform comprehensive structural and semantic dataset validation."""
    report = ValidationReport()
    report.total_cases = len(cases)

    seen_case_ids: set[str] = set()
    seen_claim_ids: set[str] = set()

    for case in cases:
        # Check duplicate case IDs
        if case.case_id in seen_case_ids:
            report.errors.append(f"Duplicate case_id detected: '{case.case_id}'.")
        seen_case_ids.add(case.case_id)

        # Check duplicate claim IDs
        for claim in case.atomic_claims:
            if claim.claim_id in seen_claim_ids:
                report.errors.append(
                    f"Duplicate claim_id detected: '{claim.claim_id}'."
                )
            seen_claim_ids.add(claim.claim_id)
            report.total_claims += 1

        # Check semantic case rules
        case_errors = validate_benchmark_case(case)
        report.errors.extend(case_errors)

        # Track categories and splits
        cat_key = case.category.value
        report.category_counts[cat_key] = report.category_counts.get(cat_key, 0) + 1

        split_key = case.split.value
        report.split_counts[split_key] = report.split_counts.get(split_key, 0) + 1

    # PRD Section 8 100-case check
    if require_full_100:
        if report.total_cases != 100:
            report.errors.append(
                f"PRD Section 8 requires exactly 100 cases, found {report.total_cases}."
            )
        expected_breakdown = {
            BenchmarkCategory.VERIFIED_FACT.value: 40,
            BenchmarkCategory.CONTROLLED_HALLUCINATION.value: 30,
            BenchmarkCategory.TRUE_UNKNOWN.value: 30,
        }
        for cat, expected_count in expected_breakdown.items():
            actual_count = report.category_counts.get(cat, 0)
            if actual_count != expected_count:
                report.errors.append(
                    f"Category '{cat}' requires {expected_count} cases, "
                    f"found {actual_count}."
                )

        expected_splits = {
            "dev": 40,
            "test": 60,
        }
        for sp, expected_count in expected_splits.items():
            actual_count = report.split_counts.get(sp, 0)
            if actual_count != expected_count:
                report.errors.append(
                    f"Formal PRD evaluation split '{sp}' requires "
                    f"{expected_count} cases, found {actual_count}."
                )

    report.is_valid = len(report.errors) == 0
    return report


def load_and_validate_dataset_file(
    file_path: Path | str, require_full_100: bool = True
) -> tuple[list[BenchmarkCase] | None, ValidationReport]:
    """Load JSON file and validate against benchmark schema."""
    import json

    report = ValidationReport()
    path = Path(file_path)

    if not path.exists():
        report.errors.append(f"Dataset file not found: {path}")
        report.is_valid = False
        return None, report

    try:
        with open(path, encoding="utf-8") as f:
            raw_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        report.errors.append(f"Failed to parse JSON file {path}: {exc}")
        report.is_valid = False
        return None, report

    if not isinstance(raw_data, list):
        report.errors.append("Dataset root must be a JSON list of cases.")
        report.is_valid = False
        return None, report

    cases: list[BenchmarkCase] = []
    for idx, item in enumerate(raw_data):
        try:
            cases.append(BenchmarkCase.model_validate(item))
        except ValidationError as val_err:
            report.errors.append(f"Case index {idx} failed validation: {val_err}")

    if report.errors:
        report.is_valid = False
        return None, report

    validation_report = validate_benchmark_dataset(
        cases, require_full_100=require_full_100
    )
    return (cases if validation_report.is_valid else None), validation_report
