"""Google Gemini LLM provider adapter."""

import asyncio
import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.token_budget.estimator import TokenEstimator


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
        max_tokens: int | None = None,
        operation: str = "COMPLETION",
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
        gen_config: dict = {"temperature": 0.3}
        if max_tokens is not None:
            gen_config["maxOutputTokens"] = max_tokens

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config,
        }

        max_retries = self.settings.TOKEN_BUDGET_MAX_RETRIES
        retries_used = 0
        last_error = None
        last_status_code = None

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=payload)
                    last_status_code = resp.status_code
                    if resp.status_code == 200:
                        elapsed = (time.monotonic() - start_time) * 1000.0
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
                                retry_count=retries_used,
                            )

                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_result = "".join(p.get("text", "") for p in parts)
                        usage_meta = data.get("usageMetadata", {})

                        in_tokens = usage_meta.get("promptTokenCount")
                        out_tokens = usage_meta.get("candidatesTokenCount")
                        is_est = False

                        if in_tokens is None or out_tokens is None:
                            in_tokens = TokenEstimator.estimate_tokens(prompt)
                            out_tokens = TokenEstimator.estimate_tokens(text_result)
                            is_est = True

                        return LLMExecutionResult(
                            provider="google",
                            model_name=model_name,
                            prompt=prompt,
                            response=text_result,
                            status="COMPLETED",
                            model_version=model_name,
                            latency_ms=round(elapsed, 2),
                            metadata={"usage": usage_meta},
                            input_tokens=in_tokens,
                            output_tokens=out_tokens,
                            is_estimated_usage=is_est,
                            retry_count=retries_used,
                        )

                    if (
                        resp.status_code in (429, 500, 502, 503, 504)
                        and attempt < max_retries
                    ):
                        retries_used += 1
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue

                    elapsed = (time.monotonic() - start_time) * 1000.0
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
                        retry_count=retries_used,
                    )
                except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                    last_error = net_err
                    if attempt < max_retries:
                        retries_used += 1
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    break

        elapsed = (time.monotonic() - start_time) * 1000.0
        return LLMExecutionResult(
            provider="google",
            model_name=model_name,
            prompt=prompt,
            status="FAILED",
            latency_ms=round(elapsed, 2),
            error_code="NETWORK_FAILURE" if last_error else f"HTTP_{last_status_code}",
            error_message=str(last_error) if last_error else "Max retries exceeded.",
            retry_count=retries_used,
        )
