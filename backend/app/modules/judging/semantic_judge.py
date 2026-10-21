"""Secondary semantic judge for dual-judge consensus verification."""

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging import lexical
from app.modules.judging import text_analysis as ta
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData

# Fraction of the claim's content words that must appear, in order, within a
# single evidence sentence.
_MIN_ORDERED_CONTAINMENT = 0.6


def _ordered_containment(claim_words: list[str], sentence_words: list[str]) -> int:
    """Length of the longest common subsequence of two word sequences."""
    prev = [0] * (len(sentence_words) + 1)
    for word in claim_words:
        curr = [0]
        for j, other in enumerate(sentence_words, start=1):
            curr.append(prev[j - 1] + 1 if word == other else max(prev[j], curr[-1]))
        prev = curr
    return prev[-1]


def _words(text: str) -> list[str]:
    return [t.norm for t in ta.content_tokens(text) if not t.is_number]


def _sentence_support(
    claim: str, item: RetrievedEvidenceItem
) -> lexical.SupportOutcome:
    """Support requires ordered containment and bound numbers in one sentence."""
    claim_words = _words(claim)
    if not claim_words:
        return lexical.SupportOutcome(False, "Claim has no content words.")
    if ta.missing_entities(claim, item.snippet):
        return lexical.SupportOutcome(False, "Claim entities absent from evidence.")

    for sentence in ta.split_sentences(item.snippet):
        matched = _ordered_containment(claim_words, _words(sentence))
        if matched / len(claim_words) < _MIN_ORDERED_CONTAINMENT:
            continue
        if not ta.check_numbers(claim, sentence).all_matched:
            continue
        return lexical.SupportOutcome(
            True,
            "Secondary judge confirmed ordered proposition containment "
            f"({matched}/{len(claim_words)} words in sequence).",
        )
    return lexical.SupportOutcome(False, "No sentence contains the proposition.")


def _best_sentence_scope(claim: str, snippet: str) -> str:
    sentence, _ = ta.best_aligned_sentence(claim, snippet)
    return sentence or snippet


class SecondarySemanticJudge(BaseJudge):
    """Secondary judge evaluating ordered containment within single sentences."""

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
        """Evaluate claim against evidence using sentence-level containment."""
        return lexical.evaluate(
            judge_name=self.name,
            model_version="semantic-nli-v2.0",
            method_prefix="SEMANTIC",
            claim_text=claim_text,
            evidence_items=evidence_items,
            support_fn=_sentence_support,
            number_scope=_best_sentence_scope,
        )
