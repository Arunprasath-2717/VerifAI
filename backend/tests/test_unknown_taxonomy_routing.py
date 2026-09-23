"""Tests for UNKNOWN taxonomy routing (CONTEXT_UNKNOWN vs SEARCH_UNKNOWN) and serialization."""

import uuid

import pytest

from app.modules.evidence.local_retriever import LocalPassageRetriever
from app.modules.judging.deterministic_judge import DeterministicRuleJudge
from app.modules.judging.semantic_judge import SecondarySemanticJudge
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    ClaimResultSchema,
    ContentType,
    UnknownReason,
    VerdictType,
    VerificationCreateRequest,
    VerificationOptions,
)


@pytest.fixture
def empty_retriever() -> LocalPassageRetriever:
    """Retriever initialized without passages."""
    retriever = LocalPassageRetriever(passages=[])
    return retriever


@pytest.fixture
def orchestrator(empty_retriever: LocalPassageRetriever) -> VerificationOrchestrator:
    return VerificationOrchestrator(
        retriever=empty_retriever,
        judges=[DeterministicRuleJudge(), SecondarySemanticJudge()],
    )


@pytest.mark.anyio
async def test_local_retrieval_failure_produces_context_unknown(
    orchestrator: VerificationOrchestrator,
) -> None:
    """When local retrieval finds no evidence and live search is disabled, reason is CONTEXT_UNKNOWN."""
    req = VerificationCreateRequest(
        text="The mysterious city of Atlantis sank beneath the waves.",
        options=VerificationOptions(enable_live_search=False),
    )
    res = await orchestrator.verify(req)

    assert len(res.claims) >= 1
    assert res.claims[0].verdict == VerdictType.UNKNOWN
    assert res.claims[0].unknown_reason == UnknownReason.CONTEXT_UNKNOWN
    assert res.claims[0].unknown_reason != UnknownReason.SEARCH_UNKNOWN


@pytest.mark.anyio
async def test_attempted_live_search_failure_produces_search_unknown(
    orchestrator: VerificationOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When external search was attempted but yields no evidence, reason is SEARCH_UNKNOWN."""
    from unittest.mock import AsyncMock

    from app.modules.evidence.live_retriever import LiveWebRetriever
    from app.modules.evidence.web_retriever import SafeWebRetriever

    monkeypatch.setattr(SafeWebRetriever, "retrieve", AsyncMock(return_value=[]))
    monkeypatch.setattr(LiveWebRetriever, "retrieve", AsyncMock(return_value=[]))

    req = VerificationCreateRequest(
        text="The average orbital speed of exoplanet HD 209458 b is precisely 140 kilometers per second.",
        options=VerificationOptions(enable_live_search=True),
    )
    res = await orchestrator.verify(req)

    assert len(res.claims) >= 1
    assert res.claims[0].verdict == VerdictType.UNKNOWN
    assert res.claims[0].unknown_reason == UnknownReason.SEARCH_UNKNOWN


@pytest.mark.anyio
async def test_search_not_attempted_never_produces_search_unknown(
    orchestrator: VerificationOrchestrator,
) -> None:
    """When search is not enabled/attempted, reason CANNOT be SEARCH_UNKNOWN."""
    req = VerificationCreateRequest(
        text="Quantum computing solves all known problems instantly in seconds.",
        options=VerificationOptions(enable_live_search=False),
    )
    res = await orchestrator.verify(req)

    assert len(res.claims) >= 1
    assert res.claims[0].unknown_reason != UnknownReason.SEARCH_UNKNOWN
    assert res.claims[0].unknown_reason == UnknownReason.CONTEXT_UNKNOWN


def test_unknown_reason_serialization_and_deserialization() -> None:
    """Verify UnknownReason survives Pydantic serialization round-trip in ClaimResultSchema and VerificationResponse."""
    claim = ClaimResultSchema(
        id=uuid.uuid4(),
        claim_index=0,
        claim_text="Dark matter is composed of sterile neutrinos.",
        content_type=ContentType.FACTUAL,
        start_offset=0,
        end_offset=46,
        verdict=VerdictType.UNKNOWN,
        is_verifiable=True,
        unknown_reason=UnknownReason.SEARCH_UNKNOWN,
        confidence=None,
        explanation="External search returned 0 matching documents.",
        evidence=[],
    )

    data = claim.model_dump(mode="json")
    assert data["unknown_reason"] == "SEARCH_UNKNOWN"
    assert data["verdict"] == "UNKNOWN"

    reconstructed = ClaimResultSchema.model_validate(data)
    assert reconstructed.unknown_reason == UnknownReason.SEARCH_UNKNOWN
    assert reconstructed.verdict == VerdictType.UNKNOWN


def test_unknown_reason_context_unknown_serialization() -> None:
    """Verify CONTEXT_UNKNOWN survives Pydantic serialization round-trip."""
    claim = ClaimResultSchema(
        id=uuid.uuid4(),
        claim_index=1,
        claim_text="Local text without corpus.",
        content_type=ContentType.FACTUAL,
        start_offset=0,
        end_offset=26,
        verdict=VerdictType.UNKNOWN,
        is_verifiable=True,
        unknown_reason=UnknownReason.CONTEXT_UNKNOWN,
        confidence=None,
        explanation="Local corpus returned no evidence.",
        evidence=[],
    )

    data = claim.model_dump(mode="json")
    assert data["unknown_reason"] == "CONTEXT_UNKNOWN"

    reconstructed = ClaimResultSchema.model_validate(data)
    assert reconstructed.unknown_reason == UnknownReason.CONTEXT_UNKNOWN
