"""Deterministic rule-based NLI judge for claim-evidence verification."""

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging import lexical
from app.modules.judging import text_analysis as ta
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData

# Fraction of the claim's content words that must appear in a passage.
_MIN_COVERAGE = 0.6


def _snippet_support(claim: str, item: RetrievedEvidenceItem) -> lexical.SupportOutcome:
    """Support requires word coverage, bound numbers, and every named entity."""
    claim_terms = ta.content_terms(claim)
    snippet = item.snippet
    covered = claim_terms & ta.content_terms(snippet)
    coverage = len(covered) / max(1, len(claim_terms))

    if coverage < _MIN_COVERAGE:
        return lexical.SupportOutcome(False, "Insufficient proposition coverage.")
    if not ta.check_numbers(claim, snippet).all_matched:
        return lexical.SupportOutcome(False, "Claim numbers not confirmed.")
    if ta.missing_entities(claim, snippet):
        return lexical.SupportOutcome(False, "Claim entities absent from evidence.")
    return lexical.SupportOutcome(
        True,
        "Evidence passage confirms key entities, quantities, and propositions "
        f"(token coverage: {len(covered)}/{len(claim_terms)}).",
    )


class DeterministicRuleJudge(BaseJudge):
    """Deterministic judge verifying entities, bound quantities, and negations."""

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
            model_version="rule-nli-v2.0",
            method_prefix="RULE_BASED",
            claim_text=claim_text,
            evidence_items=evidence_items,
            support_fn=_snippet_support,
            number_scope=lambda _claim, snippet: snippet,
        )
