"""Tests for health and readiness probes with strict contract verification."""

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings


def test_versioned_health_check(client: TestClient) -> None:
    """Verify liveness probe confirms process is running and includes request ID."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["status"] == "live"
    assert data["service"] == "verifai-backend"
    assert "version" in data
    assert "request_id" in data
    assert data["request_id"] == response.headers["x-request-id"]


def test_readiness_probe_returns_503_when_unready(
    app: FastAPI, client: TestClient
) -> None:
    """Verify readiness probe returns 503 and request ID when unconfigured."""
    unconfigured_settings = Settings(
        _env_file=None,
        DATABASE_URL=None,
        ENVIRONMENT="testing",
        FIREBASE_AUTH_ENABLED=False,
    )
    app.dependency_overrides[get_settings] = lambda: unconfigured_settings
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["ready"] is False
    assert data["process"] == "running"
    assert data["environment"] == "testing"
    assert "request_id" in data
    assert data["request_id"] == response.headers["x-request-id"]
    assert "dependencies" in data
    assert data["dependencies"]["database"]["configured"] is False
    assert data["dependencies"]["database"]["status"] == "unconfigured"
    assert data["dependencies"]["storage"]["configured"] is False
    assert data["dependencies"]["storage"]["status"] == "unconfigured"
    assert data["dependencies"]["auth"]["configured"] is True
    assert data["dependencies"]["auth"]["status"] == "available"
    # Ensure no passwords or sensitive URLs leaked in response
    assert "password" not in str(data)
    assert "postgresql://" not in str(data)


def test_readiness_probe_database_unavailable_mocked(client: TestClient) -> None:
    """Verify readiness probe returns 503 when database connectivity fails (mocked)."""
    mock_db_result = {"configured": True, "status": "unavailable"}
    with patch(
        "app.api.v1.endpoints.health.check_database_connectivity",
        new=AsyncMock(return_value=mock_db_result),
    ):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        assert "x-request-id" in response.headers
        data = response.json()
        assert data["ready"] is False
        assert data["request_id"] == response.headers["x-request-id"]
        assert data["dependencies"]["database"] == {
            "configured": True,
            "status": "unavailable",
        }


def test_readiness_probe_database_available_mocked(client: TestClient) -> None:
    """A configured JWT service and responsive DB can actually become ready."""
    mock_db_result = {"configured": True, "status": "available"}
    with patch(
        "app.api.v1.endpoints.health.check_database_connectivity",
        new=AsyncMock(return_value=mock_db_result),
    ):
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["dependencies"]["database"] == mock_db_result
    assert data["dependencies"]["storage"] == {
        "configured": True,
        "status": "available",
        "backend": "database",
    }
    assert data["dependencies"]["auth"] == {
        "configured": True,
        "status": "available",
        "check": "configuration_only",
    }


def test_readiness_fails_closed_when_jwt_missing(
    app: FastAPI, client: TestClient
) -> None:
    unconfigured_auth = Settings(
        _env_file=None,
        ENVIRONMENT="testing",
        JWT_SECRET="",
        FIREBASE_AUTH_ENABLED=False,
    )
    app.dependency_overrides[get_settings] = lambda: unconfigured_auth
    with patch(
        "app.api.v1.endpoints.health.check_database_connectivity",
        new=AsyncMock(return_value={"configured": True, "status": "available"}),
    ):
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["dependencies"]["auth"]["status"] == "unconfigured"


def test_readiness_fails_when_firebase_enabled_without_project(
    app: FastAPI, client: TestClient
) -> None:
    incomplete_auth = Settings(
        _env_file=None,
        ENVIRONMENT="testing",
        FIREBASE_AUTH_ENABLED=True,
        FIREBASE_PROJECT_ID="",
    )
    app.dependency_overrides[get_settings] = lambda: incomplete_auth
    with patch(
        "app.api.v1.endpoints.health.check_database_connectivity",
        new=AsyncMock(return_value={"configured": True, "status": "available"}),
    ):
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["dependencies"]["auth"]["status"] == "unconfigured"


def test_unversioned_root_health_not_mounted_negative_control(
    client: TestClient,
) -> None:
    """Negative control: Verify unversioned /health is not mounted."""
    response = client.get("/health")
    assert response.status_code == 404


def test_health_post_method_not_allowed_negative_control(
    client: TestClient,
) -> None:
    """Negative control: Verify POST on /api/v1/health returns 405."""
    response = client.post("/api/v1/health")
    assert response.status_code == 405


def test_ready_post_method_not_allowed_negative_control(
    client: TestClient,
) -> None:
    """Negative control: Verify POST on /api/v1/ready returns 405."""
    response = client.post("/api/v1/ready")
    assert response.status_code == 405


def test_nonexistent_route_404_negative_control(client: TestClient) -> None:
    """Negative control: Verify request to nonexistent route returns 404."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404
