"""Deterministic rule-based NLI judge for claim-evidence verification."""

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


class DeterministicRuleJudge(BaseJudge):
    """Deterministic judge verifying factual alignment, numbers, and negations."""

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
        if not evidence_items:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="rule-nli-v1.0",
                judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
                confidence=None,
                rationale=(
                    "No retrieved evidence passages were provided for evaluation."
                ),
                evidence_references=[],
                metadata={"evaluation_method": "RULE_BASED_INSUFFICIENT"},
            )

        claim_clean = claim_text.lower()
        claim_tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", claim_clean))
        claim_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim_text))
        has_claim_negation = bool(
            re.search(
                r"\b(?:not|never|no|none|neither|cannot|didn't|wasn't)\b",
                claim_clean,
            )
        )

        cited_evidence: list[str] = []
        contradiction_found = False
        support_found = False
        contradiction_reason: str | None = None
        support_reason: str | None = None

        for item in evidence_items:
            snippet_clean = item.snippet.lower()
            snippet_tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", snippet_clean))
            snippet_numbers = set(
                re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", item.snippet)
            )
            has_snippet_negation = bool(
                re.search(
                    r"\b(?:not|never|no|none|neither|cannot|didn't|wasn't|false|untrue|incorrect)\b",
                    snippet_clean,
                )
            )

            # Check for topic relevance first
            overlap = len(claim_tokens & snippet_tokens)
            if overlap < 2 and not (claim_numbers & snippet_numbers):
                continue

            cited_evidence.append(str(item.id))

            # 1. Contradiction Check: Numeric Discrepancy on shared topic
            # If claim has specific numbers and snippet has different numbers
            if claim_numbers and snippet_numbers:
                discrepancy = bool(
                    (claim_numbers - snippet_numbers)
                    and (snippet_numbers - claim_numbers)
                )
                has_num_conflict = not (claim_numbers & snippet_numbers) or discrepancy
                if has_num_conflict and overlap >= 2:
                    contradiction_found = True
                    contradiction_reason = (
                        f"Numeric discrepancy: claim asserts {claim_numbers} while "
                        f"evidence states {snippet_numbers}."
                    )
                    break

            # 2. Contradiction Check: Polar Negation Mismatch
            if has_claim_negation != has_snippet_negation and overlap >= 3:
                contradiction_found = True
                contradiction_reason = (
                    "Polarity mismatch: negation detected between claim and evidence."
                )
                break

            # 3. Contradiction Check: Conflicting Geographic / Entity Locations
            claim_cities = claim_tokens & _KNOWN_CITIES
            snippet_cities = snippet_tokens & _KNOWN_CITIES
            if (
                claim_cities
                and snippet_cities
                and not (claim_cities & snippet_cities)
                and overlap >= 2
            ):
                contradiction_found = True
                c_claim = ", ".join(sorted(claim_cities))
                c_snip = ", ".join(sorted(snippet_cities))
                contradiction_reason = (
                    f"Geographic discrepancy: claim asserts location '{c_claim}' "
                    f"while evidence specifies '{c_snip}'."
                )
                break

            claim_countries = claim_tokens & _KNOWN_COUNTRIES
            snippet_countries = snippet_tokens & _KNOWN_COUNTRIES
            if (
                claim_countries
                and snippet_countries
                and not (claim_countries & snippet_countries)
                and overlap >= 2
            ):
                contradiction_found = True
                c_claim = ", ".join(sorted(claim_countries))
                c_snip = ", ".join(sorted(snippet_countries))
                contradiction_reason = (
                    f"Geographic discrepancy: claim asserts country '{c_claim}' "
                    f"while evidence specifies '{c_snip}'."
                )
                break

            # 4. Support Check: High token overlap, numbers and entities verified
            entity_conflict = bool(
                (claim_cities and not (claim_cities & snippet_cities))
                or (claim_countries and not (claim_countries & snippet_countries))
            )
            num_match = (not claim_numbers) or claim_numbers.issubset(snippet_numbers)
            overlap_ratio = overlap / max(1, len(claim_tokens))

            if overlap_ratio >= 0.50 and num_match and not entity_conflict:
                support_found = True
                support_reason = (
                    f"Evidence passage confirms key entities and propositions "
                    f"(token overlap: {overlap}/{len(claim_tokens)})."
                )

        if contradiction_found:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="rule-nli-v1.0",
                judgment=JudgeDecision.CONTRADICTED,
                confidence=None,
                rationale=contradiction_reason or "Contradicted by evidence passage.",
                evidence_references=cited_evidence,
                metadata={"evaluation_method": "RULE_BASED_CONTRADICTION"},
            )

        if support_found:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version="rule-nli-v1.0",
                judgment=JudgeDecision.SUPPORTED,
                confidence=None,
                rationale=support_reason or "Supported by evidence passage.",
                evidence_references=cited_evidence,
                metadata={"evaluation_method": "RULE_BASED_SUPPORT"},
            )

        return JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name=self.name,
            model_version="rule-nli-v1.0",
            judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
            confidence=None,
            rationale=(
                "Evidence passages did not contain sufficient assertions "
                "to prove or disprove claim."
            ),
            evidence_references=cited_evidence,
            metadata={"evaluation_method": "RULE_BASED_INCONCLUSIVE"},
        )
