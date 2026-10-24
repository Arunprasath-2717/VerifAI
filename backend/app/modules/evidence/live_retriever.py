"""Cascading live web evidence retriever — priority fallback chain.

Implements a 3-tier live-search strategy:

  Tier 1: Tavily AI Search   (configured via TAVILY_API_KEY)
  Tier 2: DuckDuckGo Search  (no API key; ENABLE_DUCKDUCKGO_FALLBACK=true)
  Tier 3: Nightcrawler       (Wikipedia REST; ENABLE_NIGHTCRAWLER_FALLBACK=true)

Each tier is tried in order; the first that returns ≥ 1 evidence passage is
used.  If all tiers fail or return nothing, an empty list is returned and
the orchestrator records UNKNOWN/SEARCH_UNKNOWN for the claim.

This replaces the old SafeWebRetriever with a more resilient, layered
approach while preserving the same public interface expected by the
orchestrator and all existing tests.

Security:
- Every retriever in the chain independently validates URLs via is_safe_url().
- The chain itself does not perform any network requests; only the active
  retriever tier does.
- API keys are read from settings at construction time and never logged.
"""

import logging

from app.modules.evidence.duckduckgo_retriever import DuckDuckGoRetriever
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.nightcrawler_retriever import NightcrawlerRetriever
from app.modules.evidence.tavily_retriever import TavilySearchRetriever

logger = logging.getLogger("verifai.retriever.live")


class LiveWebRetriever(BaseEvidenceRetriever):
    """Cascading live web evidence retriever with 3-tier fallback chain.

    Tier priority (first with results wins):
      1. TavilySearchRetriever   — AI-optimised, highest quality
      2. DuckDuckGoRetriever     — real-time, no API key
      3. NightcrawlerRetriever   — Wikipedia REST, always safe

    Usage::

        retriever = LiveWebRetriever.from_settings()
        evidence = await retriever.retrieve("Water has the formula H2O.")
    """

    def __init__(
        self,
        tavily: TavilySearchRetriever | None = None,
        duckduckgo: DuckDuckGoRetriever | None = None,
        nightcrawler: NightcrawlerRetriever | None = None,
    ) -> None:
        self._tavily = tavily
        self._duckduckgo = duckduckgo
        self._nightcrawler = nightcrawler

    @property
    def name(self) -> str:
        return "LIVE_WEB_RETRIEVER"

    @classmethod
    def from_settings(cls) -> "LiveWebRetriever":
        """Construct instance with all tiers from application settings."""
        from app.core.config import get_settings

        s = get_settings()

        # Tier 1: Tavily (only if key configured)
        tavily = TavilySearchRetriever.from_settings() if s.TAVILY_API_KEY else None

        # Tier 2: DuckDuckGo (only if enabled in settings)
        duckduckgo = (
            DuckDuckGoRetriever.from_settings()
            if s.ENABLE_DUCKDUCKGO_FALLBACK
            else None
        )

        # Tier 3: Nightcrawler / Wikipedia (only if enabled in settings)
        nightcrawler = (
            NightcrawlerRetriever.from_settings()
            if s.ENABLE_NIGHTCRAWLER_FALLBACK
            else None
        )

        return cls(tavily=tavily, duckduckgo=duckduckgo, nightcrawler=nightcrawler)

    async def retrieve(
        self, claim_text: str, max_passages: int = 5
    ) -> list[RetrievedEvidenceItem]:
        """Attempt evidence retrieval through the configured tier chain.

        Returns the first non-empty result set.  Falls back to an empty list
        if every configured tier fails or returns no usable evidence.
        """
        if not claim_text.strip():
            return []

        # --- Tier 1: Tavily ---
        if self._tavily is not None and self._tavily.is_configured:
            try:
                results = await self._tavily.retrieve(claim_text, max_passages)
                if results:
                    logger.info(
                        "Live retrieval: Tavily returned %d passages (tier 1).",
                        len(results),
                    )
                    return results
                logger.debug("Tavily returned 0 passages; falling through to tier 2.")
            except Exception as exc:
                logger.warning("Tavily tier raised unexpectedly: %s", exc)

        # --- Tier 2: DuckDuckGo ---
        if self._duckduckgo is not None:
            try:
                results = await self._duckduckgo.retrieve(claim_text, max_passages)
                if results:
                    logger.info(
                        "Live retrieval: DuckDuckGo returned %d passages (tier 2).",
                        len(results),
                    )
                    return results
                logger.debug(
                    "DuckDuckGo returned 0 passages; falling through to tier 3."
                )
            except Exception as exc:
                logger.warning("DuckDuckGo tier raised unexpectedly: %s", exc)

        # --- Tier 3: Nightcrawler (Wikipedia REST) ---
        if self._nightcrawler is not None:
            try:
                results = await self._nightcrawler.retrieve(claim_text, max_passages)
                if results:
                    logger.info(
                        "Live retrieval: Nightcrawler returned %d passages (tier 3).",
                        len(results),
                    )
                    return results
                logger.debug("Nightcrawler returned 0 passages; all tiers exhausted.")
            except Exception as exc:
                logger.warning("Nightcrawler tier raised unexpectedly: %s", exc)

        logger.info(
            "Live retrieval: all configured tiers exhausted for claim (length=%d).",
            len(claim_text),
        )
        return []
