"""Secondary independent semantic judge for dual-judge consensus verification."""

import re
import uuid

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData
from app.schemas.verification import JudgeDecision


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

        for item in evidence_items:
            snippet_clean = item.snippet.lower()
            cited_evidence.append(str(item.id))

            # Numeric consistency check
            claim_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim_text))
            snippet_nums = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", item.snippet))

            if claim_nums and snippet_nums and not (claim_nums & snippet_nums):
                # Only flag contradiction if significant topic keywords align
                shared_tokens = [w for w in claim_tokens if w in snippet_clean]
                if len(shared_tokens) >= 2:
                    is_contradicted = True
                    rationale = (
                        f"Secondary judge detected conflicting numeric values: "
                        f"expected {claim_nums}, found {snippet_nums} in source."
                    )
                    break

            # Inclusion count
            contained_tokens = [w for w in claim_tokens if w in snippet_clean]
            containment_ratio = len(contained_tokens) / len(claim_tokens)

            # Strict threshold for secondary support: 60% directional containment
            if containment_ratio >= 0.60:
                is_supported = True
                rationale = (
                    f"Secondary judge confirmed proposition containment "
                    f"({len(contained_tokens)}/{len(claim_tokens)} tokens matched)."
                )

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
