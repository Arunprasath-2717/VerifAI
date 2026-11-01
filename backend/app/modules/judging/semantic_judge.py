"""Secondary independent semantic judge for dual-judge consensus verification.

Contradiction detection is shared with the rule judge via ``lexical``. This judge
differs in how it establishes support: ordered phrase containment inside a single
evidence sentence, with the claim's numbers bound to that same sentence.
"""

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging import lexical
from app.modules.judging import text_analysis as ta
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData

# Fraction of claim content words that must appear in one evidence sentence.
MIN_SENTENCE_CONTAINMENT = 0.6


def _aligned_sentence(claim: str, snippet: str) -> str:
    best_sentence, _ = ta.best_aligned_sentence(claim, snippet)
    return best_sentence


def _sentence_support(
    claim: str, item: RetrievedEvidenceItem
) -> lexical.SupportOutcome:
    claim_terms = ta.content_terms(claim)
    if not claim_terms:
        return lexical.SupportOutcome(False, "no content terms")
    best_sentence = _aligned_sentence(claim, item.snippet)
    sentence_terms = ta.content_terms(best_sentence) | ta.numbers(best_sentence)
    contained = claim_terms & sentence_terms
    if len(contained) / len(claim_terms) < MIN_SENTENCE_CONTAINMENT:
        return lexical.SupportOutcome(False, "containment below threshold")
    if ta.numbers(claim) - ta.numbers(best_sentence):
        return lexical.SupportOutcome(False, "claim number not in aligned sentence")
    # Entities may be introduced in a neighbouring sentence of the same passage;
    # only the predicate phrase and its numbers must share one sentence.
    if ta.missing_entities(claim, item.snippet):
        return lexical.SupportOutcome(False, "claim entity absent from passage")
    return lexical.SupportOutcome(
        True,
        "Secondary judge confirmed proposition containment within one evidence "
        f"sentence ({len(contained)}/{len(claim_terms)} content terms matched).",
    )


class SecondarySemanticJudge(BaseJudge):
    """Secondary judge: shared contradiction checks plus sentence-level containment."""

    def __init__(self, name: str = "Judge-Semantic-Secondary") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(
        self,
        claim_text: str,
        evidence_items: list[RetrievedEvidenceItem],
    ) -> JudgeEvaluationData:
        """Evaluate claim against evidence using directional containment."""
        return lexical.evaluate(
            judge_name=self.name,
            model_version="semantic-nli-v1.0",
            method_prefix="SEMANTIC",
            claim_text=claim_text,
            evidence_items=evidence_items,
            support_fn=_sentence_support,
            number_scope=_aligned_sentence,
        )
