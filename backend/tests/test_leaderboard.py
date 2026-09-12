import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_leaderboard():
    response = client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0
    assert data["models"][0]["rank"] == 1

def test_leaderboard_metrics():
    response = client.get("/api/v1/leaderboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    metric_ids = [m["id"] for m in data["metrics"]]
    assert "verification_accuracy" in metric_ids
    assert "hallucination_rate" in metric_ids

def test_compare_models():
    response = client.get("/api/v1/leaderboard/compare?models=gpt-4o,claude-3-5-sonnet")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2
    assert "comparison_matrix" in data

def test_model_detail():
    response = client.get("/api/v1/leaderboard/gpt-4o")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "gpt-4o"
    assert "accuracy" in data
    assert "hallucination_rate" in data

def test_model_detail_not_found():
    response = client.get("/api/v1/leaderboard/non-existent-model-xyz")
    assert response.status_code == 404
