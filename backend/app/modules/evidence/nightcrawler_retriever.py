"""Nightcrawler — Wikipedia REST API tertiary evidence retriever.

This is the safe, controlled, final fallback in the retrieval priority chain.
It uses the Wikipedia REST API (no authentication required) to find
encyclopedic reference passages for factual claim verification.

Priority chain:
  1. TavilySearchRetriever   (primary, requires TAVILY_API_KEY)
  2. DuckDuckGoRetriever     (secondary, no key required)
  3. NightcrawlerRetriever   ← this module (tertiary, Wikipedia REST)
  4. LocalPassageRetriever   (dev/hermetic baseline, always available)

Controlled by: ENABLE_NIGHTCRAWLER_FALLBACK=true (default: true)

Security controls:
- Only connects to en.wikipedia.org — a fixed, trusted, public endpoint.
- SSRF safety check still applied to all result URLs before inclusion.
- Content length bounded to _MAX_SNIPPET_LEN characters.
- Strict timeouts on all HTTP requests.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url

logger = logging.getLogger("verifai.retriever.nightcrawler")

_WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
_MAX_SNIPPET_LEN = 600
_USER_AGENT = "VerifAI-NightcrawlerRetriever/1.0 (academic; non-commercial)"

# HTML entities emitted by the Wikipedia search API
_HTML_ENTITY_MAP = {
    '<span class="searchmatch">': "",
    "</span>": "",
    "&quot;": '"',
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&#39;": "'",
}


def _clean_snippet(raw: str) -> str:
    """Strip Wikipedia search-API HTML markup from a snippet string."""
    result = raw
    for token, replacement in _HTML_ENTITY_MAP.items():
        result = result.replace(token, replacement)
    return result.strip()


class NightcrawlerRetriever(BaseEvidenceRetriever):
    """Wikipedia REST API evidence retriever (safe tertiary fallback).

    Performs keyword search against the Wikipedia search endpoint and
    returns cleaned encyclopedic passages with full source provenance.

    Designed as the final fallback before the system falls to the local
    hermetic index (LocalPassageRetriever) or returns no evidence.
    """

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "NIGHTCRAWLER_WIKIPEDIA"

    @classmethod
    def from_settings(cls) -> "NightcrawlerRetriever":
        """Construct instance from application settings."""
        from app.core.config import get_settings

        s = get_settings()
        return cls(timeout_seconds=s.NIGHTCRAWLER_TIMEOUT_SECONDS)

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        """Search Wikipedia for encyclopedic evidence relevant to the claim.

        Returns an empty list (never raises) on network failure, timeout,
        or non-200 response so the pipeline degrades gracefully.
        """
        if not claim_text.strip():
            return []

        # Build safe keyword query from alphanumeric tokens
        keywords = " ".join(
            [w for w in claim_text.split() if len(w) > 2 and w.isalnum()][:8]
        )
        if not keywords:
            return []

        params: dict[str, Any] = {
            "action": "query",
            "list": "search",
            "srsearch": keywords,
            "format": "json",
            "srlimit": max_passages,
            "utf8": "1",
        }
        headers = {"User-Agent": _USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    _WIKIPEDIA_API_URL, params=params, headers=headers
                )
                if response.status_code != 200:
                    logger.warning(
                        "Nightcrawler Wikipedia search returned HTTP %d.",
                        response.status_code,
                    )
                    return []

                data = response.json()
                search_results = data.get("query", {}).get("search", [])
        except Exception as exc:
            logger.warning(
                "Nightcrawler Wikipedia retrieval failed (%s): returning empty.",
                type(exc).__name__,
            )
            return []

        evidence: list[RetrievedEvidenceItem] = []
        for item in search_results:
            title = item.get("title", "")
            raw_snippet = item.get("snippet", "")
            snippet = _clean_snippet(raw_snippet)[:_MAX_SNIPPET_LEN]
            if not snippet:
                continue

            title_path = quote(title.replace(" ", "_"))
            page_url = f"https://en.wikipedia.org/wiki/{title_path}"

            # SSRF safety check — should always pass for Wikipedia, but enforced
            if not is_safe_url(page_url):
                logger.warning(
                    "Nightcrawler: Wikipedia URL failed SSRF check: %s", page_url
                )
                continue

            pub_date: str | None = None
            if ts := item.get("timestamp"):
                pub_date = str(ts)[:10]

            evidence.append(
                RetrievedEvidenceItem(
                    id=uuid.uuid4(),
                    source_url=page_url,
                    source_title=title,
                    publisher="Wikipedia",
                    publication_date=pub_date,
                    retrieval_timestamp=datetime.now(UTC),
                    snippet=snippet,
                    query_used=keywords,
                    retriever_name=self.name,
                    relevance_score=0.8,
                    authority_score=compute_domain_authority(page_url),
                    metadata_json={"wordcount": item.get("wordcount", 0)},
                )
            )

        logger.info(
            "Nightcrawler retrieved %d evidence passages for claim (length=%d).",
            len(evidence),
            len(claim_text),
        )
        return evidence
