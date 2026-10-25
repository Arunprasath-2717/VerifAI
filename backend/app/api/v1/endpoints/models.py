"""Dynamic Model Discovery and Catalog Endpoints.

Provides live discovery of LLM providers, model families, context windows,
capabilities, and connection statuses to power a data-driven model selector.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

logger = logging.getLogger("verifai.api.models")
router = APIRouter(prefix="/models", tags=["Model Ecosystem & Discovery"])


class ModelItem(BaseModel):
    """Metadata specification for a single model in the VerifAI ecosystem."""

    id: str = Field(description="Unique model identifier passed to inference APIs")
    name: str = Field(description="Human-readable model display name")
    family: str = Field(
        description="Model family, e.g. GPT, Claude, Gemini, Llama, Qwen, DeepSeek"
    )
    model_type: Literal["proprietary", "open-weight", "local"] = Field(
        description="Licensing & deployment type"
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Supported capabilities: text, vision, reasoning, coding, rerank",
    )
    context_window: int = Field(description="Maximum context window tokens")
    max_output_tokens: int = Field(
        default=4096, description="Maximum completion tokens"
    )
    recommended: bool = Field(
        default=False, description="Whether recommended in default benchmark set"
    )
    description: str | None = None


class ProviderCatalog(BaseModel):
    """Catalog of models provided by an individual inference provider or gateway."""

    provider: str = Field(
        description="Canonical provider key: openai, anthropic, google, etc."
    )
    name: str = Field(description="Provider display name")
    category: Literal["cloud", "local", "router"] = Field(
        description="Provider architecture tier"
    )
    status: Literal["connected", "not_configured", "available"] = Field(
        description="Live credential and availability state"
    )
    docs_url: str = Field(description="Provider documentation URL")
    models: list[ModelItem] = Field(default_factory=list)


class ModelCatalogResponse(BaseModel):
    """Consolidated model ecosystem response for dynamic frontend selectors."""

    total_providers: int
    total_models: int
    recommended_defaults: list[str]
    providers: list[ProviderCatalog]


@router.get(
    "",
    response_model=ModelCatalogResponse,
    summary="Get Dynamic Model Catalog",
    description=(
        "Returns the complete ecosystem of proprietary, open-weight, and local models "
        "dynamically annotated with live provider credential connectivity, "
        "capabilities, "
        "and token context windows."
    ),
)
async def get_model_catalog(
    settings: Settings = Depends(get_settings),
) -> ModelCatalogResponse:
    """Dynamically resolve model catalog with live provider connectivity statuses."""

    # 1. OpenAI (Proprietary + Open-Weight)
    openai_connected = bool(settings.OPENAI_API_KEY)
    openai_models = [
        ModelItem(
            id="gpt-5.6-sol",
            name="GPT-5.6 Sol",
            family="GPT",
            model_type="proprietary",
            capabilities=["text", "vision", "reasoning"],
            context_window=1050000,
            max_output_tokens=16384,
            recommended=True,
            description=(
                "Frontier high-intelligence reasoning flagship for deep claim "
                "deconstruction."
            ),
        ),
        ModelItem(
            id="gpt-5.6-terra",
            name="GPT-5.6 Terra",
            family="GPT",
            model_type="proprietary",
            capabilities=["text", "vision", "reasoning"],
            context_window=500000,
            max_output_tokens=8192,
            recommended=False,
            description=(
                "Balanced frontier model optimized for high-throughput enterprise "
                "verification."
            ),
        ),
        ModelItem(
            id="gpt-5.6-luna",
            name="GPT-5.6 Luna",
            family="GPT",
            model_type="proprietary",
            capabilities=["text", "reasoning"],
            context_window=200000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Fast, low-latency reasoning variant for instant verification triage."
            ),
        ),
        ModelItem(
            id="gpt-4o",
            name="GPT-4o",
            family="GPT",
            model_type="proprietary",
            capabilities=["text", "vision"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=True,
            description="Omni multimodal benchmark baseline for claim extraction.",
        ),
        ModelItem(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            family="GPT",
            model_type="proprietary",
            capabilities=["text", "vision"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=False,
            description="Cost-efficient verification worker model.",
        ),
        ModelItem(
            id="gpt-oss-120b",
            name="GPT-OSS 120B",
            family="GPT",
            model_type="open-weight",
            capabilities=["text", "coding"],
            context_window=131072,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "OpenAI open-weight foundation model for transparent self-hosted "
                "benchmarking."
            ),
        ),
    ]

    # 2. Anthropic (Proprietary)
    anthropic_connected = bool(settings.ANTHROPIC_API_KEY)
    anthropic_models = [
        ModelItem(
            id="claude-3-5-sonnet",
            name="Claude 3.5 Sonnet",
            family="Claude",
            model_type="proprietary",
            capabilities=["text", "vision", "coding", "reasoning"],
            context_window=200000,
            max_output_tokens=8192,
            recommended=True,
            description=(
                "Frontier reasoning and factual nuance leader with high claim "
                "corroboration precision."
            ),
        ),
        ModelItem(
            id="claude-3-opus",
            name="Claude 3 Opus",
            family="Claude",
            model_type="proprietary",
            capabilities=["text", "vision", "reasoning"],
            context_window=200000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Deep synthetic analysis model for highly technical cross-examination."
            ),
        ),
        ModelItem(
            id="claude-3-5-haiku",
            name="Claude 3.5 Haiku",
            family="Claude",
            model_type="proprietary",
            capabilities=["text", "coding"],
            context_window=200000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Ultra-fast proposition verification and initial snippet filtering."
            ),
        ),
    ]

    # 3. Google Gemini (Proprietary + Multimodal)
    gemini_connected = bool(settings.GEMINI_API_KEY)
    gemini_models = [
        ModelItem(
            id="gemini-3.8-flash",
            name="Gemini 3.8 Flash",
            family="Gemini",
            model_type="proprietary",
            capabilities=["text", "vision", "multimodal"],
            context_window=1000000,
            max_output_tokens=8192,
            recommended=True,
            description=(
                "1M+ token context window leader for full-document corpus grounding."
            ),
        ),
        ModelItem(
            id="gemini-3.1-pro",
            name="Gemini 3.1 Pro",
            family="Gemini",
            model_type="proprietary",
            capabilities=["text", "vision", "reasoning"],
            context_window=2000000,
            max_output_tokens=8192,
            recommended=True,
            description=(
                "Deep multi-step reasoning flagship with 2M token context capability."
            ),
        ),
        ModelItem(
            id="gemini-2.5-pro",
            name="Gemini 2.5 Pro",
            family="Gemini",
            model_type="proprietary",
            capabilities=["text", "multimodal"],
            context_window=1000000,
            max_output_tokens=4096,
            recommended=False,
            description="Previous-generation enterprise grounding model.",
        ),
        ModelItem(
            id="gemini-2.5-flash-lite",
            name="Gemini 2.5 Flash-Lite",
            family="Gemini",
            model_type="proprietary",
            capabilities=["text"],
            context_window=500000,
            max_output_tokens=4096,
            recommended=False,
            description="Lightweight rapid claim deconstruction variant.",
        ),
    ]

    # 4. Groq (Ultra-Fast Inference Gateway)
    groq_connected = bool(settings.GROQ_API_KEY)
    groq_models = [
        ModelItem(
            id="llama-3.3-70b-versatile",
            name="Llama 3.3 70B (Groq LPU)",
            family="Llama",
            model_type="open-weight",
            capabilities=["text", "reasoning"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=True,
            description=(
                "Sub-second verification responses powered by Groq LPU silicon."
            ),
        ),
        ModelItem(
            id="mixtral-8x7b-32768",
            name="Mixtral 8x7B MoE",
            family="Mistral",
            model_type="open-weight",
            capabilities=["text"],
            context_window=32768,
            max_output_tokens=4096,
            recommended=False,
            description="High-speed Mixture-of-Experts inference.",
        ),
    ]

    # 5. OpenRouter / OmniRoute (Unified Gateway for DeepSeek, Mistral, Qwen, Cohere)
    router_connected = bool(settings.OPENROUTER_API_KEY or settings.OMNIROUTE_API_KEY)
    router_models = [
        ModelItem(
            id="deepseek/deepseek-r1",
            name="DeepSeek R1 (Reasoning)",
            family="DeepSeek",
            model_type="open-weight",
            capabilities=["text", "reasoning"],
            context_window=64000,
            max_output_tokens=8192,
            recommended=True,
            description=(
                "Reinforcement-learning reasoning model for deep contradiction "
                "proofing."
            ),
        ),
        ModelItem(
            id="deepseek/deepseek-chat",
            name="DeepSeek V3",
            family="DeepSeek",
            model_type="open-weight",
            capabilities=["text", "coding"],
            context_window=64000,
            max_output_tokens=8192,
            recommended=False,
            description=(
                "671B MoE architecture with exceptional factual retrieval fidelity."
            ),
        ),
        ModelItem(
            id="mistralai/mistral-large-2411",
            name="Mistral Large 3",
            family="Mistral",
            model_type="open-weight",
            capabilities=["text", "reasoning"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=True,
            description=(
                "European sovereign open-weight flagship with multi-lingual reasoning."
            ),
        ),
        ModelItem(
            id="qwen/qwen-2.5-72b-instruct",
            name="Qwen 2.5 72B",
            family="Qwen",
            model_type="open-weight",
            capabilities=["text", "coding", "reasoning"],
            context_window=131072,
            max_output_tokens=4096,
            recommended=True,
            description=(
                "Top-tier open-weight reasoning model matching frontier proprietary"
                " baselines."
            ),
        ),
        ModelItem(
            id="qwen/qwen-2.5-coder-32b-instruct",
            name="Qwen 2.5 Coder 32B",
            family="Qwen",
            model_type="open-weight",
            capabilities=["text", "coding"],
            context_window=131072,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Domain specialist for verifying code correctness and technical "
                "syntaxes."
            ),
        ),
        ModelItem(
            id="cohere/command-r-plus",
            name="Cohere Command R+",
            family="Cohere",
            model_type="proprietary",
            capabilities=["text", "reasoning", "rerank"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Specialized RAG and enterprise evidence retrieval foundation model."
            ),
        ),
        ModelItem(
            id="x-ai/grok-2-1212",
            name="xAI Grok 2",
            family="Grok",
            model_type="proprietary",
            capabilities=["text", "vision"],
            context_window=131072,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Independent proprietary baseline for non-consensus verification tests."
            ),
        ),
    ]

    # 6. Ollama / Local Self-Hosted (Air-gapped & Private KB)
    ollama_models = [
        ModelItem(
            id="gemma4:12b",
            name="Google Gemma 4 12B",
            family="Gemma",
            model_type="local",
            capabilities=["text", "multimodal"],
            context_window=262144,
            max_output_tokens=4096,
            recommended=True,
            description=(
                "Latest open-weight Gemma architecture running privately with 256K "
                "context."
            ),
        ),
        ModelItem(
            id="phi4:14b",
            name="Microsoft Phi-4 14B",
            family="Phi",
            model_type="local",
            capabilities=["text", "reasoning"],
            context_window=16384,
            max_output_tokens=4096,
            recommended=True,
            description=(
                "Synthetic high-quality reasoning model suited for local air-gapped"
                " deployments."
            ),
        ),
        ModelItem(
            id="llama3.3:8b",
            name="Llama 3.3 8B (Local)",
            family="Llama",
            model_type="local",
            capabilities=["text"],
            context_window=128000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Lightweight local model for privacy-first proposition extraction."
            ),
        ),
        ModelItem(
            id="deepseek-r1:14b",
            name="DeepSeek R1 Distill 14B",
            family="DeepSeek",
            model_type="local",
            capabilities=["text", "reasoning"],
            context_window=64000,
            max_output_tokens=4096,
            recommended=False,
            description=(
                "Locally hosted distilled reasoning model for offline verification "
                "checks."
            ),
        ),
    ]

    providers = [
        ProviderCatalog(
            provider="openai",
            name="OpenAI",
            category="cloud",
            status="connected" if openai_connected else "not_configured",
            docs_url="https://platform.openai.com/docs/models",
            models=openai_models,
        ),
        ProviderCatalog(
            provider="anthropic",
            name="Anthropic",
            category="cloud",
            status="connected" if anthropic_connected else "not_configured",
            docs_url="https://docs.anthropic.com/en/docs/about-claude/models",
            models=anthropic_models,
        ),
        ProviderCatalog(
            provider="google",
            name="Google Gemini",
            category="cloud",
            status="connected" if gemini_connected else "not_configured",
            docs_url="https://ai.google.dev/gemini-api/docs/models",
            models=gemini_models,
        ),
        ProviderCatalog(
            provider="groq",
            name="Groq LPU",
            category="cloud",
            status="connected" if groq_connected else "not_configured",
            docs_url="https://console.groq.com/docs/models",
            models=groq_models,
        ),
        ProviderCatalog(
            provider="openrouter",
            name="OpenRouter Gateway",
            category="router",
            status="connected" if router_connected else "not_configured",
            docs_url="https://openrouter.ai/docs#models",
            models=router_models,
        ),
        ProviderCatalog(
            provider="ollama",
            name="Ollama (Local / On-Prem)",
            category="local",
            status="connected" if bool(settings.OLLAMA_BASE_URL) else "available",
            docs_url="https://ollama.com/library",
            models=ollama_models,
        ),
    ]

    all_models = [m for p in providers for m in p.models]
    recommended_defaults = [m.id for m in all_models if m.recommended]

    return ModelCatalogResponse(
        total_providers=len(providers),
        total_models=len(all_models),
        recommended_defaults=recommended_defaults,
        providers=providers,
    )


class LeaderboardCategories(BaseModel):
    factualSupport: float
    evidenceSupport: float
    contradictionDetection: float
    unknownHandling: float
    claimVerification: float


class ModelLeaderboardResponseItem(BaseModel):
    rank: int
    model: str
    provider: str
    version: str
    overallScore: float
    categories: LeaderboardCategories
    evaluationsCount: int
    lastEvaluated: str
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


@router.get(
    "/leaderboard",
    response_model=list[ModelLeaderboardResponseItem],
    summary="Get Empirical Model Benchmark Leaderboard",
    description=(
        "Returns empirical benchmarks, hallucination resistance rates, and category"
        " rankings across frontier models."
    ),
)
async def get_model_leaderboard() -> list[ModelLeaderboardResponseItem]:
    """Return no rankings until a persisted benchmark evaluation pipeline exists.

    Catalog metadata and provider availability are not measurements of accuracy.
    Publishing fabricated scores would misrepresent VerifAI evaluation results.
    """
    return []


class PublicSuiteScores(BaseModel):
    """Source-reported LiveBench 2.0 scores, never inferred from VerifAI runs."""

    agentic: float | None
    design: float | None
    coding: float | None
    browser: float | None
    data_analysis: float | None
    research: float | None
    reasoning: float | None


class PublicLeaderboardModel(BaseModel):
    id: str
    rank: int
    name: str
    organization: str
    overall_score: float = Field(ge=0, le=100)
    suite_scores: PublicSuiteScores
    suite_coverage: int = Field(ge=1, le=7)


class PublicLeaderboardSnapshot(BaseModel):
    schema_version: int = 1
    benchmark: str
    benchmark_release: str
    source_updated_at: str
    retrieved_at: str
    source_url: str
    data_url: str
    methodology_url: str
    refresh_policy: str
    score_description: str
    total_models: int
    models: list[PublicLeaderboardModel]


@router.get(
    "/public-benchmarks",
    response_model=PublicLeaderboardSnapshot,
    summary="Sourced, weekly refreshed LiveBench 2.0 model scores",
    description=(
        "A separately attributed public benchmark snapshot; unlike the empirical "
        "VerifAI leaderboard, it does not assert hallucination/citation accuracy."
    ),
)
async def get_public_benchmarks() -> PublicLeaderboardSnapshot:
    from fastapi import HTTPException

    from app.modules.benchmarks.public_leaderboard import (
        PublicBenchmarkRefreshError,
        load_public_snapshot,
    )

    try:
        return PublicLeaderboardSnapshot.model_validate(load_public_snapshot())
    except (PublicBenchmarkRefreshError, ValueError) as exc:
        logger.warning("Public benchmark snapshot unavailable: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail=(
                "Public benchmark snapshot is unavailable; retry after the weekly "
                "refresh."
            ),
        ) from exc
