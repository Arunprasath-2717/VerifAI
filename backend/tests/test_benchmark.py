import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_benchmarks():
    response = client.get("/api/v1/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) > 0

def test_benchmark_metrics():
    response = client.get("/api/v1/benchmark/bm-factuality-v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "claim_level" in data
    assert "system_level" in data
    assert "calibration" in data
    assert "operational" in data
    assert "sampling_basis" in data
    assert data["sampling_basis"] in ["prompt_generation", "response_rewrite"]

def test_benchmark_models():
    response = client.get("/api/v1/benchmark/bm-factuality-v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0

def test_benchmark_claims():
    response = client.get("/api/v1/benchmark/bm-factuality-v1/claims")
    assert response.status_code == 200
    data = response.json()
    assert "claims" in data
    assert len(data["claims"]) > 0

def test_compare_benchmarks():
    response = client.get("/api/v1/benchmark/compare?benchmark_ids=bm-factuality-v1,bm-hallucination-v2")
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data
    assert len(data["comparison"]) >= 1
