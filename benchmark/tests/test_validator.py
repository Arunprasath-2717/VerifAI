"""Unit tests for benchmark.validator — dataset semantic validation rules.

Covers single-case validation and full dataset validation.
Does NOT require the actual 100-case dataset file (uses fabricated cases).
"""

from benchmark.schemas import (
    AtomicClaim,
    BenchmarkCase,
    BenchmarkCategory,
    ClaimLabel,
    ContentType,
    DatasetSplit,
    UnknownReason,
    VerdictType,
)
from benchmark.validator import (
    ValidationReport,
    validate_benchmark_case,
    validate_benchmark_dataset,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claim(
    claim_id: str = "c1",
    text: str = "The capital of France is Paris.",
    start: int = 0,
    end: int = 31,
    label: ClaimLabel = ClaimLabel.SUPPORTED,
) -> AtomicClaim:
    return AtomicClaim(
        claim_id=claim_id,
        claim_text=text,
        start_offset=start,
        end_offset=end,
        gold_label=label,
        expected_evidence=["Query: capital of France"],
    )


def _make_case(
    case_id: str = "CASE-001",
    category: BenchmarkCategory = BenchmarkCategory.VERIFIED_FACT,
    verdict: VerdictType = VerdictType.SUPPORTED,
    response: str = "The capital of France is Paris.",
    claims: list[AtomicClaim] | None = None,
    unknown_reason: UnknownReason | None = None,
    split: DatasetSplit = DatasetSplit.TRAIN,
) -> BenchmarkCase:
    if claims is None:
        claims = [_make_claim(end=len(response))]
    return BenchmarkCase(
        case_id=case_id,
        query="What is the capital of France?",
        response=response,
        category=category,
        content_type=ContentType.FACTUAL,
        expected_verdict=verdict,
        unknown_reason=unknown_reason,
        atomic_claims=claims,
        split=split,
    )


def _make_100_cases() -> list[BenchmarkCase]:
    """Generate a minimal valid 100-case dataset (40 VF, 30 CH, 30 TU)."""
    cases: list[BenchmarkCase] = []
    response = "A" * 50

    # Assign splits: 60 train, 20 dev, 20 test
    split_seq = (
        [DatasetSplit.TRAIN] * 60 + [DatasetSplit.DEV] * 20 + [DatasetSplit.TEST] * 20
    )

    for i in range(40):
        split = split_seq[i]
        cases.append(
            _make_case(
                case_id=f"CASE-VF-{i + 1:03d}",
                category=BenchmarkCategory.VERIFIED_FACT,
                verdict=VerdictType.SUPPORTED,
                response=response,
                split=split,
                claims=[_make_claim(f"c{i}-1", "X", 0, 10)],
            )
        )
    for i in range(30):
        idx = i + 40
        split = split_seq[idx]
        cases.append(
            _make_case(
                case_id=f"CASE-CH-{i + 1:03d}",
                category=BenchmarkCategory.CONTROLLED_HALLUCINATION,
                verdict=VerdictType.CONTRADICTED,
                response=response,
                split=split,
                claims=[_make_claim(f"c{idx}-1", "X", 0, 10, ClaimLabel.CONTRADICTED)],
            )
        )
    for i in range(30):
        idx = i + 70
        split = split_seq[idx]
        cases.append(
            _make_case(
                case_id=f"CASE-TU-{i + 1:03d}",
                category=BenchmarkCategory.TRUE_UNKNOWN,
                verdict=VerdictType.UNKNOWN,
                response=response,
                unknown_reason=UnknownReason.INSUFFICIENT_EVIDENCE,
                split=split,
                claims=[_make_claim(f"c{idx}-1", "X", 0, 10, ClaimLabel.UNKNOWN)],
            )
        )
    return cases


# ---------------------------------------------------------------------------
# Individual case validation
# ---------------------------------------------------------------------------


class TestCaseValidation:
    def test_valid_verified_fact_case_has_no_errors(self):
        case = _make_case()
        errors = validate_benchmark_case(case)
        assert errors == []

    def test_verified_fact_wrong_verdict_gives_error(self):
        case = _make_case(
            category=BenchmarkCategory.VERIFIED_FACT,
            verdict=VerdictType.CONTRADICTED,  # wrong
        )
        errors = validate_benchmark_case(case)
        assert any("VERIFIED_FACT expects verdict SUPPORTED" in e for e in errors)

    def test_controlled_hallucination_wrong_verdict_gives_error(self):
        case = _make_case(
            category=BenchmarkCategory.CONTROLLED_HALLUCINATION,
            verdict=VerdictType.SUPPORTED,  # wrong
        )
        errors = validate_benchmark_case(case)
        assert any(
            "CONTROLLED_HALLUCINATION expects verdict CONTRADICTED" in e for e in errors
        )

    def test_true_unknown_wrong_verdict_gives_error(self):
        case = _make_case(
            category=BenchmarkCategory.TRUE_UNKNOWN,
            verdict=VerdictType.SUPPORTED,  # wrong
        )
        errors = validate_benchmark_case(case)
        assert any("TRUE_UNKNOWN expects verdict UNKNOWN" in e for e in errors)

    def test_true_unknown_missing_unknown_reason_gives_error(self):
        case = _make_case(
            category=BenchmarkCategory.TRUE_UNKNOWN,
            verdict=VerdictType.UNKNOWN,
            unknown_reason=None,  # missing
        )
        errors = validate_benchmark_case(case)
        assert any("missing unknown_reason" in e for e in errors)

    def test_invalid_offset_start_ge_end_gives_error(self):
        claim = _make_claim(claim_id="bad", start=20, end=10)  # start > end
        case = _make_case(claims=[claim])
        errors = validate_benchmark_case(case)
        assert any("invalid offsets" in e for e in errors)

    def test_offset_exceeds_response_length_gives_error(self):
        response = "Short."
        claim = _make_claim(claim_id="oor", start=0, end=999)  # way beyond response
        case = _make_case(response=response, claims=[claim])
        errors = validate_benchmark_case(case)
        assert any("exceeds response length" in e for e in errors)

    def test_valid_hallucination_case_no_errors(self):
        claim = _make_claim(label=ClaimLabel.CONTRADICTED)
        case = _make_case(
            category=BenchmarkCategory.CONTROLLED_HALLUCINATION,
            verdict=VerdictType.CONTRADICTED,
            claims=[claim],
        )
        errors = validate_benchmark_case(case)
        assert errors == []

    def test_valid_unknown_case_no_errors(self):
        claim = _make_claim(label=ClaimLabel.UNKNOWN)
        case = _make_case(
            category=BenchmarkCategory.TRUE_UNKNOWN,
            verdict=VerdictType.UNKNOWN,
            unknown_reason=UnknownReason.CONTEXT_UNKNOWN,
            claims=[claim],
        )
        errors = validate_benchmark_case(case)
        assert errors == []


# ---------------------------------------------------------------------------
# Full dataset validation
# ---------------------------------------------------------------------------


class TestDatasetValidation:
    def test_valid_100_case_dataset_passes(self):
        cases = _make_100_cases()
        report = validate_benchmark_dataset(cases, require_full_100=True)
        assert report.is_valid is True
        assert report.errors == []
        assert report.total_cases == 100

    def test_category_counts_correct(self):
        cases = _make_100_cases()
        report = validate_benchmark_dataset(cases, require_full_100=True)
        assert report.category_counts["VERIFIED_FACT"] == 40
        assert report.category_counts["CONTROLLED_HALLUCINATION"] == 30
        assert report.category_counts["TRUE_UNKNOWN"] == 30

    def test_split_counts_correct(self):
        cases = _make_100_cases()
        report = validate_benchmark_dataset(cases, require_full_100=True)
        assert report.split_counts["train"] == 60
        assert report.split_counts["dev"] == 20
        assert report.split_counts["test"] == 20

    def test_wrong_total_count_gives_error(self):
        cases = _make_100_cases()[:50]  # only 50 cases
        report = validate_benchmark_dataset(cases, require_full_100=True)
        assert report.is_valid is False
        assert any("100 cases" in e for e in report.errors)

    def test_duplicate_case_id_gives_error(self):
        cases = _make_100_cases()
        cases[1].model_copy()
        # Force duplicate by rebuilding first case with same ID
        dup = _make_case(case_id="CASE-VF-001")
        cases.append(dup)
        report = validate_benchmark_dataset([cases[0], dup], require_full_100=False)
        assert any("Duplicate case_id" in e for e in report.errors)

    def test_require_full_100_false_allows_partial_dataset(self):
        cases = _make_100_cases()[:10]
        report = validate_benchmark_dataset(cases, require_full_100=False)
        # No count-based errors expected; only semantic errors
        count_errors = [e for e in report.errors if "100 cases" in e]
        assert count_errors == []

    def test_returns_validation_report_instance(self):
        cases = _make_100_cases()
        report = validate_benchmark_dataset(cases)
        assert isinstance(report, ValidationReport)
