"""Safe live web evidence retrieval via Wikipedia public API."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url

logger = logging.getLogger("verifai.retriever.web")


class SafeWebRetriever(BaseEvidenceRetriever):
    """Live web retriever utilizing Wikipedia public REST search API.

    Enforces strict timeout bounds, SSRF destination validation, and
    graceful degradation upon network unavailability or connection errors.
    """

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, timeout_seconds: float = 4.0) -> None:
        self.timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "SAFE_WIKIPEDIA_WEB_SEARCH"

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        """Perform search query against Wikipedia public API with provenance."""
        # Sanitize query: extract main alphanumeric keywords
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
        headers = {
            "User-Agent": "VerifAI-Research-Verifier/1.0 (academic; non-commercial)"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.WIKIPEDIA_API_URL, params=params, headers=headers
                )
                if response.status_code != 200:
                    logger.warning(
                        "Live web retrieval returned non-200 status: %d",
                        response.status_code,
                    )
                    return []

                data = response.json()
                search_results = data.get("query", {}).get("search", [])

                evidence_items: list[RetrievedEvidenceItem] = []
                for item in search_results:
                    title = item.get("title", "")
                    raw_snippet = item.get("snippet", "")
                    # Remove Wikipedia HTML snippet tags like <span class="searchmatch">
                    clean_snippet = (
                        raw_snippet.replace('<span class="searchmatch">', "")
                        .replace("</span>", "")
                        .replace("&quot;", '"')
                        .replace("&amp;", "&")
                    )

                    title_path = quote(title.replace(" ", "_"))
                    page_url = f"https://en.wikipedia.org/wiki/{title_path}"

                    if not is_safe_url(page_url):
                        continue

                    evidence_items.append(
                        RetrievedEvidenceItem(
                            id=uuid.uuid4(),
                            source_url=page_url,
                            source_title=title,
                            publisher="Wikipedia",
                            publication_date=item.get("timestamp", "")[:10]
                            if item.get("timestamp")
                            else None,
                            retrieval_timestamp=datetime.now(UTC),
                            snippet=clean_snippet,
                            query_used=keywords,
                            retriever_name=self.name,
                            relevance_score=0.85,
                            authority_score=compute_domain_authority(page_url),
                            metadata_json={"wordcount": item.get("wordcount", 0)},
                        )
                    )

                return evidence_items

        except Exception as exc:
            # Graceful degradation: never crash pipeline if live web search fails
            logger.warning(
                "Live web retrieval failed gracefully: %s", type(exc).__name__
            )
            return []
