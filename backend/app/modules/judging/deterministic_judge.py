"""Deterministic rule-based NLI judge for claim-evidence verification.

Contradiction detection is shared with the semantic judge via ``lexical``; this
judge differs in how it establishes support: unordered content-word coverage of
the whole evidence passage, with every claim number and entity present.
"""

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging import lexical
from app.modules.judging import text_analysis as ta
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData

# Fraction of claim terms (content words and numbers) that must appear in a passage.
MIN_COVERAGE = 0.5


def _rule_support(claim: str, item: RetrievedEvidenceItem) -> lexical.SupportOutcome:
    snippet = item.snippet
    claim_terms = ta.content_terms(claim) | ta.numbers(claim)
    snippet_terms = ta.content_terms(snippet) | ta.numbers(snippet)
    coverage = len(claim_terms & snippet_terms) / len(claim_terms)
    if coverage < MIN_COVERAGE:
        return lexical.SupportOutcome(False, "coverage below threshold")
    if ta.numbers(claim) - ta.numbers(snippet):
        return lexical.SupportOutcome(False, "claim number absent from passage")
    if ta.missing_entities(claim, snippet):
        return lexical.SupportOutcome(False, "claim entity absent from passage")
    # A negated claim is only supported by a passage that negates the same
    # proposition; a positive passage about the subject does not support it.
    if ta.has_negation(claim) != ta.has_negation(
        ta.best_aligned_sentence(claim, snippet)[0], evidence=True
    ):
        return lexical.SupportOutcome(False, "polarity differs from passage")
    return lexical.SupportOutcome(
        True,
        "Evidence passage confirms key entities and propositions "
        f"(term coverage: {len(claim_terms & snippet_terms)}/{len(claim_terms)}).",
    )


def _whole_passage(_claim: str, snippet: str) -> str:
    return snippet


class DeterministicRuleJudge(BaseJudge):
    """Deterministic judge: shared contradiction checks plus passage-level coverage."""

    def __init__(self, name: str = "Judge-Deterministic-Primary") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(
        self,
        claim_text: str,
        evidence_items: list[RetrievedEvidenceItem],
    ) -> JudgeEvaluationData:
        """Evaluate factual entailment between claim and evidence passages."""
        return lexical.evaluate(
            judge_name=self.name,
            model_version="rule-nli-v1.0",
            method_prefix="RULE_BASED",
            claim_text=claim_text,
            evidence_items=evidence_items,
            support_fn=_rule_support,
            number_scope=_whole_passage,
        )
