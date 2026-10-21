"""Evidence retrieval and provenance package."""

from app.modules.evidence.duckduckgo_retriever import DuckDuckGoRetriever
from app.modules.evidence.fixture_retriever import TestFixtureRetriever
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.live_retriever import LiveWebRetriever
from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.nightcrawler_retriever import NightcrawlerRetriever
from app.modules.evidence.security import compute_domain_authority, is_safe_url
from app.modules.evidence.tavily_retriever import TavilySearchRetriever

__all__ = [
    "BaseEvidenceRetriever",
    "RetrievedEvidenceItem",
    "LocalPassageRetriever",
    "TestFixtureRetriever",
    "TavilySearchRetriever",
    "DuckDuckGoRetriever",
    "NightcrawlerRetriever",
    "LiveWebRetriever",
    "is_safe_url",
    "compute_domain_authority",
]
