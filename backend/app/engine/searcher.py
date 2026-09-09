"""Web source searcher — Phase 2D.

Generates focused search queries for claims and normalizes raw search results
into the engine's internal NormalizedSource representation.

Design:
- One query per claim (claim → query → sources)
- Deduplication by canonical URL
- Graceful failure: returns empty list on provider errors
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.engine.models import ExtractedClaim, NormalizedSource
from app.engine.providers import SearchProvider

logger = logging.getLogger("verifai.engine.searcher")

# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------


def build_query(claim: ExtractedClaim) -> str:
    """Generate a focused search query from a claim.

    Rules:
    - Use the claim text directly — the claim already represents what to verify.
    - Truncate to 200 chars (search APIs have practical limits).
    - Strip excessive whitespace.
    """
    q = " ".join(claim.text.split())  # normalise whitespace
    return q[:200]


# ---------------------------------------------------------------------------
# Source normalization
# ---------------------------------------------------------------------------


def _canonical_url(raw_url: str) -> str:
    """Return a canonical form of *raw_url* for deduplication.

    Strips query strings and fragment identifiers; lowercases the host.
    """
    try:
        parsed = urlparse(raw_url)
        return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}".rstrip("/")
    except Exception:
        return raw_url.lower()


def _extract_domain(url: str) -> str:
    """Return the hostname (without 'www.') from a URL."""
    try:
        host = urlparse(url).netloc.lower()
        return host.removeprefix("www.")
    except Exception:
        return ""


def _normalize_result(raw: Dict[str, Any], rank: int, query: str) -> Optional[NormalizedSource]:
    """Convert a raw DuckDuckGo result dict into a NormalizedSource.

    Returns None for results without a usable URL.
    """
    url = raw.get("href") or raw.get("url") or ""
    if not url or not url.startswith(("http://", "https://")):
        return None

    title = str(raw.get("title") or "").strip()
    snippet = str(raw.get("body") or raw.get("snippet") or "").strip()
    pub_date = raw.get("published") or raw.get("date") or None

    return NormalizedSource(
        url=url,
        title=title,
        snippet=snippet,
        domain=_extract_domain(url),
        rank=rank,
        query=query,
        publication_date=str(pub_date) if pub_date else None,
    )


def normalize_results(
    raw_results: List[Dict[str, Any]],
    query: str,
) -> List[NormalizedSource]:
    """Normalize and deduplicate raw search results.

    - Skips results with no usable URL.
    - Deduplicates by canonical URL (keeps first occurrence by rank).
    """
    seen: set[str] = set()
    sources: List[NormalizedSource] = []

    for i, raw in enumerate(raw_results, start=1):
        source = _normalize_result(raw, rank=i, query=query)
        if source is None:
            continue
        canon = _canonical_url(source.url)
        if canon in seen:
            continue
        seen.add(canon)
        sources.append(source)

    return sources


# ---------------------------------------------------------------------------
# Searcher
# ---------------------------------------------------------------------------


class SourceSearcher:
    """Searches for web sources for a given claim.

    Failure policy: returns an empty list rather than raising.
    The caller (engine orchestrator) tracks the failure count.
    """

    def __init__(
        self,
        provider: SearchProvider,
        max_results_per_query: int = 5,
    ) -> None:
        self._provider = provider
        self._max_results = max_results_per_query

    async def search_for_claim(
        self, claim: ExtractedClaim
    ) -> List[NormalizedSource]:
        """Generate a query for *claim* and return normalized sources.

        Returns an empty list on provider failures.
        """
        query = build_query(claim)
        logger.info(
            "Searching for claim %s: %r", claim.claim_id, query[:80]
        )

        raw_results = await self._provider.search(
            query, max_results=self._max_results
        )

        sources = normalize_results(raw_results, query)
        logger.info(
            "Found %d source(s) for claim %s", len(sources), claim.claim_id
        )
        return sources
