"""LLM and search provider abstractions.

These thin interfaces keep the engine components independent of any specific
vendor SDK. Swapping Gemini for Groq/Claude, or DuckDuckGo for Tavily,
only requires a new class that implements the protocol.

Configuration values (API keys, model names) are read from the existing
Settings singleton — never hard-coded here.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger("verifai.engine.providers")


# ===========================================================================
# LLM provider
# ===========================================================================


class LLMProvider(Protocol):
    """Minimal interface for text-generation providers."""

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_output_tokens: int = 1024,
    ) -> str:
        """Return the model's text response for *prompt*."""
        ...


class GeminiProvider:
    """Thin async wrapper around the Google Generative AI SDK.

    Uses the model name from Settings (``LLM_MODEL``).  Falls back to
    ``gemini-1.5-flash`` — the free-tier model — when the setting is absent.

    NEVER logs or exposes ``GEMINI_API_KEY``.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        import google.generativeai as genai  # local import — only needed at runtime

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)
        self._model_name = model_name

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_output_tokens: int = 1024,
    ) -> str:
        """Send *prompt* to Gemini and return the text response.

        Raises:
            RuntimeError: On any provider-level failure, with a safe message
                          that does not expose the API key or internal path.
        """
        import asyncio
        import google.generativeai as genai

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        try:
            # Gemini SDK is synchronous; run in the default executor to avoid
            # blocking the FastAPI event loop.
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    prompt, generation_config=generation_config
                ),
            )
            return response.text
        except Exception as exc:
            logger.error("Gemini provider error (model=%s): %s", self._model_name, exc)
            raise RuntimeError("LLM provider unavailable") from exc


# ===========================================================================
# Search provider
# ===========================================================================


class SearchProvider(Protocol):
    """Minimal interface for web-search providers."""

    async def search(self, query: str, *, max_results: int = 5) -> List[Dict[str, Any]]:
        """Return up to *max_results* result dicts for *query*.

        Each dict should contain at minimum:
            ``url``, ``title``, ``body``/``snippet``.
        Missing fields should be absent rather than set to fake values.
        """
        ...


class DuckDuckGoProvider:
    """Async wrapper around duckduckgo-search (free, no API key required).

    Runs the synchronous SDK in the default thread-pool executor so it does
    not block the FastAPI event loop.
    """

    async def search(
        self, query: str, *, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search DuckDuckGo and return normalized result dicts.

        Returns an empty list on any provider failure (search failures are
        handled gracefully upstream).
        """
        import asyncio
        from ddgs import DDGS

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results)),
            )
            return results or []
        except Exception as exc:
            logger.warning("DuckDuckGo search error for query %r: %s", query[:80], exc)
            return []


# ===========================================================================
# Factory helpers — build from Settings
# ===========================================================================


def build_llm_provider() -> Optional[LLMProvider]:
    """Create the configured LLM provider from Settings.

    Returns ``None`` when no API key is configured so that the engine can
    degrade gracefully rather than crashing on startup.
    """
    from app.core.config import get_settings

    settings = get_settings()
    api_key: Optional[str] = getattr(settings, "GEMINI_API_KEY", None)
    model_name: str = getattr(settings, "LLM_MODEL", "gemini-1.5-flash")

    if not api_key or api_key.startswith("mock"):
        logger.info(
            "GEMINI_API_KEY not configured — LLM provider disabled. "
            "Verification will produce UNKNOWN verdicts without an API key."
        )
        return None

    return GeminiProvider(api_key=api_key, model_name=model_name)


def build_search_provider() -> SearchProvider:
    """Create the configured search provider.

    DuckDuckGo requires no API key, so it is always available.
    """
    return DuckDuckGoProvider()
