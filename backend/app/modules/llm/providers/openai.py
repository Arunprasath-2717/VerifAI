"""OpenAI and OpenAI-compatible LLM provider adapter."""

import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI and OpenAI-compatible chat completion APIs."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "openai"

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> LLMExecutionResult:
        start_time = time.monotonic()
        api_key = (
            self.settings.OPENAI_API_KEY.get_secret_value()
            if self.settings.OPENAI_API_KEY
            else None
        )
        base_url = self.settings.OPENAI_BASE_URL or "https://api.openai.com/v1"

        if not api_key and "api.openai.com" in base_url:
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider="openai",
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="CREDENTIALS_MISSING",
                error_message="OPENAI_API_KEY is not configured on the server.",
            )

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            elapsed = (time.monotonic() - start_time) * 1000.0

            if resp.status_code != 200:
                return LLMExecutionResult(
                    provider="openai",
                    model_name=model_name,
                    prompt=prompt,
                    status="FAILED",
                    latency_ms=round(elapsed, 2),
                    error_code=f"HTTP_{resp.status_code}",
                    error_message=(
                        f"OpenAI error ({resp.status_code}): {resp.text[:300]}"
                    ),
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return LLMExecutionResult(
                    provider="openai",
                    model_name=model_name,
                    prompt=prompt,
                    status="FAILED",
                    latency_ms=round(elapsed, 2),
                    error_code="EMPTY_CHOICES",
                    error_message="Model returned no completion choices.",
                )

            content = choices[0].get("message", {}).get("content", "")
            return LLMExecutionResult(
                provider="openai",
                model_name=model_name,
                prompt=prompt,
                response=content,
                status="COMPLETED",
                model_version=data.get("model", model_name),
                latency_ms=round(elapsed, 2),
                metadata={"usage": data.get("usage", {})},
            )
