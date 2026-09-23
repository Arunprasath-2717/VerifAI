"""Tests for evidence retrieval, SSRF prevention, and source provenance."""

import pytest

from app.modules.evidence.fixture_retriever import TestFixtureRetriever
from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.security import compute_domain_authority, is_safe_url


def test_is_safe_url_ssrf_prevention() -> None:
    """Verify SSRF filter blocks loopback, private networks, and cloud metadata."""
    # Forbidden loopback & localhost
    assert is_safe_url("http://localhost:8000/api") is False
    assert is_safe_url("http://127.0.0.1:5432") is False
    assert is_safe_url("http://127.0.0.2") is False
    assert is_safe_url("http://[::1]/status") is False

    # Forbidden private subnets
    assert is_safe_url("http://10.0.0.1/admin") is False
    assert is_safe_url("http://172.16.5.10/") is False
    assert is_safe_url("http://192.168.1.1/") is False

    # Forbidden cloud metadata endpoints
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://metadata.google.internal/computeMetadata/v1/") is False
    assert is_safe_url("http://instance-data/") is False

    # Forbidden schemes
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://ftp.example.com/file") is False
    assert is_safe_url("javascript:alert(1)") is False

    # Allowed public URLs
    assert is_safe_url("https://en.wikipedia.org/wiki/Water") is True
    assert is_safe_url("https://www.nature.com/articles/12345") is True
    assert is_safe_url("https://api.nasa.gov/planetary/apod") is True


def test_compute_domain_authority() -> None:
    """Verify domain authority scoring heuristics."""
    assert compute_domain_authority("https://www.cdc.gov/flu") >= 0.90
    assert compute_domain_authority("https://harvard.edu/research") >= 0.90
    assert compute_domain_authority("https://en.wikipedia.org/wiki/Earth") >= 0.75
    assert compute_domain_authority("https://random-unverified-blog.xyz") == 0.60
    assert compute_domain_authority(None) == 0.50


@pytest.mark.anyio
async def test_local_passage_retriever_hit() -> None:
    """Verify LocalPassageRetriever retrieves relevant passage for known fact."""
    retriever = LocalPassageRetriever()
    claim = "Water has the chemical formula H2O."
    evidence = await retriever.retrieve(claim, max_passages=3)

    assert len(evidence) >= 1
    ev = evidence[0]
    assert isinstance(ev, RetrievedEvidenceItem)
    assert ev.retriever_name == "LOCAL_PASSAGE_INDEX"
    assert "H2O" in ev.snippet or "water" in ev.snippet.lower()
    assert ev.authority_score is not None and ev.authority_score > 0.7
    assert ev.relevance_score is not None and ev.relevance_score > 0.0


@pytest.mark.anyio
async def test_local_passage_retriever_miss() -> None:
    """Verify LocalPassageRetriever returns empty list when no passage matches."""
    retriever = LocalPassageRetriever()
    claim = "Xyzzy non-existent quantum flibbertigibbet."
    evidence = await retriever.retrieve(claim, max_passages=3)
    assert evidence == []


@pytest.mark.anyio
async def test_fixture_retriever() -> None:
    """Verify TestFixtureRetriever returns injected mocked passages."""
    fixture_items = [
        RetrievedEvidenceItem(
            snippet="Test passage for fixture verification.",
            source_url="https://test.verifai.local",
            source_title="Test Document",
            retriever_name="test_fixture",
            authority_score=0.9,
            relevance_score=0.95,
        )
    ]
    retriever = TestFixtureRetriever(fixture_map={"test claim": fixture_items})

    results = await retriever.retrieve("test claim")
    assert len(results) == 1
    assert results[0].snippet == "Test passage for fixture verification."

    # Unknown claim in fixture retriever returns empty list
    empty_results = await retriever.retrieve("unknown claim")
    assert empty_results == []
