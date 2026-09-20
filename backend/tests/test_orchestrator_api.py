"""Integration tests for VerificationOrchestrator and Verification API endpoints."""

import uuid

import pytest
from starlette.testclient import TestClient

from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    ContentType,
    VerdictType,
    VerificationCreateRequest,
)


@pytest.mark.anyio
async def test_orchestrator_factual_supported_claim() -> None:
    """Verify end-to-end verification of a verified factual claim."""
    orchestrator = VerificationOrchestrator()
    request = VerificationCreateRequest(
        text="Water has the chemical formula H2O.",
    )
    response = await orchestrator.verify(request=request)

    assert response.status == "COMPLETED"
    assert response.total_claims == 1
    assert response.supported_claims == 1
    assert response.contradicted_claims == 0
    assert response.trust_score == 100.0
    assert response.is_calibrated is False
    assert response.calibration_status == "NOT_CALIBRATED"
    assert len(response.claims) == 1
    c = response.claims[0]
    assert c.verdict == VerdictType.SUPPORTED
    assert len(c.evidence) >= 1
    assert len(c.judges) >= 1
    assert len(response.audit_trail) >= 3


@pytest.mark.anyio
async def test_orchestrator_factual_contradicted_claim() -> None:
    """Verify end-to-end verification of a contradictory claim."""
    orchestrator = VerificationOrchestrator()
    request = VerificationCreateRequest(
        text="Apollo 11 landed on the Moon in 1975.",
    )
    response = await orchestrator.verify(request=request)

    assert response.status == "COMPLETED"
    assert response.total_claims == 1
    assert response.contradicted_claims == 1
    assert response.supported_claims == 0
    assert response.trust_score == 0.0
    assert response.claims[0].verdict == VerdictType.CONTRADICTED


@pytest.mark.anyio
async def test_orchestrator_subjective_opinion() -> None:
    """Verify opinion inputs are routed to VIEWPOINT with exempt trust score."""
    orchestrator = VerificationOrchestrator()
    request = VerificationCreateRequest(
        text="In my opinion, chocolate ice cream is the best dessert.",
    )
    response = await orchestrator.verify(request=request)

    assert response.status == "COMPLETED"
    assert response.total_claims == 1
    assert response.non_factual_claims == 1
    assert response.trust_score is None
    assert response.claims[0].content_type == ContentType.OPINION
    assert response.claims[0].verdict == VerdictType.VIEWPOINT


@pytest.mark.anyio
async def test_orchestrator_multi_claim_processing() -> None:
    """Verify decomposition and individual evaluation of multiple claims."""
    orchestrator = VerificationOrchestrator()
    text = (
        "Water has the chemical formula H2O. "
        "Apollo 11 landed on the Moon in 1975. "
        "In my opinion, science is fascinating."
    )
    request = VerificationCreateRequest(text=text)
    response = await orchestrator.verify(request=request)

    assert response.status == "COMPLETED"
    assert response.total_claims == 3
    assert response.supported_claims == 1
    assert response.contradicted_claims == 1
    assert response.non_factual_claims == 1
    # Contradiction triggers hallucination risk penalty: 0.0%
    assert response.trust_score == 0.0


def test_api_create_verification_success(client: TestClient) -> None:
    """Verify POST /api/v1/verification successfully verifies text."""
    payload = {
        "text": "Water has the chemical formula H2O.",
    }
    res = client.post("/api/v1/verification", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "verification_id" in data
    assert data["total_claims"] == 1
    assert data["supported_claims"] == 1
    assert data["trust_score"] == 100.0
    assert len(data["claims"]) == 1
    assert data["claims"][0]["verdict"] == "SUPPORTED"
    assert len(data["audit_trail"]) > 0


def test_api_create_verification_empty_text(client: TestClient) -> None:
    """Verify POST /api/v1/verification rejects empty text with 422."""
    payload = {"text": ""}
    res = client.post("/api/v1/verification", json=payload)
    assert res.status_code == 422


def test_api_create_verification_whitespace_text(client: TestClient) -> None:
    """Verify POST /api/v1/verification rejects whitespace-only text with 422."""
    payload = {"text": "    \n\t  "}
    res = client.post("/api/v1/verification", json=payload)
    assert res.status_code == 422


def test_api_create_verification_exceeds_max_chars(client: TestClient) -> None:
    """Verify POST /api/v1/verification rejects text exceeding 20,000 characters."""
    payload = {"text": "A" * 20001}
    res = client.post("/api/v1/verification", json=payload)
    assert res.status_code == 422


def test_api_get_verification_not_found(client: TestClient) -> None:
    """Verify GET /api/v1/verification/{id} returns 404 for unknown job ID."""
    random_id = uuid.uuid4()
    res = client.get(f"/api/v1/verification/{random_id}")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_api_get_verification_invalid_uuid(client: TestClient) -> None:
    """Verify GET /api/v1/verification/{id} returns 422 for non-UUID string."""
    res = client.get("/api/v1/verification/not-a-uuid")
    assert res.status_code == 422
