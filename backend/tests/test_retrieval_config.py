"""Tests for KB chunking invariants and retrieval-related settings wiring."""

import asyncio
import random

import pytest

from app.core.config import clear_settings_cache
from app.core.errors import AppError
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.evidence.nightcrawler_retriever import build_search_keywords
from app.modules.knowledge.ingestion import chunk_document_text
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    UnknownReason,
    VerdictType,
    VerificationCreateRequest,
    VerificationOptions,
)

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

_WORDS = ["alpha", "beta.", "gamma", "delta\n\n", "zeta!", "eta", "theta,", "x" * 70]


@pytest.mark.parametrize("seed", range(25))
def test_chunks_have_exact_offsets_overlap_and_full_coverage(seed: int) -> None:
    rng = random.Random(seed)
    text = " ".join(rng.choice(_WORDS) for _ in range(rng.randint(1, 400))).strip()
    size = rng.randint(20, 300)
    overlap = rng.randint(0, size)

    chunks = chunk_document_text(text, size, overlap)

    assert chunks
    for chunk in chunks:
        assert text[chunk.start_offset : chunk.end_offset] == chunk.text
        assert len(chunk.text) <= size
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        assert nxt.start_offset > prev.start_offset
    covered = set()
    for chunk in chunks:
        covered.update(range(chunk.start_offset, chunk.end_offset))
    assert all(i in covered for i, ch in enumerate(text) if not ch.isspace())


def test_consecutive_chunks_actually_overlap() -> None:
    text = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(6))
    chunks = chunk_document_text(text, 300, 100)
    overlaps = [
        a.end_offset - b.start_offset for a, b in zip(chunks, chunks[1:], strict=False)
    ]
    assert overlaps and all(0 < o <= 100 for o in overlaps)


# ---------------------------------------------------------------------------
# Wikipedia keyword construction
# ---------------------------------------------------------------------------


def test_search_keywords_keep_words_with_punctuation() -> None:
    assert build_search_keywords("The Eiffel Tower is in Paris.") == (
        "The Eiffel Tower Paris"
    )
    assert "0" in build_search_keywords("Water freezes at 0 degrees Celsius.").split()


# ---------------------------------------------------------------------------
# Settings wiring
# ---------------------------------------------------------------------------


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch):
    def _set(**values: str) -> None:
        for key, value in values.items():
            monkeypatch.setenv(key, value)
        clear_settings_cache()

    yield _set
    clear_settings_cache()


class _SlowRetriever(BaseEvidenceRetriever):
    @property
    def name(self) -> str:
        return "SLOW"

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        await asyncio.sleep(5)
        return []


def test_demo_index_disabled_outside_development(env) -> None:
    env(ENVIRONMENT="production", API_KEYS='{"ops": "ops-key-0123456789abcdef"}')
    assert not isinstance(VerificationOrchestrator().retriever, LocalPassageRetriever)


def test_demo_index_enabled_in_development(env) -> None:
    env(ENVIRONMENT="development")
    assert isinstance(VerificationOrchestrator().retriever, LocalPassageRetriever)


@pytest.mark.anyio
async def test_production_without_evidence_source_returns_unknown(env) -> None:
    env(ENVIRONMENT="production", API_KEYS='{"ops": "ops-key-0123456789abcdef"}')
    response = await VerificationOrchestrator().verify(
        VerificationCreateRequest(text="Water freezes at 0 degrees Celsius.")
    )
    assert response.claims[0].verdict == VerdictType.UNKNOWN


@pytest.mark.anyio
async def test_max_input_chars_setting_enforced(env) -> None:
    env(VERIFICATION_MAX_INPUT_CHARS="10")
    with pytest.raises(AppError) as exc:
        await VerificationOrchestrator().verify(
            VerificationCreateRequest(text="This text is longer than ten characters.")
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_max_claims_setting_caps_request(env) -> None:
    env(VERIFICATION_MAX_CLAIMS="2")
    response = await VerificationOrchestrator().verify(
        VerificationCreateRequest(
            text="Water is wet. Fire is hot. Ice is cold. Snow is white.",
            options=VerificationOptions(max_claims=10),
        )
    )
    assert response.total_claims == 2


@pytest.mark.anyio
async def test_live_search_default_comes_from_settings(env) -> None:
    env(ENABLE_LIVE_SEARCH="true")
    orchestrator = VerificationOrchestrator(retriever=_SlowRetriever())
    from unittest.mock import AsyncMock, patch

    with patch(
        "app.modules.evidence.live_retriever.LiveWebRetriever.retrieve",
        AsyncMock(return_value=[]),
    ) as live:
        response = await orchestrator.verify(
            VerificationCreateRequest(text="Water freezes at 0 degrees Celsius.")
        )
    assert live.await_count == 1
    assert response.claims[0].unknown_reason == UnknownReason.SEARCH_UNKNOWN


@pytest.mark.anyio
async def test_retrieval_timeout_setting_bounds_slow_providers(env) -> None:
    env(RETRIEVAL_TIMEOUT_SECONDS="0.05")
    orchestrator = VerificationOrchestrator(retriever=_SlowRetriever())
    response = await asyncio.wait_for(
        orchestrator.verify(
            VerificationCreateRequest(text="Water freezes at 0 degrees Celsius.")
        ),
        timeout=2,
    )
    assert response.claims[0].verdict == VerdictType.UNKNOWN
    assert any(a.event_type == "DEGRADED_EXECUTION" for a in response.audit_trail)


class _DelayRetriever(BaseEvidenceRetriever):
    def __init__(self) -> None:
        self.active = 0
        self.peak = 0

    @property
    def name(self) -> str:
        return "DELAY"

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.05)
        self.active -= 1
        return []


@pytest.mark.anyio
async def test_claims_processed_concurrently_with_ordered_audit(env) -> None:
    env(VERIFICATION_CLAIM_CONCURRENCY="3")
    retriever = _DelayRetriever()
    text = "Water is wet. Fire is hot. Ice is cold. Snow is white. Grass is green."
    response = await VerificationOrchestrator(retriever=retriever).verify(
        VerificationCreateRequest(
            text=text, options=VerificationOptions(enable_kb_search=False)
        )
    )
    assert response.total_claims == 5
    assert retriever.peak == 3  # bounded by the configured concurrency
    assert [c.claim_index for c in response.claims] == [0, 1, 2, 3, 4]
    retrieval_order = [
        a.message
        for a in response.audit_trail
        if a.event_type == "EXTERNAL_RETRIEVAL_STARTED"
    ]
    assert retrieval_order == [
        f"Searching external provider for claim {i}." for i in range(5)
    ]
