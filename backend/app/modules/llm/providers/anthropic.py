"""Anthropic LLM provider adapter."""

import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic Messages API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "anthropic"

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> LLMExecutionResult:
        start_time = time.monotonic()
        api_key = (
            self.settings.ANTHROPIC_API_KEY.get_secret_value()
            if self.settings.ANTHROPIC_API_KEY
            else None
        )
        if not api_key:
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider="anthropic",
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="CREDENTIALS_MISSING",
                error_message="ANTHROPIC_API_KEY is not configured on the server.",
            )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model_name,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }

        url = "https://api.anthropic.com/v1/messages"
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            elapsed = (time.monotonic() - start_time) * 1000.0

            if resp.status_code != 200:
                return LLMExecutionResult(
                    provider="anthropic",
                    model_name=model_name,
                    prompt=prompt,
                    status="FAILED",
                    latency_ms=round(elapsed, 2),
                    error_code=f"HTTP_{resp.status_code}",
                    error_message=(
                        f"Anthropic error ({resp.status_code}): {resp.text[:300]}"
                    ),
                )

            data = resp.json()
            contents = data.get("content", [])
            text_blocks = [
                c.get("text", "") for c in contents if c.get("type") == "text"
            ]
            return LLMExecutionResult(
                provider="anthropic",
                model_name=model_name,
                prompt=prompt,
                response="\n".join(text_blocks),
                status="COMPLETED",
                model_version=data.get("model", model_name),
                latency_ms=round(elapsed, 2),
                metadata={"usage": data.get("usage", {})},
            )
