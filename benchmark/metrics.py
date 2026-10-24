"""Deterministic, pure-Python inter-annotator agreement metrics."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KappaResult:
    """Detailed results of a Cohen's kappa agreement evaluation."""

    kappa: float | None
    observed_agreement: float
    expected_agreement: float
    n_items: int
    agreement_count: int
    disagreement_count: int
    confusion_matrix: dict[str, dict[str, int]] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    is_valid: bool = True
    message: str = "Success"


def compute_cohens_kappa(
    annotations_1: dict[str, str],
    annotations_2: dict[str, str],
) -> KappaResult:
    """Compute Cohen's kappa coefficient between two sets of annotations.

    Compares atomic claim labels matching on claim identifier.
    Formula:
        kappa = (P_o - P_e) / (1 - P_e)
    Where:
        P_o = observed proportional agreement
        P_e = expected chance agreement based on marginal label distributions

    Zero-dependency, deterministic implementation.
    """
    # Identify items present in both annotation sets
    common_keys = sorted(set(annotations_1.keys()) & set(annotations_2.keys()))
    n_items = len(common_keys)

    if n_items == 0:
        return KappaResult(
            kappa=None,
            observed_agreement=0.0,
            expected_agreement=0.0,
            n_items=0,
            agreement_count=0,
            disagreement_count=0,
            confusion_matrix={},
            categories=[],
            is_valid=False,
            message="Insufficient data: No common annotated claims to compare.",
        )

    # Collect labels for both annotators on matching items
    labels_1 = [annotations_1[k] for k in common_keys]
    labels_2 = [annotations_2[k] for k in common_keys]

    all_categories = sorted(set(labels_1) | set(labels_2))

    # Initialize confusion matrix: row = annotator 1, col = annotator 2
    matrix: dict[str, dict[str, int]] = {
        cat1: dict.fromkeys(all_categories, 0) for cat1 in all_categories
    }

    agreement_count = 0
    for l1, l2 in zip(labels_1, labels_2, strict=True):
        matrix[l1][l2] += 1
        if l1 == l2:
            agreement_count += 1

    disagreement_count = n_items - agreement_count
    p_o = agreement_count / n_items

    # Marginal totals
    marginals_1: dict[str, int] = dict.fromkeys(all_categories, 0)
    marginals_2: dict[str, int] = dict.fromkeys(all_categories, 0)

    for cat in all_categories:
        marginals_1[cat] = sum(matrix[cat][c2] for c2 in all_categories)
        marginals_2[cat] = sum(matrix[c1][cat] for c1 in all_categories)

    # Expected chance agreement: sum of products of marginal probabilities
    p_e = sum(
        (marginals_1[cat] / n_items) * (marginals_2[cat] / n_items)
        for cat in all_categories
    )

    # Edge case: perfect chance agreement (denominator = 0)
    denominator = 1.0 - p_e
    if abs(denominator) < 1e-12:
        # Both annotators used exclusively one category
        kappa = 1.0 if abs(p_o - 1.0) < 1e-12 else 0.0
    else:
        raw_kappa = (p_o - p_e) / denominator
        # Round to 4 decimal places for clean deterministic reporting
        kappa = round(raw_kappa, 4)

    return KappaResult(
        kappa=kappa,
        observed_agreement=round(p_o, 4),
        expected_agreement=round(p_e, 4),
        n_items=n_items,
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        confusion_matrix=matrix,
        categories=all_categories,
        is_valid=True,
        message="Cohen's kappa evaluated successfully.",
    )
