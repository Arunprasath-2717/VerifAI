"""Common evaluation loop for the deterministic lexical judges.

Both hermetic judges share the contradiction primitives in ``text_analysis`` and
differ in how they establish *support*:

- the rule judge measures unordered content-word coverage over the whole
  evidence snippet;
- the semantic judge requires ordered phrase containment within a single
  evidence sentence and binds numbers within that sentence only.

Because they share primitives their errors are correlated; genuine judge
independence requires configuring the model judge (see ``model_judge``).
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging import text_analysis as ta
from app.modules.judging.models import JudgeEvaluationData
from app.schemas.verification import JudgeDecision

# A passage must share this many content words/numbers with the claim to count
# as on-topic at all.
MIN_TOPICAL_OVERLAP = 2
# Polarity is only compared when the best-aligned sentence is clearly about the
# same proposition: it must share at least this many claim terms, and at least
# MIN_POLARITY_COVERAGE of them.
MIN_POLARITY_OVERLAP = 2
MIN_POLARITY_COVERAGE = 0.6


@dataclass(frozen=True)
class SupportOutcome:
    supported: bool
    reason: str


SupportFn = Callable[[str, RetrievedEvidenceItem], SupportOutcome]
NumberScopeFn = Callable[[str, str], str]


def _is_anchored(claim: str, snippet: str) -> bool:
    """True when the passage is about the claim's subject.

    Claims without proper nouns cannot be anchored by entity and pass trivially.
    """
    names = ta.proper_nouns(claim)
    return not names or bool(names & ta.content_terms(snippet))


def find_contradiction(
    claim: str, snippet: str, number_scope: NumberScopeFn
) -> str | None:
    """Return a contradiction rationale, or None if no contradiction is detected."""
    if not _is_anchored(claim, snippet):
        return None

    number_text = number_scope(claim, snippet)
    conflict = ta.check_numbers(claim, number_text).conflict
    if conflict is not None:
        claim_value, evidence_value = conflict
        return (
            f"Numeric discrepancy: claim states {claim_value} where evidence "
            f"states {evidence_value} for the same quantity."
        )

    year_conflict = ta.check_year_conflict(claim, snippet)
    if year_conflict is not None:
        claim_year, evidence_year = year_conflict
        return (
            f"Numeric discrepancy: claim dates the event to {claim_year} where "
            f"evidence states {evidence_year}."
        )

    substitution = ta.find_substitution(claim, snippet)
    if substitution is not None:
        claim_entity, evidence_entity = substitution
        return (
            f"Entity mismatch: claim names '{claim_entity}' where evidence "
            f"names '{evidence_entity}' in the same role."
        )

    best_sentence, best_overlap = ta.best_aligned_sentence(claim, snippet)
    claim_term_count = len(ta.content_terms(claim) | ta.numbers(claim))
    aligned = best_overlap >= max(
        MIN_POLARITY_OVERLAP, MIN_POLARITY_COVERAGE * claim_term_count
    )
    if aligned and ta.has_negation(claim) != ta.has_negation(
        best_sentence, evidence=True
    ):
        return "Polarity mismatch: negation differs between claim and evidence."
    return None


def evaluate(
    *,
    judge_name: str,
    model_version: str,
    method_prefix: str,
    claim_text: str,
    evidence_items: list[RetrievedEvidenceItem],
    support_fn: SupportFn,
    number_scope: NumberScopeFn,
) -> JudgeEvaluationData:
    """Run the shared contradiction checks and judge-specific support test."""

    def result(
        judgment: JudgeDecision, rationale: str, method: str, refs: list[str]
    ) -> JudgeEvaluationData:
        return JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name=judge_name,
            model_version=model_version,
            judgment=judgment,
            confidence=None,
            rationale=rationale,
            evidence_references=refs,
            metadata={"evaluation_method": f"{method_prefix}_{method}"},
        )

    if not evidence_items:
        return result(
            JudgeDecision.INSUFFICIENT_EVIDENCE,
            "No retrieved evidence passages were provided for evaluation.",
            "INSUFFICIENT",
            [],
        )

    claim_terms = ta.content_terms(claim_text) | ta.numbers(claim_text)
    if not claim_terms:
        return result(
            JudgeDecision.INSUFFICIENT_EVIDENCE,
            "Claim does not contain sufficient content tokens.",
            "EMPTY_CLAIM",
            [],
        )

    cited: list[str] = []
    contradictions: list[str] = []
    supports: list[str] = []
    for item in evidence_items:
        snippet = item.snippet
        snippet_terms = ta.content_terms(snippet) | ta.numbers(snippet)
        if len(claim_terms & snippet_terms) < MIN_TOPICAL_OVERLAP:
            continue
        cited.append(str(item.id))

        contradiction = find_contradiction(claim_text, snippet, number_scope)
        if contradiction is not None:
            contradictions.append(contradiction)
            continue
        outcome = support_fn(claim_text, item)
        if outcome.supported:
            supports.append(outcome.reason)

    if contradictions and supports:
        return result(
            JudgeDecision.INSUFFICIENT_EVIDENCE,
            "Evidence passages conflict: some support the claim while others "
            f"contradict it ({contradictions[0]})",
            "CONFLICTING",
            cited,
        )
    if contradictions:
        return result(
            JudgeDecision.CONTRADICTED, contradictions[0], "CONTRADICTION", cited
        )
    if supports:
        return result(JudgeDecision.SUPPORTED, supports[0], "SUPPORT", cited)
    return result(
        JudgeDecision.INSUFFICIENT_EVIDENCE,
        "Evidence passages did not contain sufficient assertions to prove or "
        "disprove the claim.",
        "INCONCLUSIVE",
        cited,
    )
