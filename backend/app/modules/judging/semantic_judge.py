"""Secondary independent semantic judge for dual-judge consensus verification."""

import re
import uuid

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData
from app.schemas.verification import JudgeDecision

_KNOWN_CITIES = {
    "paris",
    "berlin",
    "london",
    "rome",
    "madrid",
    "tokyo",
    "beijing",
    "washington",
    "moscow",
    "ottawa",
    "cairo",
    "canberra",
    "delhi",
    "brasilia",
}

_KNOWN_COUNTRIES = {
    "france",
    "germany",
    "italy",
    "spain",
    "japan",
    "china",
    "usa",
    "russia",
    "canada",
    "egypt",
    "australia",
    "india",
    "brazil",
    "uk",
}


class SecondarySemanticJudge(BaseJudge):
    """Secondary judge evaluating directional inclusion and entity matching."""

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
        if not evidence_items:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="semantic-nli-v1.0",
                judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
                confidence=None,
                rationale="Zero evidence items supplied to secondary judge.",
                evidence_references=[],
                metadata={"evaluation_method": "SEMANTIC_INSUFFICIENT"},
            )

        claim_clean = claim_text.lower()
        claim_tokens = re.findall(r"\b[a-z0-9]{3,}\b", claim_clean)
        if not claim_tokens:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="semantic-nli-v1.0",
                judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
                confidence=None,
                rationale="Claim does not contain sufficient content tokens.",
                evidence_references=[],
                metadata={"evaluation_method": "SEMANTIC_EMPTY_CLAIM"},
            )

        cited_evidence: list[str] = []
        is_supported = False
        is_contradicted = False
        rationale = ""

        all_evidence_numbers: set[str] = set()
        for it in evidence_items:
            all_evidence_numbers.update(
                re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", it.snippet)
            )

        # Sort evidence items by numeric overlap and token overlap
        claim_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim_text))
        sorted_items = sorted(
            evidence_items,
            key=lambda it: (
                len(
                    claim_nums
                    & set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", it.snippet))
                ),
                len(
                    set(claim_tokens)
                    & set(re.findall(r"\b[a-z0-9]{3,}\b", it.snippet.lower()))
                ),
                it.relevance_score or 0.0,
            ),
            reverse=True,
        )

        for item in sorted_items:
            snippet_clean = item.snippet.lower()
            cited_evidence.append(str(item.id))

            # Numeric consistency check
            snippet_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", item.snippet))

            # Find best-matching sentence in snippet for proposition-level polarity
            best_sent = ""
            best_sent_overlap = 0
            for sent in re.split(r"[.!?;\n]+", snippet_clean):
                s_tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", sent))
                s_overlap = len(set(claim_tokens) & s_tokens)
                if s_overlap > best_sent_overlap:
                    best_sent_overlap = s_overlap
                    best_sent = sent.strip()

            has_sentence_neg = bool(
                re.search(
                    r"\b(?:not|never|no|none|neither|cannot|didn't|wasn't|false|untrue|incorrect)\b",
                    best_sent,
                )
            )

            if claim_nums and snippet_nums:
                num_match = claim_nums.issubset(snippet_nums)
                if not num_match:
                    unmatched_claim_numbers = claim_nums - all_evidence_numbers
                    conflicting_snippet_numbers = snippet_nums - claim_nums
                    shared_tokens = [w for w in claim_tokens if w in snippet_clean]
                    if (
                        unmatched_claim_numbers
                        and conflicting_snippet_numbers
                        and len(shared_tokens) >= 2
                    ):
                        is_contradicted = True
                        rationale = (
                            "Secondary judge detected conflicting numeric values: "
                            f"claim={unmatched_claim_numbers}, "
                            f"source={conflicting_snippet_numbers}."
                        )
                        break

            # Geographic / entity consistency check
            claim_cities = set(claim_tokens) & _KNOWN_CITIES
            snippet_cities = (
                set(re.findall(r"\b[a-z0-9]{3,}\b", snippet_clean)) & _KNOWN_CITIES
            )
            claim_countries = set(claim_tokens) & _KNOWN_COUNTRIES
            snippet_countries = (
                set(re.findall(r"\b[a-z0-9]{3,}\b", snippet_clean)) & _KNOWN_COUNTRIES
            )

            shared_tokens = [w for w in claim_tokens if w in snippet_clean]

            if (
                claim_cities
                and snippet_cities
                and not (claim_cities & snippet_cities)
                and len(shared_tokens) >= 2
            ):
                is_contradicted = True
                c_claim = ", ".join(sorted(claim_cities))
                c_snip = ", ".join(sorted(snippet_cities))
                rationale = (
                    f"Secondary judge detected conflicting entity location: "
                    f"claim asserts '{c_claim}', source specifies '{c_snip}'."
                )
                break

            if (
                claim_countries
                and snippet_countries
                and not (claim_countries & snippet_countries)
                and len(shared_tokens) >= 2
            ):
                is_contradicted = True
                c_claim = ", ".join(sorted(claim_countries))
                c_snip = ", ".join(sorted(snippet_countries))
                rationale = (
                    f"Secondary judge detected conflicting country: "
                    f"claim asserts '{c_claim}', source specifies '{c_snip}'."
                )
                break

            # Polarity / negation mismatch check on best sentence
            has_claim_neg = bool(
                re.search(
                    r"\b(?:not|never|no|none|neither|cannot|didn't|wasn't)\b",
                    claim_clean,
                )
            )
            if has_claim_neg != has_sentence_neg and best_sent_overlap >= 3:
                is_contradicted = True
                rationale = (
                    "Secondary judge detected polarity/negation mismatch "
                    "between claim and evidence."
                )
                break

            # Inclusion count
            contained_tokens = [w for w in claim_tokens if w in snippet_clean]
            containment_ratio = len(contained_tokens) / len(claim_tokens)

            # Strict threshold for secondary support: 60% directional containment
            # and no unresolved entity conflict
            entity_conflict = bool(
                (claim_cities and not (claim_cities & snippet_cities))
                or (claim_countries and not (claim_countries & snippet_countries))
            )
            if containment_ratio >= 0.60 and not entity_conflict:
                is_supported = True
                rationale = (
                    f"Secondary judge confirmed proposition containment "
                    f"({len(contained_tokens)}/{len(claim_tokens)} tokens matched)."
                )
                break

        if is_contradicted:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="semantic-nli-v1.0",
                judgment=JudgeDecision.CONTRADICTED,
                confidence=None,
                rationale=rationale,
                evidence_references=cited_evidence,
                metadata={"evaluation_method": "SEMANTIC_CONTRADICTION"},
            )

        if is_supported:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="semantic-nli-v1.0",
                judgment=JudgeDecision.SUPPORTED,
                confidence=None,
                rationale=rationale,
                evidence_references=cited_evidence,
                metadata={"evaluation_method": "SEMANTIC_SUPPORT"},
            )

        return JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name=self.name,
            model_version="semantic-nli-v1.0",
            judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
            confidence=None,
            rationale="Passages do not satisfy directional containment threshold.",
            evidence_references=cited_evidence,
            metadata={"evaluation_method": "SEMANTIC_INSUFFICIENT"},
        )
