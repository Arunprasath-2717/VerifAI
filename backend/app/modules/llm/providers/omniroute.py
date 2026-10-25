"""OmniRoute / CheaperInference Gateway LLM provider adapter."""

import asyncio
import time

import httpx

from app.core.config import Settings, get_settings
from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.token_budget.estimator import TokenEstimator


class OmniRouteProvider(BaseLLMProvider):
    """Adapter for OmniRoute / CheaperInference API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "omniroute"

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
            self.settings.OMNIROUTE_API_KEY.get_secret_value()
            if self.settings.OMNIROUTE_API_KEY
            else None
        )
        base_url = (
            self.settings.OMNIROUTE_BASE_URL or "https://api.cheaperinference.com/v1"
        )

        if not api_key:
            elapsed = (time.monotonic() - start_time) * 1000.0
            return LLMExecutionResult(
                provider="omniroute",
                model_name=model_name,
                prompt=prompt,
                status="UNAVAILABLE",
                latency_ms=round(elapsed, 2),
                error_code="CREDENTIALS_MISSING",
                error_message="OMNIROUTE_API_KEY is not configured on the server.",
            )

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload: dict = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{base_url.rstrip('/')}/chat/completions"
        max_retries = self.settings.TOKEN_BUDGET_MAX_RETRIES
        retries_used = 0
        last_error = None
        last_status_code = None

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    last_status_code = resp.status_code
                    if resp.status_code == 200:
                        elapsed = (time.monotonic() - start_time) * 1000.0
                        data = resp.json()
                        choices = data.get("choices", [])
                        if not choices:
                            return LLMExecutionResult(
                                provider="omniroute",
                                model_name=model_name,
                                prompt=prompt,
                                status="FAILED",
                                latency_ms=round(elapsed, 2),
                                error_code="EMPTY_CHOICES",
                                error_message=(
                                    "OmniRoute returned no completion choices."
                                ),
                                retry_count=retries_used,
                            )

                        content = choices[0].get("message", {}).get("content", "")
                        usage = data.get("usage") or {}
                        in_tokens = usage.get("prompt_tokens")
                        out_tokens = usage.get("completion_tokens")
                        is_est = False

                        if in_tokens is None or out_tokens is None:
                            in_tokens = TokenEstimator.estimate_tokens(prompt)
                            out_tokens = TokenEstimator.estimate_tokens(content)
                            is_est = True

                        return LLMExecutionResult(
                            provider="omniroute",
                            model_name=model_name,
                            prompt=prompt,
                            response=content,
                            status="COMPLETED",
                            model_version=data.get("model", model_name),
                            latency_ms=round(elapsed, 2),
                            metadata={"usage": usage},
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
                        provider="omniroute",
                        model_name=model_name,
                        prompt=prompt,
                        status="FAILED",
                        latency_ms=round(elapsed, 2),
                        error_code=f"HTTP_{resp.status_code}",
                        error_message=(
                            f"OmniRoute error ({resp.status_code}): {resp.text[:300]}"
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
            provider="omniroute",
            model_name=model_name,
            prompt=prompt,
            status="FAILED",
            latency_ms=round(elapsed, 2),
            error_code="NETWORK_FAILURE" if last_error else f"HTTP_{last_status_code}",
            error_message=str(last_error) if last_error else "Max retries exceeded.",
            retry_count=retries_used,
        )
