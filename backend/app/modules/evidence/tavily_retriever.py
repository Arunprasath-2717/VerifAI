"""Tavily AI-powered web search evidence retriever.

Tavily provides structured, clean, grounded search results specifically
designed for AI/LLM evidence-retrieval use cases.  It is used as the
**primary** live-search provider when configured.

Priority chain in the orchestrator:
  1. TavilySearchRetriever  (if TAVILY_API_KEY configured)
  2. DuckDuckGoRetriever     (secondary fallback, no key required)
  3. NightcrawlerRetriever   (Wikipedia REST API, tertiary safe fallback)
  4. LocalPassageRetriever   (always available, dev/hermetic only)

Security controls:
- SSRF validation applied to every source URL returned by Tavily.
- Source domain authority scored before inclusion.
- API key never logged; sent only as a Bearer header over HTTPS.
- Calls the REST API directly with httpx (no SDK dependency) and a hard timeout.
- Request/response content length bounded.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url

logger = logging.getLogger("verifai.retriever.tavily")

# Maximum snippet length to avoid unbounded memory / log growth
_MAX_SNIPPET_LEN = 600

_TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilySearchRetriever(BaseEvidenceRetriever):
    """Evidence retriever powered by the Tavily AI search API.

    Returns structured, grounded evidence passages with source provenance.
    Applies SSRF validation and domain authority scoring to every result.

    Configure via environment variable::

        TAVILY_API_KEY=tvly-...

    When the key is absent or the API is unreachable, returns an empty list
    so the orchestrator gracefully falls back to the next retriever.
    """

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = 5,
        search_depth: str = "basic",
        timeout_seconds: float = 8.0,
    ) -> None:
        self._api_key = api_key
        self._max_results = max_results
        self._search_depth = search_depth
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "TAVILY_SEARCH"

    @classmethod
    def from_settings(cls) -> "TavilySearchRetriever":
        """Construct instance from application settings."""
        from app.core.config import get_settings

        s = get_settings()
        api_key = s.TAVILY_API_KEY.get_secret_value() if s.TAVILY_API_KEY else None
        return cls(
            api_key=api_key,
            max_results=s.TAVILY_MAX_RESULTS,
            search_depth=s.TAVILY_SEARCH_DEPTH,
            timeout_seconds=s.TAVILY_TIMEOUT_SECONDS,
        )

    @property
    def is_configured(self) -> bool:
        """Return True only when API key is present and non-empty."""
        return bool(self._api_key)

    async def retrieve(
        self, claim_text: str, max_passages: int = 5
    ) -> list[RetrievedEvidenceItem]:
        """Query Tavily for evidence passages relevant to the given claim.

        Returns an empty list (never raises) so the orchestrator can fall
        through to the next retriever in the priority chain.
        """
        if not self.is_configured:
            logger.debug("Tavily retriever not configured (TAVILY_API_KEY absent).")
            return []

        if not claim_text.strip():
            return []

        effective_max = min(max_passages, self._max_results)

        try:
            response = await self._search(claim_text, effective_max)
        except Exception as exc:
            logger.warning(
                "Tavily search request failed (%s): gracefully returning empty.",
                type(exc).__name__,
            )
            return []

        results = response.get("results", []) or []
        evidence: list[RetrievedEvidenceItem] = []

        for item in results:
            url = item.get("url", "")
            if not url or not is_safe_url(url):
                logger.debug("Tavily result skipped — SSRF/unsafe URL: %s", url)
                continue

            title = item.get("title", "") or ""
            raw_content = item.get("content", "") or ""
            snippet = raw_content[:_MAX_SNIPPET_LEN].strip()
            if not snippet:
                continue

            score: float | None = item.get("score")
            relevance = float(score) if score is not None else 0.8

            evidence.append(
                RetrievedEvidenceItem(
                    id=uuid.uuid4(),
                    source_url=url,
                    source_title=title or url,
                    publisher=_extract_publisher(url),
                    publication_date=None,
                    retrieval_timestamp=datetime.now(UTC),
                    snippet=snippet,
                    query_used=claim_text,
                    retriever_name=self.name,
                    relevance_score=round(relevance, 4),
                    authority_score=compute_domain_authority(url),
                    metadata_json={
                        "search_depth": self._search_depth,
                        "tavily_score": score,
                    },
                )
            )

        logger.info(
            "Tavily retrieved %d evidence passages for claim (length=%d).",
            len(evidence),
            len(claim_text),
        )
        return evidence

    async def _search(self, query: str, max_results: int) -> dict[str, Any]:
        """Call the Tavily REST search API with a hard request timeout."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                _TAVILY_SEARCH_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "query": query,
                    "search_depth": self._search_depth,
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, dict) else {}


def _extract_publisher(url: str) -> str | None:
    """Extract a clean domain name to use as publisher label."""
    try:
        from urllib.parse import urlparse

        host = urlparse(url).hostname or ""
        # Strip leading www.
        return host.removeprefix("www.") or None
    except Exception:
        return None
