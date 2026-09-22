"""Hermetic unit tests for live evidence retrievers and Supabase integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.supabase import SupabaseClient
from app.modules.evidence.duckduckgo_retriever import DuckDuckGoRetriever
from app.modules.evidence.live_retriever import LiveWebRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.nightcrawler_retriever import NightcrawlerRetriever
from app.modules.evidence.tavily_retriever import TavilySearchRetriever

# ==============================================================================
# TavilySearchRetriever Tests
# ==============================================================================


@pytest.mark.anyio
async def test_tavily_retriever_unconfigured() -> None:
    """TavilySearchRetriever returns [] when no API key is set."""
    retriever = TavilySearchRetriever(api_key=None)
    assert not retriever.is_configured
    assert retriever.name == "TAVILY_SEARCH"
    result = await retriever.retrieve("The Earth orbits the Sun.")
    assert result == []


@pytest.mark.anyio
async def test_tavily_retriever_empty_claim() -> None:
    """TavilySearchRetriever returns [] for blank/empty claims."""
    retriever = TavilySearchRetriever(api_key="tvly-mock-key")
    assert await retriever.retrieve("   ") == []


@pytest.mark.anyio
async def test_tavily_retriever_success_mocked() -> None:
    """TavilySearchRetriever correctly maps Tavily API response to RetrievedEvidenceItem."""
    retriever = TavilySearchRetriever(api_key="tvly-mock-key")

    mock_response = {
        "results": [
            {
                "url": "https://en.wikipedia.org/wiki/Water",
                "title": "Water - Wikipedia",
                "content": "Water is an inorganic compound with chemical formula H2O.",
                "score": 0.95,
            },
            {
                # Unsafe URL should be filtered by SSRF check
                "url": "http://169.254.169.254/latest/meta-data/",
                "title": "AWS Metadata",
                "content": "Secret credentials",
                "score": 0.99,
            },
        ]
    }

    mock_tavily_client = MagicMock()
    mock_tavily_client.search.return_value = mock_response

    with patch.dict(
        "sys.modules",
        {"tavily": MagicMock(TavilyClient=MagicMock(return_value=mock_tavily_client))},
    ):
        items = await retriever.retrieve("Water formula is H2O", max_passages=5)

    # AWS metadata result must have been filtered out
    assert len(items) == 1
    item = items[0]
    assert isinstance(item, RetrievedEvidenceItem)
    assert item.source_url == "https://en.wikipedia.org/wiki/Water"
    assert "H2O" in item.snippet
    assert item.retriever_name == "TAVILY_SEARCH"
    assert item.relevance_score == 0.95
    assert item.authority_score is not None and item.authority_score > 0.7


@pytest.mark.anyio
async def test_tavily_retriever_exception_handled() -> None:
    """TavilySearchRetriever never raises; returns [] on network/API exceptions."""
    retriever = TavilySearchRetriever(api_key="tvly-mock-key")

    mock_tavily_client = MagicMock()
    mock_tavily_client.search.side_effect = ConnectionError("Tavily unreachable")

    with patch.dict(
        "sys.modules",
        {"tavily": MagicMock(TavilyClient=MagicMock(return_value=mock_tavily_client))},
    ):
        items = await retriever.retrieve("Any claim")
        assert items == []


# ==============================================================================
# DuckDuckGoRetriever Tests
# ==============================================================================


@pytest.mark.anyio
async def test_duckduckgo_retriever_empty_claim() -> None:
    """DuckDuckGoRetriever returns [] for empty claims."""
    retriever = DuckDuckGoRetriever()
    assert await retriever.retrieve("") == []
    assert retriever.name == "DUCKDUCKGO_SEARCH"


@pytest.mark.anyio
async def test_duckduckgo_retriever_success_mocked() -> None:
    """DuckDuckGoRetriever maps DDGS response correctly and applies SSRF filter."""
    retriever = DuckDuckGoRetriever(max_results=5)

    mock_ddg_results = [
        {
            "href": "https://www.nature.com/articles/science-123",
            "title": "Quantum Mechanics Overview",
            "body": "Quantum mechanics describes nature at the smallest scales.",
        },
        {
            # Private network URL should be filtered out
            "href": "http://192.168.1.1/router",
            "title": "Router config",
            "body": "Admin interface",
        },
    ]

    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.text.return_value = mock_ddg_results
    mock_ddgs_context = MagicMock(
        __enter__=MagicMock(return_value=mock_ddgs_instance), __exit__=MagicMock()
    )

    with patch.dict(
        "sys.modules",
        {
            "duckduckgo_search": MagicMock(
                DDGS=MagicMock(return_value=mock_ddgs_context)
            )
        },
    ):
        items = await retriever.retrieve("Quantum mechanics", max_passages=3)

    assert len(items) == 1
    assert items[0].source_url == "https://www.nature.com/articles/science-123"
    assert items[0].retriever_name == "DUCKDUCKGO_SEARCH"
    assert "Quantum" in items[0].snippet


@pytest.mark.anyio
async def test_duckduckgo_retriever_exception_handled() -> None:
    """DuckDuckGoRetriever gracefully catches exceptions and returns []."""
    retriever = DuckDuckGoRetriever()

    mock_ddgs_context = MagicMock(
        __enter__=MagicMock(side_effect=RuntimeError("Rate limited")),
        __exit__=MagicMock(),
    )

    with patch.dict(
        "sys.modules",
        {
            "duckduckgo_search": MagicMock(
                DDGS=MagicMock(return_value=mock_ddgs_context)
            )
        },
    ):
        items = await retriever.retrieve("Some search")
        assert items == []


# ==============================================================================
# NightcrawlerRetriever Tests
# ==============================================================================


@pytest.mark.anyio
async def test_nightcrawler_empty_claim() -> None:
    """NightcrawlerRetriever returns [] for empty input."""
    retriever = NightcrawlerRetriever()
    assert await retriever.retrieve("   ") == []
    assert retriever.name == "NIGHTCRAWLER_WIKIPEDIA"


@pytest.mark.anyio
async def test_nightcrawler_success_mocked() -> None:
    """NightcrawlerRetriever cleans HTML entities and builds Wikipedia evidence."""
    retriever = NightcrawlerRetriever()

    mock_wiki_response = {
        "query": {
            "search": [
                {
                    "title": "DNA",
                    "snippet": 'Deoxyribonucleic acid is a polymer composed of two <span class="searchmatch">polynucleotide</span> chains &amp; encodes genetic instructions.',
                    "timestamp": "2026-01-01T00:00:00Z",
                    "wordcount": 5432,
                }
            ]
        }
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_wiki_response

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client_ctx = MagicMock(
        __aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()
    )

    with patch("httpx.AsyncClient", return_value=mock_client_ctx):
        items = await retriever.retrieve(
            "DNA structure and double helix", max_passages=3
        )

    assert len(items) == 1
    assert items[0].source_url == "https://en.wikipedia.org/wiki/DNA"
    assert "<span" not in items[0].snippet
    assert "&amp;" not in items[0].snippet
    assert "& encodes" in items[0].snippet
    assert items[0].publisher == "Wikipedia"
    assert items[0].retriever_name == "NIGHTCRAWLER_WIKIPEDIA"


@pytest.mark.anyio
async def test_nightcrawler_http_error_handled() -> None:
    """NightcrawlerRetriever handles HTTP 500 gracefully."""
    retriever = NightcrawlerRetriever()

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client_ctx = MagicMock(
        __aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()
    )

    with patch("httpx.AsyncClient", return_value=mock_client_ctx):
        items = await retriever.retrieve("Some topic")
        assert items == []


# ==============================================================================
# LiveWebRetriever Fallback Chain Tests
# ==============================================================================


@pytest.mark.anyio
async def test_live_retriever_tier1_wins() -> None:
    """When Tavily (Tier 1) returns results, DDG and Nightcrawler are not called."""
    mock_item = RetrievedEvidenceItem(
        snippet="Tavily evidence",
        source_url="https://example.com/tavily",
        source_title="Tavily Source",
        retriever_name="TAVILY_SEARCH",
    )

    tavily_mock = AsyncMock(spec=TavilySearchRetriever)
    tavily_mock.is_configured = True
    tavily_mock.retrieve.return_value = [mock_item]

    ddg_mock = AsyncMock(spec=DuckDuckGoRetriever)
    nightcrawler_mock = AsyncMock(spec=NightcrawlerRetriever)

    chain = LiveWebRetriever(
        tavily=tavily_mock,
        duckduckgo=ddg_mock,
        nightcrawler=nightcrawler_mock,
    )
    assert chain.name == "LIVE_WEB_RETRIEVER"

    results = await chain.retrieve("Any claim")
    assert len(results) == 1
    assert results[0].snippet == "Tavily evidence"
    tavily_mock.retrieve.assert_awaited_once()
    ddg_mock.retrieve.assert_not_called()
    nightcrawler_mock.retrieve.assert_not_called()


@pytest.mark.anyio
async def test_live_retriever_tier2_fallback_when_tier1_empty() -> None:
    """When Tavily returns [], falls through to DuckDuckGo (Tier 2)."""
    mock_item = RetrievedEvidenceItem(
        snippet="DDG evidence",
        source_url="https://example.com/ddg",
        source_title="DDG Source",
        retriever_name="DUCKDUCKGO_SEARCH",
    )

    tavily_mock = AsyncMock(spec=TavilySearchRetriever)
    tavily_mock.is_configured = True
    tavily_mock.retrieve.return_value = []

    ddg_mock = AsyncMock(spec=DuckDuckGoRetriever)
    ddg_mock.retrieve.return_value = [mock_item]

    nightcrawler_mock = AsyncMock(spec=NightcrawlerRetriever)

    chain = LiveWebRetriever(
        tavily=tavily_mock,
        duckduckgo=ddg_mock,
        nightcrawler=nightcrawler_mock,
    )

    results = await chain.retrieve("Any claim")
    assert len(results) == 1
    assert results[0].snippet == "DDG evidence"
    tavily_mock.retrieve.assert_awaited_once()
    ddg_mock.retrieve.assert_awaited_once()
    nightcrawler_mock.retrieve.assert_not_called()


@pytest.mark.anyio
async def test_live_retriever_tier3_fallback_when_tier1_and_2_empty() -> None:
    """When Tavily and DDG return [], falls through to Nightcrawler (Tier 3)."""
    mock_item = RetrievedEvidenceItem(
        snippet="Wikipedia evidence",
        source_url="https://en.wikipedia.org/wiki/Topic",
        source_title="Topic",
        retriever_name="NIGHTCRAWLER_WIKIPEDIA",
    )

    tavily_mock = AsyncMock(spec=TavilySearchRetriever)
    tavily_mock.is_configured = False  # Not configured

    ddg_mock = AsyncMock(spec=DuckDuckGoRetriever)
    ddg_mock.retrieve.return_value = []

    nightcrawler_mock = AsyncMock(spec=NightcrawlerRetriever)
    nightcrawler_mock.retrieve.return_value = [mock_item]

    chain = LiveWebRetriever(
        tavily=tavily_mock,
        duckduckgo=ddg_mock,
        nightcrawler=nightcrawler_mock,
    )

    results = await chain.retrieve("Any claim")
    assert len(results) == 1
    assert results[0].snippet == "Wikipedia evidence"
    ddg_mock.retrieve.assert_awaited_once()
    nightcrawler_mock.retrieve.assert_awaited_once()


@pytest.mark.anyio
async def test_live_retriever_all_tiers_exhausted_returns_empty() -> None:
    """When all tiers return [], returns [] gracefully."""
    tavily_mock = AsyncMock(spec=TavilySearchRetriever)
    tavily_mock.is_configured = True
    tavily_mock.retrieve.return_value = []

    ddg_mock = AsyncMock(spec=DuckDuckGoRetriever)
    ddg_mock.retrieve.return_value = []

    nightcrawler_mock = AsyncMock(spec=NightcrawlerRetriever)
    nightcrawler_mock.retrieve.return_value = []

    chain = LiveWebRetriever(
        tavily=tavily_mock,
        duckduckgo=ddg_mock,
        nightcrawler=nightcrawler_mock,
    )

    results = await chain.retrieve("Obscure claim with no evidence")
    assert results == []


# ==============================================================================
# SupabaseClient Tests
# ==============================================================================


@pytest.mark.anyio
async def test_supabase_client_unconfigured() -> None:
    """SupabaseClient correctly indicates unconfigured status."""
    client = SupabaseClient(url=None)
    assert not client.is_configured
    assert client.active_key is None
    status = await client.check_connectivity()
    assert status == {"configured": False, "status": "unconfigured"}
    query_result = await client.query_table("verifications")
    assert query_result == []


@pytest.mark.anyio
async def test_supabase_client_check_connectivity_available() -> None:
    """SupabaseClient returns available when endpoint responds 200."""
    client = SupabaseClient(
        url="https://mock-proj.supabase.co",
        publishable_key="sb_publishable_test",
        secret_key="sb_secret_test",
    )
    assert client.is_configured
    assert client.active_key == "sb_secret_test"

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mock_http_client = AsyncMock()
    mock_http_client.get.return_value = mock_resp
    mock_ctx = MagicMock(
        __aenter__=AsyncMock(return_value=mock_http_client), __aexit__=AsyncMock()
    )

    with patch("httpx.AsyncClient", return_value=mock_ctx):
        status = await client.check_connectivity()
        assert status == {"configured": True, "status": "available"}


@pytest.mark.anyio
async def test_supabase_client_check_connectivity_unavailable() -> None:
    """SupabaseClient returns unavailable when endpoint fails or errors."""
    client = SupabaseClient(
        url="https://mock-proj.supabase.co",
        publishable_key="sb_publishable_test",
    )

    mock_http_client = AsyncMock()
    mock_http_client.get.side_effect = httpx.ConnectError("Network down")
    mock_ctx = MagicMock(
        __aenter__=AsyncMock(return_value=mock_http_client),
        __aexit__=AsyncMock(return_value=False),
    )

    with patch("httpx.AsyncClient", return_value=mock_ctx):
        status = await client.check_connectivity()
        assert status == {"configured": True, "status": "unavailable"}


@pytest.mark.anyio
async def test_supabase_client_query_table_success() -> None:
    """SupabaseClient queries PostgREST endpoint and parses rows."""
    client = SupabaseClient(
        url="https://mock-proj.supabase.co",
        publishable_key="sb_publishable_test",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"id": "job-1", "status": "completed"}]

    mock_http_client = AsyncMock()
    mock_http_client.get.return_value = mock_resp
    mock_ctx = MagicMock(
        __aenter__=AsyncMock(return_value=mock_http_client), __aexit__=AsyncMock()
    )

    with patch("httpx.AsyncClient", return_value=mock_ctx):
        rows = await client.query_table("verification_jobs")
        assert len(rows) == 1
        assert rows[0]["id"] == "job-1"
