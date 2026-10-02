"""Multi-LLM Orchestrator executing 1 to 3 models with parallel failure isolation."""

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.modules.llm.client import LLMExecutionResult, RealLLMClient
from app.schemas.chat import LLMModelSelection

logger = logging.getLogger("verifai.llm.orchestrator")


class MultiLLMOrchestrator:
    """Manages parallel dispatch and execution across 1 to 3 LLM providers."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: RealLLMClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or RealLLMClient(settings=self.settings)

    async def execute_models(
        self,
        prompt: str,
        models: list[LLMModelSelection],
    ) -> list[LLMExecutionResult]:
        """Execute between 1 and 3 models in parallel with strict failure isolation."""
        if not (1 <= len(models) <= 3):
            raise ValueError(
                f"Between 1 and 3 models must be specified (received {len(models)})."
            )

        timeout = self.settings.LLM_TIMEOUT_SECONDS

        async def _run_single(selection: LLMModelSelection) -> LLMExecutionResult:
            try:
                return await self.client.execute_model(
                    provider=selection.provider,
                    model_name=selection.model_name,
                    prompt=prompt,
                    timeout_seconds=timeout,
                )
            except Exception as exc:
                logger.error(
                    "Unexpected error executing %s/%s: %s",
                    selection.provider,
                    selection.model_name,
                    exc,
                )
                return LLMExecutionResult(
                    provider=selection.provider,
                    model_name=selection.model_name,
                    prompt=prompt,
                    status="FAILED",
                    error_code="UNEXPECTED_EXECUTION_ERROR",
                    error_message=str(exc),
                )

        tasks = [_run_single(m) for m in models]
        raw_results = await asyncio.gather(*tasks, return_exceptions=False)

        results: list[LLMExecutionResult] = []
        for r in raw_results:
            results.append(r)

        return results
