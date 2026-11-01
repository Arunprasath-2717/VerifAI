"""Owner-scoped Claude Messages and Gemini GenerateContent implementations.

Unlike generic OpenAI-compatible adapters, these providers use native model
APIs. The caller's decrypted key is held only in this request-local instance.
"""

from __future__ import annotations

import re
import time

import httpx

from app.modules.llm.models import LLMExecutionResult
from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.providers.chat_specs import SPECS


class OwnerNativeChatProvider(BaseLLMProvider):
    def __init__(self, provider: str, key: str):
        if provider not in ("anthropic", "google"):
            raise ValueError("Unsupported native BYOK protocol")
        self._name = provider
        self._key = key

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30,
        max_tokens: int | None = None,
        operation: str = "COMPLETION",
    ) -> LLMExecutionResult:
        start = time.monotonic()

        def answer(
            status: str,
            text: str | None = None,
            code: str | None = None,
            message: str | None = None,
        ) -> LLMExecutionResult:
            return LLMExecutionResult(
                provider=self._name,
                model_name=model_name,
                prompt=prompt,
                response=text,
                status=status,
                latency_ms=round((time.monotonic() - start) * 1000, 2),
                error_code=code,
                error_message=message,
            )

        if not self._key:
            return answer(
                "UNAVAILABLE",
                code="CREDENTIALS_MISSING",
                message="No verified provider key.",
            )
        model_id = model_name.removeprefix("models/")
        if not re.fullmatch(r"[a-zA-Z0-9._:-]{2,128}", model_id):
            return answer(
                "UNAVAILABLE",
                code="MODEL_ID_INVALID",
                message="Model identifier is not supported.",
            )
        if self._name == "anthropic":
            url = SPECS["prov-anthropic"].base_url + "/messages"
            headers = {
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model_id,
                "max_tokens": max_tokens or 1250,
                "messages": [{"role": "user", "content": prompt}],
            }
        else:
            url = (
                SPECS["prov-google"].base_url
                + "/models/"
                + model_id
                + ":generateContent"
            )
            headers = {
                "x-goog-api-key": self._key,
                "content-type": "application/json",
            }
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens or 1250},
            }

        try:
            async with httpx.AsyncClient(
                transport=CHAT_PROVIDER_TRANSPORT.get(),
                timeout=httpx.Timeout(timeout_seconds),
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return answer(
                    "FAILED",
                    code=f"HTTP_{response.status_code}",
                    message="Provider rejected the request or quota was exhausted.",
                )
            data = response.json()
            if self._name == "anthropic":
                blocks = data.get("content", [])
                result = "\n".join(
                    block.get("text", "")
                    for block in blocks
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                candidates = data.get("candidates") or []
                parts = (
                    candidates[0].get("content", {}).get("parts", [])
                    if candidates
                    else []
                )
                result = "\n".join(
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                )
            if not result.strip():
                return answer(
                    "FAILED",
                    code="EMPTY_RESPONSE",
                    message="Provider returned no non-empty text.",
                )
            return answer("COMPLETED", text=result)
        except httpx.TimeoutException:
            return answer(
                "FAILED", code="TIMEOUT", message="Provider request timed out."
            )
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError):
            return answer(
                "FAILED",
                code="PROVIDER_ERROR",
                message="Provider response could not be processed.",
            )
