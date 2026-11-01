"""Atomic token reservations must degrade gracefully under parallel claim jobs."""

import pytest

from app.core.config import Settings
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import VerificationCreateRequest, VerificationOptions


class FixedEvidence(BaseEvidenceRetriever):
    @property
    def name(self) -> str:
        return "fixed-budget-test"

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        return [
            RetrievedEvidenceItem(
                snippet=f"{claim_text} The report also describes this event in detail.",
                retriever_name=self.name,
            )
        ]


@pytest.mark.anyio
async def test_claims_share_one_atomic_budget_without_crashing() -> None:
    settings = Settings(
        ENVIRONMENT="testing",
        ENABLE_LIVE_SEARCH=False,
        VERIFICATION_CLAIM_CONCURRENCY=3,
        TOKEN_BUDGET_ANALYSIS_DEFAULT=35,
    )
    orchestrator = VerificationOrchestrator(
        retriever=FixedEvidence(), settings=settings
    )
    request = VerificationCreateRequest(
        text="Water is wet. Fire is hot. Ice is cold. Snow is white. Grass is green.",
        options=VerificationOptions(enable_kb_search=False),
    )
    response = await orchestrator.verify(request)
    assert response.total_claims == 5
    assert [claim.claim_index for claim in response.claims] == list(range(5))
    evaluations = [judge for claim in response.claims for judge in claim.judges]
    assert len(evaluations) == 10
    assert any(judge.judgment == "UNAVAILABLE" for judge in evaluations)
    assert any(
        "budget exhausted" in (judge.rationale or "").lower() for judge in evaluations
    )
