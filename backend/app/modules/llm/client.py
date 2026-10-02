"""Real LLM Provider clients with strict absence of mock/fake runtime responses."""

import logging
import time
from typing import Any

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger("verifai.llm.client")


class LLMExecutionResult:
    """Encapsulates the truthful outcome of a model execution."""

    def __init__(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        response: str | None = None,
        status: str = "COMPLETED",  # COMPLETED, FAILED, UNAVAILABLE
        model_version: str | None = None,
        latency_ms: float | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        self.model_name = model_name
        self.prompt = prompt
        self.response = response
        self.status = status
        self.model_version = model_version
        self.latency_ms = latency_ms
        self.error_code = error_code
        self.error_message = error_message
        self.metadata = metadata or {}


class RealLLMClient:
    """Executes requests against configured LLM provider APIs via HTTP."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def execute_model(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> LLMExecutionResult:
        """Execute prompt against a provider and return response or failure state."""
        prov = provider.lower().strip()
        start_time = time.monotonic()

        try:
            if prov in ("openai", "openai-compatible"):
                return await self._call_openai(
                    model_name, prompt, timeout_seconds, start_time
                )
            elif prov == "anthropic":
                return await self._call_anthropic(
                    model_name, prompt, timeout_seconds, start_time
                )
            elif prov in ("google", "gemini"):
                return await self._call_gemini(
                    model_name, prompt, timeout_seconds, start_time
                )
            elif prov == "ollama":
                return await self._call_ollama(
                    model_name, prompt, timeout_seconds, start_time
                )
            else:
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
        except Exception as exc:
            elapsed = (time.monotonic() - start_time) * 1000.0
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
                error_message=str(exc) or "Provider API invocation failed.",
            )

    async def _call_openai(
        self,
        model_name: str,
        prompt: str,
        timeout: float,
        start_time: float,
    ) -> LLMExecutionResult:
        """Call OpenAI or OpenAI-compatible chat completion endpoint."""
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
        async with httpx.AsyncClient(timeout=timeout) as client:
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

    async def _call_anthropic(
        self,
        model_name: str,
        prompt: str,
        timeout: float,
        start_time: float,
    ) -> LLMExecutionResult:
        """Call Anthropic Messages API."""
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
        async with httpx.AsyncClient(timeout=timeout) as client:
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

    async def _call_gemini(
        self,
        model_name: str,
        prompt: str,
        timeout: float,
        start_time: float,
    ) -> LLMExecutionResult:
        """Call Google Gemini GenerativeLanguage API."""
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

        async with httpx.AsyncClient(timeout=timeout) as client:
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

    async def _call_ollama(
        self,
        model_name: str,
        prompt: str,
        timeout: float,
        start_time: float,
    ) -> LLMExecutionResult:
        """Call local Ollama endpoint."""
        base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
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
                return LLMExecutionResult(
                    provider="ollama",
                    model_name=model_name,
                    prompt=prompt,
                    response=content,
                    status="COMPLETED",
                    model_version=model_name,
                    latency_ms=round(elapsed, 2),
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
