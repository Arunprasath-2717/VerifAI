"""Web source searcher — Phase 2E Hardening.

Generates focused search queries for claims and normalizes raw search results
into the engine's internal NormalizedSource representation.

Hardening:
- URL canonicalization strips tracking parameters (utm_*, ref, gclid, etc.) and amp/m. prefixes.
- Pre-extracts root domain, wire attribution, and article fingerprint for downstream independence clustering.
- Graceful failure: returns empty list on provider errors, cleanly isolated.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.engine.authority import extract_root_domain
from app.engine.independence import compute_article_fingerprint, detect_wire_attribution
from app.engine.models import ExtractedClaim, NormalizedSource
from app.engine.providers import SearchProvider

logger = logging.getLogger("verifai.engine.searcher")

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "ref_src", "fbclid", "gclid", "msclkid", "mc_eid", "yclid",
}


# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------


def build_query(claim: ExtractedClaim) -> str:
    """Generate a focused search query from a claim.

    Rules:
    - Normalise whitespace.
    - Truncate to 200 chars.
    """
    q = " ".join(claim.text.split())
    return q[:200]


# ---------------------------------------------------------------------------
# Source normalization & canonicalization
# ---------------------------------------------------------------------------


def _canonical_url(raw_url: str) -> str:
    """Return a canonical form of *raw_url* for deduplication.

    - Lowercases host.
    - Strips 'm.' and 'amp.' mobile prefixes.
    - Strips query tracking parameters (utm_*, fbclid, ref, etc.).
    - Strips fragment identifiers and trailing slashes.
    """
    try:
        parsed = urlparse(raw_url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host.startswith("amp."):
            host = host[4:]
        if host.startswith("m.") and not host.startswith("medium."):
            host = host[2:]

        # Filter out tracking query params
        if parsed.query:
            filtered_q = [
                (k, v) for k, v in parse_qsl(parsed.query)
                if k.lower() not in _TRACKING_PARAMS and not k.lower().startswith("utm_")
            ]
            clean_query = urlencode(filtered_q)
        else:
            clean_query = ""

        clean_path = parsed.path.rstrip("/")
        if not clean_path and not parsed.path:
            clean_path = ""

        canonical = urlunparse((
            parsed.scheme.lower() or "https",
            host,
            clean_path,
            "",
            clean_query,
            "",  # strip fragment
        ))
        return canonical.rstrip("/")
    except Exception:
        return raw_url.lower().rstrip("/")


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

    domain = _extract_domain(url)
    root = extract_root_domain(domain)
    wire = detect_wire_attribution(title, snippet)
    fingerprint = compute_article_fingerprint(f"{title} {snippet}")

    return NormalizedSource(
        url=url,
        title=title,
        snippet=snippet,
        domain=domain,
        rank=rank,
        query=query,
        publication_date=str(pub_date) if pub_date else None,
        root_domain=root,
        wire_attribution=wire,
        article_fingerprint=fingerprint,
    )


def normalize_results(
    raw_results: List[Dict[str, Any]],
    query: str,
) -> List[NormalizedSource]:
    """Normalize and deduplicate raw search results by canonical URL."""
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
    """Searches for web sources for a given claim."""

    def __init__(
        self,
        provider: SearchProvider,
        max_results_per_query: int = 5,
    ) -> None:
        self._provider = provider
        self._max_results = max_results_per_query
        self.last_search_error: Optional[str] = None

    async def search_for_claim(
        self, claim: ExtractedClaim
    ) -> List[NormalizedSource]:
        """Generate a query for *claim* and return normalized sources.

        Returns an empty list on any search provider failure.
        """
        self.last_search_error = None
        query = build_query(claim)
        try:
            raw_results = await self._provider.search(
                query, max_results=self._max_results
            )
            return normalize_results(raw_results, query=query)
        except Exception as exc:
            logger.warning("Search failed for query %r: %s", query[:60], exc)
            self.last_search_error = str(exc)
            return []
