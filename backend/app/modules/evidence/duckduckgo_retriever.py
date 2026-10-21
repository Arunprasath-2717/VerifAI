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

import asyncio
import importlib
import logging
import uuid
import warnings
from datetime import UTC, datetime
from typing import cast
from urllib.parse import urlparse

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url

logger = logging.getLogger("verifai.retriever.duckduckgo")

_MAX_SNIPPET_LEN = 600

_missing_package_logged = False


def load_ddgs_class() -> type | None:
    """Import the DDGS client from ``ddgs`` (current) or ``duckduckgo_search``.

    Returns None when neither package is installed, logging that once per
    process rather than on every claim.
    """
    global _missing_package_logged
    for module_name in ("ddgs", "duckduckgo_search"):
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                module = importlib.import_module(module_name)
            return cast(type, module.DDGS)
        except (ImportError, AttributeError):
            continue
    if not _missing_package_logged:
        logger.warning(
            "DuckDuckGo fallback enabled but the 'ddgs' package is not installed; "
            "tier skipped. Install with: pip install -r requirements-live.txt"
        )
        _missing_package_logged = True
    return None


class DuckDuckGoRetriever(BaseEvidenceRetriever):
    """Evidence retriever backed by DuckDuckGo web search.

    Uses the optional ``ddgs`` library (no API key required); see
    ``requirements-live.txt``.
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

        ddgs_class = load_ddgs_class()
        if ddgs_class is None:
            return []

        effective_max = min(max_passages, self._max_results)

        def _run_search() -> list[dict]:
            with ddgs_class(timeout=max(int(self._timeout), 1)) as ddgs:
                return list(ddgs.text(claim_text, max_results=effective_max))

        try:
            # The library is synchronous; run it off the event loop and bound the
            # wait so a stalled search cannot hold the request open.
            results = await asyncio.wait_for(
                asyncio.to_thread(_run_search), timeout=self._timeout + 1.0
            )
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
