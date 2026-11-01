"""Registry for pluggable LLM provider strategy adapters."""

import logging
from typing import ClassVar

from app.core.config import Settings, get_settings
from app.modules.llm.providers.anthropic import AnthropicProvider
from app.modules.llm.providers.gemini import GeminiProvider
from app.modules.llm.providers.groq import GroqProvider
from app.modules.llm.providers.interface import BaseLLMProvider
from app.modules.llm.providers.ollama import OllamaProvider
from app.modules.llm.providers.omniroute import OmniRouteProvider
from app.modules.llm.providers.openai import OpenAIProvider
from app.modules.llm.providers.openrouter import OpenRouterProvider

logger = logging.getLogger("verifai.llm.registry")


class LLMProviderRegistry:
    """Strategy registry providing extensible lookup for LLM provider adapters."""

    _ALIASES: ClassVar[dict[str, str]] = {
        "openai-compatible": "openai",
        "cheaperinference": "omniroute",
        "gemini": "google",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._providers: dict[str, BaseLLMProvider] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the built-in provider adapters."""
        defaults: list[BaseLLMProvider] = [
            OpenAIProvider(self.settings),
            OpenRouterProvider(self.settings),
            GroqProvider(self.settings),
            OmniRouteProvider(self.settings),
            AnthropicProvider(self.settings),
            GeminiProvider(self.settings),
            OllamaProvider(self.settings),
        ]
        for p in defaults:
            self.register(p.name, p)

    def register(self, name: str, provider: BaseLLMProvider) -> None:
        """Register or override a provider strategy."""
        normalized = name.lower().strip()
        self._providers[normalized] = provider
        logger.debug("Registered LLM provider adapter: %s", normalized)

    def get(self, provider_name: str) -> BaseLLMProvider | None:
        """Retrieve the provider strategy for a given name or alias."""
        normalized = provider_name.lower().strip()
        canonical = self._ALIASES.get(normalized, normalized)
        return self._providers.get(canonical)

    def supported_providers(self) -> list[str]:
        """Return list of supported provider names."""
        return sorted(list(self._providers.keys()) + list(self._ALIASES.keys()))
