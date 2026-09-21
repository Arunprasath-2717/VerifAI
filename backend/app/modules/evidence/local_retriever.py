"""Deterministic in-memory evidence retriever for hermetic execution and testing."""

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority


@dataclass
class KnowledgePassage:
    """An indexed reference passage stored in the local knowledge base."""

    title: str
    snippet: str
    url: str
    publisher: str
    publication_date: str
    tokens: set[str]


class LocalPassageRetriever(BaseEvidenceRetriever):
    """Deterministic in-memory evidence retriever — DEVELOPMENT / TESTING ONLY.

    This retriever operates entirely in-process against a small curated set of
    reference passages (≈6 entries by default).  It performs no external network
    requests and produces fully reproducible, hermetic results suitable for unit
    tests and local demonstrations.

    KNOWN LIMITATIONS (not suitable for production):
    - The passage index is intentionally sparse.  Claims about topics not covered
      by an indexed passage will receive INSUFFICIENT_EVIDENCE or may trigger
      spurious numeric-discrepancy detection when unrelated numbers co-occur.
    - Relevance scoring is lexical token-overlap (Jaccard-like); it is not
      semantic or embedding-based.
    - Evidence sourced from this retriever is labelled ``retriever_name =
      "LOCAL_PASSAGE_INDEX"`` in every response so that consumers can
      distinguish it from live web or database evidence.
    - Do NOT present LOCAL_PASSAGE_INDEX results as authoritative live evidence
      in any user-facing context outside of development demonstrations.

    For production evidence retrieval, configure :class:`SafeWebRetriever` with
    a valid Wikipedia API endpoint, or a future vector-store retriever (Phase 4).
    """

    def __init__(self, passages: list[dict[str, str]] | None = None) -> None:
        self._passages: list[KnowledgePassage] = []
        # Seed with initial core facts
        seed_data = (
            passages if passages is not None else self._get_default_reference_passages()
        )
        for p in seed_data:
            self.add_passage(
                title=p["title"],
                snippet=p["snippet"],
                url=p["url"],
                publisher=p["publisher"],
                publication_date=p["publication_date"],
            )

    @property
    def name(self) -> str:
        return "LOCAL_PASSAGE_INDEX"

    def add_passage(
        self,
        title: str,
        snippet: str,
        url: str,
        publisher: str,
        publication_date: str,
    ) -> None:
        """Register a new verified passage into the in-memory index."""
        text = f"{title} {snippet}".lower()
        tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", text))
        self._passages.append(
            KnowledgePassage(
                title=title,
                snippet=snippet,
                url=url,
                publisher=publisher,
                publication_date=publication_date,
                tokens=tokens,
            )
        )

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        """Retrieve top matching passages based on token overlap score."""
        claim_tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", claim_text.lower()))
        if not claim_tokens:
            return []

        scored: list[tuple[float, KnowledgePassage]] = []
        for passage in self._passages:
            overlap = len(claim_tokens & passage.tokens)
            if overlap == 0:
                continue
            # Jaccard-like score with length bias
            score = overlap / (len(claim_tokens) + len(passage.tokens) - overlap)
            # Require at least 2 common tokens or >0.12 score for relevance
            if overlap >= 2 or score > 0.12:
                scored.append((score, passage))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[RetrievedEvidenceItem] = []

        for score, passage in scored[:max_passages]:
            results.append(
                RetrievedEvidenceItem(
                    id=uuid.uuid4(),
                    source_url=passage.url,
                    source_title=passage.title,
                    publisher=passage.publisher,
                    publication_date=passage.publication_date,
                    retrieval_timestamp=datetime.now(UTC),
                    snippet=passage.snippet,
                    query_used=claim_text,
                    retriever_name=self.name,
                    relevance_score=round(score, 4),
                    authority_score=compute_domain_authority(passage.url),
                    metadata_json={
                        "overlap_tokens": len(claim_tokens & passage.tokens)
                    },
                )
            )

        return results

    @staticmethod
    def _get_default_reference_passages() -> list[dict[str, str]]:
        """Core reference knowledge corpus for testing and local demonstration."""
        return [
            {
                "title": "Speed of Light in Vacuum",
                "snippet": (
                    "The speed of light in vacuum, commonly denoted c, is a universal "
                    "physical constant exactly equal to 299,792,458 metres per second."
                ),
                "url": "https://en.wikipedia.org/wiki/Speed_of_light",
                "publisher": "Wikipedia",
                "publication_date": "2024-01-15",
            },
            {
                "title": "Apollo 11 Mission Overview",
                "snippet": (
                    "Apollo 11 was the American spaceflight that first landed humans "
                    "on the Moon. Commander Neil Armstrong and lunar module pilot Buzz "
                    "Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969."
                ),
                "url": "https://www.nasa.gov/mission_pages/apollo/missions/apollo11.html",
                "publisher": "NASA",
                "publication_date": "2023-07-20",
            },
            {
                "title": "Chemical Structure of Water",
                "snippet": (
                    "Water is an inorganic compound with the chemical formula H2O. "
                    "It is composed of two hydrogen atoms bonded to one oxygen atom."
                ),
                "url": "https://pubchem.ncbi.nlm.nih.gov/compound/Water",
                "publisher": "NIH PubChem",
                "publication_date": "2024-02-10",
            },
            {
                "title": "Earth's Atmosphere and Nitrogen",
                "snippet": (
                    "Nitrogen makes up approximately 78 percent of Earth's atmosphere "
                    "by volume, followed by oxygen at approximately 21 percent."
                ),
                "url": "https://climate.nasa.gov/news/earth-atmosphere",
                "publisher": "NASA Climate",
                "publication_date": "2023-11-01",
            },
            {
                "title": "Capital of France",
                "snippet": (
                    "Paris is the capital and most populous city of France, with an "
                    "estimated population of over 2.1 million residents as of 2023."
                ),
                "url": "https://en.wikipedia.org/wiki/Paris",
                "publisher": "Wikipedia",
                "publication_date": "2024-03-01",
            },
            {
                "title": "Photosynthesis and Plants",
                "snippet": (
                    "Photosynthesis is a biological process used by plants and other "
                    "organisms to convert light energy into chemical energy stored in "
                    "carbohydrates."
                ),
                "url": "https://www.nature.com/subjects/photosynthesis",
                "publisher": "Nature",
                "publication_date": "2023-09-12",
            },
        ]
