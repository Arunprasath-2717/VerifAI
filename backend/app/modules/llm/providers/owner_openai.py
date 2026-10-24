"""Request-scoped OpenAI-compatible inference (NVIDIA NIM and secure custom BYOK).

Never uses a global API key. Unsafe/private endpoint URLs are rejected before
sending a bearer token, and upstream bodies do not flow into user-facing errors.
"""

from __future__ import annotations

import time

import httpx

from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.providers.chat_specs import credential_provider_id
from app.modules.providers.openai_compatible import resolve_openai_base_url


class OwnerOpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        provider_id: str,
        provider_name: str,
        base_url: str | None,
        api_key: str,
    ) -> None:
        self._name = provider_id
        self._provider_name = provider_name
        self._base_url = base_url
        self._api_key = api_key

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
        max_tokens: int | None = None,
        operation: str = "COMPLETION",
    ) -> LLMExecutionResult:
        started = time.monotonic()

        def result(
            status: str,
            *,
            answer: str | None = None,
            code: str | None = None,
            message: str | None = None,
            version: str | None = None,
        ) -> LLMExecutionResult:
            return LLMExecutionResult(
                provider=self._name,
                model_name=model_name,
                prompt=prompt,
                response=answer,
                status=status,
                model_version=version,
                error_code=code,
                error_message=message,
                latency_ms=round((time.monotonic() - started) * 1000, 2),
            )

        if not self._api_key:
            return result(
                "UNAVAILABLE",
                code="CREDENTIALS_MISSING",
                message="Your provider key is missing or not verified.",
            )
        transport = CHAT_PROVIDER_TRANSPORT.get()
        try:
            url = (
                resolve_openai_base_url(
                    credential_provider_id(self._name),
                    self._base_url,
                    self._provider_name,
                    resolve_dns=transport is None,
                )
                + "/chat/completions"
            )
        except Exception:
            return result(
                "UNAVAILABLE",
                code="UNSAFE_ENDPOINT",
                message="Provider endpoint is invalid or unsafe. Review the base URL.",
            )
        payload: dict[str, object] = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if max_tokens is not None:
            # Recent OpenAI reasoning families require max_completion_tokens.
            # Generic OpenAI-compatible providers may only accept max_tokens.
            if self._name == "groq" or (
                self._name == "openai" and model_name.lower().startswith(
                    ("gpt-5", "gpt-6", "o1", "o3", "o4")
                )
            ):
                payload["max_completion_tokens"] = max_tokens
            else:
                payload["max_tokens"] = max_tokens
            # Small reasoning probes otherwise exhaust output tokens without visible text.
            if (self._name == "groq"
                and model_name.lower() in ("openai/gpt-oss-120b", "openai/gpt-oss-20b")
                and max_tokens <= 256):
                payload["reasoning_effort"] = "low"
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_seconds),
                transport=transport,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            if response.status_code != 200:
                return result(
                    "FAILED",
                    code=f"HTTP_{response.status_code}",
                    message=(
                        f"Inference provider returned HTTP {response.status_code}. "
                        "Check model permissions, quota and endpoint availability."
                    ),
                )
            data = response.json()
            choices = data.get("choices") or []
            selected = choices[0] if choices and isinstance(choices[0], dict) else {}
            message = selected.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, list):
                content = "\n".join(
                    part.get("text", "") for part in content
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                )
            if not isinstance(content, str) or not content.strip():
                exhausted = selected.get("finish_reason") == "length"
                return result(
                    "FAILED",
                    code="EMPTY_OUTPUT_BUDGET" if exhausted else "EMPTY_RESPONSE",
                    message=("Model exhausted the output budget without visible text."
                             if exhausted else "The provider did not return a text completion."),
                )
            return result(
                "COMPLETED",
                answer=content,
                version=data.get("model")
                if isinstance(data.get("model"), str)
                else model_name,
            )
        except (httpx.TimeoutException, httpx.NetworkError):
            return result(
                "FAILED",
                code="NETWORK_FAILURE",
                message="The provider timed out or could not be reached.",
            )
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            return result(
                "FAILED",
                code="INVALID_PROVIDER_RESPONSE",
                message="The provider returned an invalid response.",
            )
