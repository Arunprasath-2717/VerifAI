"""DuckDuckGo web search evidence retriever (secondary fallback).

DuckDuckGo requires no API key and provides real-time web search results.
It is used as the **secondary** live-search fallback when Tavily is
unconfigured or returns no results.

Controlled by: ENABLE_DUCKDUCKGO_FALLBACK=true (default: true)

Security controls:
- SSRF validation applied to every result URL.
- Domain authority scored before inclusion.
- Content length bounded to _MAX_SNIPPET_LEN characters.
- Connection and read timeouts enforced.
"""

import logging
import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url

logger = logging.getLogger("verifai.retriever.duckduckgo")

_MAX_SNIPPET_LEN = 600


class DuckDuckGoRetriever(BaseEvidenceRetriever):
    """Evidence retriever backed by DuckDuckGo web search.

    Uses the ``duckduckgo-search`` library (no API key required).
    Returns structured evidence passages with provenance metadata.

    When the library is absent or the search fails, returns an empty list
    so the orchestrator falls through to the Nightcrawler fallback.
    """

    def __init__(
        self,
        max_results: int = 5,
        timeout_seconds: float = 6.0,
    ) -> None:
        self._max_results = max_results
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "DUCKDUCKGO_SEARCH"

    @classmethod
    def from_settings(cls) -> "DuckDuckGoRetriever":
        """Construct instance from application settings."""
        from app.core.config import get_settings

        s = get_settings()
        return cls(
            max_results=s.DUCKDUCKGO_MAX_RESULTS,
            timeout_seconds=s.DUCKDUCKGO_TIMEOUT_SECONDS,
        )

    async def retrieve(
        self, claim_text: str, max_passages: int = 5
    ) -> list[RetrievedEvidenceItem]:
        """Search DuckDuckGo for evidence relevant to the given claim.

        Returns an empty list (never raises) on any error or library absence.
        """
        if not claim_text.strip():
            return []

        try:
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                from duckduckgo_search import DDGS  # type: ignore[import-untyped]
        except ImportError:
            logger.warning(
                "duckduckgo-search package not installed; skipping DDG retrieval. "
                "Install with: pip install duckduckgo-search"
            )
            return []

        effective_max = min(max_passages, self._max_results)

        try:
            import asyncio

            def _run_search() -> list[dict]:
                with DDGS(timeout=max(int(self._timeout), 5)) as ddgs:
                    return list(
                        ddgs.text(
                            claim_text,
                            max_results=effective_max,
                        )
                    )

            results = await asyncio.get_event_loop().run_in_executor(None, _run_search)
        except Exception as exc:
            logger.warning(
                "DuckDuckGo search failed (%s): gracefully returning empty.",
                type(exc).__name__,
            )
            return []

        evidence: list[RetrievedEvidenceItem] = []

        for item in results:
            url = item.get("href", "") or item.get("url", "")
            if not url or not is_safe_url(url):
                logger.debug("DDG result skipped — SSRF/unsafe URL: %s", url)
                continue

            title = item.get("title", "") or ""
            body = item.get("body", "") or ""
            snippet = body[:_MAX_SNIPPET_LEN].strip()
            if not snippet:
                continue

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
                    # Fixed score — DDG provides no relevance signal
                    relevance_score=0.75,
                    authority_score=compute_domain_authority(url),
                    metadata_json={"source": "duckduckgo"},
                )
            )

        logger.info(
            "DuckDuckGo retrieved %d evidence passages for claim (length=%d).",
            len(evidence),
            len(claim_text),
        )
        return evidence


def _extract_publisher(url: str) -> str | None:
    """Extract a clean domain name as publisher label."""
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.") or None
    except Exception:
        return None
