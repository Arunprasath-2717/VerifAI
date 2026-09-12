import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_overview():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert "overall_trust_score" in data
    assert "total_verifications" in data
    assert "supported_claims" in data
    assert "contradicted_claims" in data
    assert "inconclusive_claims" in data
    assert "hallucination_rate" in data

def test_trust_score():
    response = client.get("/api/v1/dashboard/trust-score")
    assert response.status_code == 200
    data = response.json()
    assert "trust_score" in data
    assert data["source_of_truth"] == "core.verifications.trust_score"

def test_verification_stats():
    response = client.get("/api/v1/dashboard/verification-stats")
    assert response.status_code == 200
    data = response.json()
    assert "supported" in data
    assert "contradicted" in data
    assert "inconclusive" in data
    assert data["supported"]["count"] >= 0

def test_hallucination_rate():
    response = client.get("/api/v1/dashboard/hallucination-rate")
    assert response.status_code == 200
    data = response.json()
    assert "hallucination_rate" in data
    assert "contradiction_rate" in data

def test_confidence():
    response = client.get("/api/v1/dashboard/confidence")
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert "no_verification_signal_count" in data

def test_signal_quality():
    response = client.get("/api/v1/dashboard/signal-quality")
    assert response.status_code == 200
    data = response.json()
    assert "breakdown" in data
    assert "failed_judgment" in data["breakdown"]

def test_evidence_quality():
    response = client.get("/api/v1/dashboard/evidence-quality")
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert "UNKNOWN" in data["distribution"]

def test_trends():
    response = client.get("/api/v1/dashboard/trends")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data

def test_domains():
    response = client.get("/api/v1/dashboard/domains")
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data

def test_models():
    response = client.get("/api/v1/dashboard/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data

def test_filters():
    response = client.get("/api/v1/dashboard/filters")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "domains" in data

def test_combined_filters():
    response = client.get("/api/v1/dashboard/overview?domain=Healthcare&verdict=SUPPORTED")
    assert response.status_code == 200
    data = response.json()
    assert "total_verifications" in data
