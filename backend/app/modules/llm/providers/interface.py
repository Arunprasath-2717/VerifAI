"""Abstract interface for pluggable LLM provider adapters."""

from abc import ABC, abstractmethod

from app.modules.llm.models import LLMExecutionResult


class BaseLLMProvider(ABC):
    """Normalized contract for LLM provider strategy implementations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Normalized identifier for the provider (e.g. 'groq', 'openrouter')."""
        pass

    @abstractmethod
    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> LLMExecutionResult:
        """Execute a prompt against the provider and return normalized result."""
        pass
