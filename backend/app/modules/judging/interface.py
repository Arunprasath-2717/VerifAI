"""Abstract interface for independent LLM and heuristic judges."""

from abc import ABC, abstractmethod

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.models import JudgeEvaluationData


class BaseJudge(ABC):
    """Abstract interface for evidence verification judges."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the judge."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        claim_text: str,
        evidence_items: list[RetrievedEvidenceItem],
    ) -> JudgeEvaluationData:
        """Evaluate if evidence supports, contradicts, or leaves claim unknown."""
        pass
