"""Ollama local LLM provider adapter."""

import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.token_budget.estimator import TokenEstimator


class OllamaProvider(BaseLLMProvider):
    """Adapter for local Ollama API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "ollama"

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
        max_tokens: int | None = None,
        operation: str = "COMPLETION",
    ) -> LLMExecutionResult:
        start_time = time.monotonic()
        base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/chat"
        payload: dict = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if max_tokens is not None:
            payload["options"] = {"num_predict": max_tokens}

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                elapsed = (time.monotonic() - start_time) * 1000.0

                if resp.status_code != 200:
                    return LLMExecutionResult(
                        provider="ollama",
                        model_name=model_name,
                        prompt=prompt,
                        status="FAILED",
                        latency_ms=round(elapsed, 2),
                        error_code=f"HTTP_{resp.status_code}",
                        error_message=(
                            f"Ollama error ({resp.status_code}): {resp.text[:300]}"
                        ),
                    )

                data = resp.json()
                content = data.get("message", {}).get("content", "")
                prompt_tokens = data.get("prompt_eval_count")
                eval_tokens = data.get("eval_count")
                is_est = False

                if prompt_tokens is None or eval_tokens is None:
                    prompt_tokens = TokenEstimator.estimate_tokens(prompt)
                    eval_tokens = TokenEstimator.estimate_tokens(content)
                    is_est = True

                return LLMExecutionResult(
                    provider="ollama",
                    model_name=model_name,
                    prompt=prompt,
                    response=content,
                    status="COMPLETED",
                    model_version=model_name,
                    latency_ms=round(elapsed, 2),
                    metadata={
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": eval_tokens,
                            "total_tokens": (prompt_tokens or 0) + (eval_tokens or 0),
                        }
                    },
                    input_tokens=prompt_tokens,
                    output_tokens=eval_tokens,
                    is_estimated_usage=is_est,
                )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider="ollama",
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="CONNECTION_REFUSED",
                error_message=(
                    f"Cannot connect to Ollama daemon at '{base_url}'. "
                    "Is Ollama running?"
                ),
            )
