"""Google Gemini LLM provider adapter."""

import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Adapter for Google Gemini GenerativeLanguage API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "google"

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> LLMExecutionResult:
        start_time = time.monotonic()
        api_key = (
            self.settings.GEMINI_API_KEY.get_secret_value()
            if self.settings.GEMINI_API_KEY
            else None
        )
        if not api_key:
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider="google",
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="CREDENTIALS_MISSING",
                error_message="GEMINI_API_KEY is not configured on the server.",
            )

        clean_model = (
            model_name if model_name.startswith("models/") else f"models/{model_name}"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/{clean_model}:generateContent"
            f"?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            elapsed = (time.monotonic() - start_time) * 1000.0

            if resp.status_code != 200:
                return LLMExecutionResult(
                    provider="google",
                    model_name=model_name,
                    prompt=prompt,
                    status="FAILED",
                    latency_ms=round(elapsed, 2),
                    error_code=f"HTTP_{resp.status_code}",
                    error_message=(
                        f"Gemini error ({resp.status_code}): {resp.text[:300]}"
                    ),
                )

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return LLMExecutionResult(
                    provider="google",
                    model_name=model_name,
                    prompt=prompt,
                    status="FAILED",
                    latency_ms=round(elapsed, 2),
                    error_code="EMPTY_CANDIDATES",
                    error_message="Gemini returned no response candidates.",
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            text_result = "".join(p.get("text", "") for p in parts)
            return LLMExecutionResult(
                provider="google",
                model_name=model_name,
                prompt=prompt,
                response=text_result,
                status="COMPLETED",
                model_version=model_name,
                latency_ms=round(elapsed, 2),
            )
