"""Verification evidence retry and explicit-source consent regression tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.token_budget.cache import AnalysisCacheService
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    VerdictType,
    VerificationCreateRequest,
    VerificationOptions,
)


@pytest.fixture(autouse=True)
def reset_analysis_cache():
    AnalysisCacheService.reset_for_test()
    yield
    AnalysisCacheService.reset_for_test()


@pytest.mark.anyio
async def test_no_evidence_unknown_does_not_block_later_success():
    source = AsyncMock()
    source.name = "TEST_SOURCE"
    source.retrieve = AsyncMock(return_value=[])
    orchestrator = VerificationOrchestrator(
        settings=Settings(ENABLE_LIVE_SEARCH=False), retriever=source
    )
    request = VerificationCreateRequest(
        text="Paris is the capital of France.",
        options=VerificationOptions(enable_kb_search=False),
    )
    first = await orchestrator.verify(request)
    assert first.claims[0].verdict == VerdictType.UNKNOWN
    assert not first.claims[0].evidence

    source.retrieve.return_value = [
        RetrievedEvidenceItem(
            snippet="Paris is the capital of France.", retriever_name="TEST_SOURCE"
        )
    ]
    second = await orchestrator.verify(request)
    assert second.claims[0].verdict == VerdictType.SUPPORTED
    assert second.claims[0].evidence
    assert source.retrieve.await_count == 2


@pytest.mark.anyio
async def test_refresh_replaces_cached_result_for_identical_request():
    source = AsyncMock()
    source.name = "TEST_SOURCE"
    source.retrieve = AsyncMock(
        return_value=[
            RetrievedEvidenceItem(
                snippet="Paris is the capital of France.",
                retriever_name="TEST_SOURCE",
            )
        ]
    )
    orchestrator = VerificationOrchestrator(
        settings=Settings(ENABLE_LIVE_SEARCH=False), retriever=source
    )
    options = VerificationOptions(enable_kb_search=False)
    first = await orchestrator.verify(
        VerificationCreateRequest(
            text="Paris is the capital of France.", options=options
        )
    )
    assert first.claims[0].verdict == VerdictType.SUPPORTED
    assert source.retrieve.await_count == 1

    source.retrieve.return_value = [
        RetrievedEvidenceItem(
            snippet="Berlin is the capital of Germany.",
            retriever_name="TEST_SOURCE",
        )
    ]
    refreshed = await orchestrator.verify(
        VerificationCreateRequest(
            text="Paris is the capital of France.",
            options=VerificationOptions(enable_kb_search=False, bypass_cache=True),
        )
    )
    assert source.retrieve.await_count == 2
    assert refreshed.verification_id != first.verification_id
    assert (
        refreshed.claims[0].evidence[0].snippet == "Berlin is the capital of Germany."
    )

    cached = await orchestrator.verify(
        VerificationCreateRequest(
            text="Paris is the capital of France.", options=options
        )
    )
    assert cached.verification_id == refreshed.verification_id
    assert source.retrieve.await_count == 2


@pytest.mark.anyio
async def test_explicit_web_opt_out_blocks_retrievers_despite_server_default():
    source = AsyncMock()
    source.name = "LOCAL_INDEX"
    source.retrieve = AsyncMock()
    with patch(
        "app.modules.verification.orchestrator.LiveWebRetriever.from_settings",
        side_effect=RuntimeError("External retrieval must not be used"),
    ):
        orchestrator = VerificationOrchestrator(
            settings=Settings(ENABLE_LIVE_SEARCH=True), retriever=source
        )
        result = await orchestrator.verify(
            VerificationCreateRequest(
                text="Paris is the capital of France.",
                options=VerificationOptions(
                    enable_live_search=False, enable_kb_search=False
                ),
            )
        )
    assert result.claims[0].verdict == VerdictType.UNKNOWN
    assert not result.claims[0].evidence
    source.retrieve.assert_not_awaited()


@pytest.mark.anyio
async def test_empty_live_search_has_traceable_audit_warning():
    source = AsyncMock()
    source.name = "TEST_LIVE_PROVIDER"
    source.retrieve = AsyncMock(return_value=[])
    with patch(
        "app.modules.verification.orchestrator.LiveWebRetriever.from_settings",
        return_value=source,
    ):
        result = await VerificationOrchestrator(
            settings=Settings(ENABLE_LIVE_SEARCH=False)
        ).verify(
            VerificationCreateRequest(
                text="Paris is the capital of France.",
                options=VerificationOptions(
                    enable_live_search=True, enable_kb_search=False
                ),
            )
        )
    assert result.claims[0].verdict == VerdictType.UNKNOWN
    assert any(
        event.event_type == "EXTERNAL_EVIDENCE_EMPTY" and event.stage == "RETRIEVAL"
        for event in result.audit_trail
    )
