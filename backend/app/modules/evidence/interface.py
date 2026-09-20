"""Abstract interface for pluggable evidence retrieval providers."""

from abc import ABC, abstractmethod

from app.modules.evidence.models import RetrievedEvidenceItem


class BaseEvidenceRetriever(ABC):
    """Abstract interface for evidence retrieval services."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the retriever provider."""
        pass

    @abstractmethod
    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        """Retrieve relevant evidence passages for the given claim."""
        pass
