"""Real LLM Provider clients with strict absence of mock/fake runtime responses."""

import logging
import time

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult, sanitize_credential_text
from app.modules.llm.providers.registry import LLMProviderRegistry

logger = logging.getLogger("verifai.llm.client")

# Re-export for backward compatibility
__all__ = ["RealLLMClient", "LLMExecutionResult", "sanitize_credential_text"]


class RealLLMClient:
    """Coordinates execution against configured LLM provider strategy adapters."""

    def __init__(
        self,
        settings: Settings | None = None,
        registry: LLMProviderRegistry | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.registry = registry or LLMProviderRegistry(settings=self.settings)

    async def execute_model(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
        max_tokens: int | None = None,
        operation: str = "COMPLETION",
    ) -> LLMExecutionResult:
        """Execute prompt against a provider strategy with error normalization."""
        start_time = time.monotonic()
        adapter = self.registry.get(provider)
        if not adapter:
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider=provider,
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="UNSUPPORTED_PROVIDER",
                error_message=f"Provider '{provider}' is not supported by VerifAI.",
            )

        try:
            return await adapter.execute(
                model_name=model_name,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
                max_tokens=max_tokens,
                operation=operation,
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start_time) * 1000.0
            clean_err = sanitize_credential_text(str(exc))
            logger.warning(
                "Execution failed for provider '%s', model '%s': %s",
                provider,
                model_name,
                type(exc).__name__,
            )
            return LLMExecutionResult(
                provider=provider,
                model_name=model_name,
                prompt=prompt,
                status="FAILED",
                latency_ms=round(elapsed, 2),
                error_code=type(exc).__name__.upper(),
                error_message=clean_err or "Provider API invocation failed.",
            )
