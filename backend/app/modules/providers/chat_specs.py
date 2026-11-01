"""Supported BYOK chat providers, capability metadata and fixed HTTPS endpoints.

Fixed providers do not accept user-repointed base URLs: bearer credentials must
only go to known official API hosts. Unlisted OpenAI-compatible services use
the separate public-HTTPS custom-provider path.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatProviderSpec:
    provider_id: str
    name: str
    base_url: str
    protocol: str = "openai"  # "openai", "anthropic", "gemini"
    docs_url: str = ""


SPECS: dict[str, ChatProviderSpec] = {
    spec.provider_id: spec
    for spec in [
        ChatProviderSpec(
            "prov-openai",
            "OpenAI",
            "https://api.openai.com/v1",
            docs_url="https://platform.openai.com/api-keys",
        ),
        ChatProviderSpec(
            "prov-anthropic",
            "Anthropic Claude",
            "https://api.anthropic.com/v1",
            "anthropic",
            "https://console.anthropic.com/settings/keys",
        ),
        ChatProviderSpec(
            "prov-google",
            "Google Gemini",
            "https://generativelanguage.googleapis.com/v1beta",
            "gemini",
            "https://aistudio.google.com/apikey",
        ),
        ChatProviderSpec(
            "prov-groq",
            "Groq",
            "https://api.groq.com/openai/v1",
            docs_url="https://console.groq.com/keys",
        ),
        ChatProviderSpec(
            "prov-openrouter",
            "OpenRouter",
            "https://openrouter.ai/api/v1",
            docs_url="https://openrouter.ai/keys",
        ),
        ChatProviderSpec(
            "prov-nvidia",
            "NVIDIA NIM",
            "https://integrate.api.nvidia.com/v1",
            docs_url="https://build.nvidia.com/",
        ),
        ChatProviderSpec(
            "prov-mistral",
            "Mistral AI",
            "https://api.mistral.ai/v1",
            docs_url="https://console.mistral.ai/api-keys",
        ),
        ChatProviderSpec(
            "prov-deepseek",
            "DeepSeek",
            "https://api.deepseek.com",
            docs_url="https://platform.deepseek.com/",
        ),
        ChatProviderSpec(
            "prov-perplexity",
            "Perplexity",
            "https://api.perplexity.ai",
            docs_url="https://docs.perplexity.ai/",
        ),
        ChatProviderSpec(
            "prov-xai",
            "xAI Grok",
            "https://api.x.ai/v1",
            docs_url="https://console.x.ai/",
        ),
        ChatProviderSpec(
            "prov-together",
            "Together AI",
            "https://api.together.xyz/v1",
            docs_url="https://api.together.ai/",
        ),
        ChatProviderSpec(
            "prov-fireworks",
            "Fireworks AI",
            "https://api.fireworks.ai/inference/v1",
            docs_url="https://fireworks.ai/",
        ),
        ChatProviderSpec(
            "prov-cerebras",
            "Cerebras",
            "https://api.cerebras.ai/v1",
            docs_url="https://cloud.cerebras.ai/",
        ),
        ChatProviderSpec(
            "prov-deepinfra",
            "DeepInfra",
            "https://api.deepinfra.com/v1/openai",
            docs_url="https://deepinfra.com/",
        ),
        ChatProviderSpec(
            "prov-sambanova",
            "SambaNova",
            "https://api.sambanova.ai/v1",
            docs_url="https://cloud.sambanova.ai/",
        ),
        ChatProviderSpec(
            "prov-moonshot",
            "Moonshot AI",
            "https://api.moonshot.ai/v1",
            docs_url="https://platform.moonshot.ai/",
        ),
    ]
}


def credential_provider_id(selection_provider: str) -> str:
    return (
        selection_provider
        if selection_provider.startswith("prov-custom-")
        else "prov-" + selection_provider.lower()
    )


def is_supported_provider(provider_id: str) -> bool:
    return provider_id in SPECS or (
        provider_id.startswith("prov-custom-") and len(provider_id) <= 64
    )


def provider_protocol(provider_id: str) -> str:
    return SPECS[provider_id].protocol if provider_id in SPECS else "openai"
