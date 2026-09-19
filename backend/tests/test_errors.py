"""Tests for API error handling and structured error responses."""

from collections.abc import Generator

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from app.core.errors import BadRequestError, NotFoundError, ServiceUnavailableError
from app.main import create_app


@pytest.fixture
def error_test_client() -> Generator[TestClient, None, None]:
    """Provide a TestClient instance with test routes to exercise error handlers."""
    app = create_app()

    @app.get("/test/app-error")
    def route_app_error() -> None:
        raise BadRequestError("Malformed query filter", details={"field": "filter"})

    @app.get("/test/not-found-error")
    def route_not_found_error() -> None:
        raise NotFoundError("Requested entity could not be found")

    @app.get("/test/service-unavailable")
    def route_service_unavailable() -> None:
        raise ServiceUnavailableError("Downstream service is offline")

    class TestPayload(BaseModel):
        name: str
        count: int
        secret_token: str

    @app.post("/test/validation")
    def route_validation(payload: TestPayload) -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/test/unhandled-crash")
    def route_unhandled_crash() -> None:
        raise RuntimeError(
            "Unexpected DB failure: postgresql+asyncpg://admin:superSecretPass@localhost:5432/db"
        )

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_app_error_handled_consistently(error_test_client: TestClient) -> None:
    """Verify AppError subclasses return consistent structured responses."""
    response = error_test_client.get("/test/app-error")
    assert response.status_code == 400
    assert "x-request-id" in response.headers
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BAD_REQUEST"
    assert data["error"]["message"] == "Malformed query filter"
    assert data["error"]["request_id"] == response.headers["x-request-id"]
    assert data["error"]["details"] == {"field": "filter"}


def test_not_found_error_subclass(error_test_client: TestClient) -> None:
    """Verify NotFoundError returns 404 with structured code NOT_FOUND."""
    response = error_test_client.get("/test/not-found-error")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Requested entity could not be found"
    assert data["error"]["request_id"] == response.headers["x-request-id"]


def test_service_unavailable_error_subclass(error_test_client: TestClient) -> None:
    """Verify ServiceUnavailableError returns 503 and SERVICE_UNAVAILABLE code."""
    response = error_test_client.get("/test/service-unavailable")
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert data["error"]["message"] == "Downstream service is offline"


def test_http_exception_handled_with_stable_codes(client: TestClient) -> None:
    """Verify standard HTTP exceptions (404, 405) produce structured JSON responses."""
    # 404 Not Found
    res_404 = client.get("/api/v1/nonexistent-route")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert data_404["error"]["code"] == "NOT_FOUND"
    assert data_404["error"]["message"] == "Not Found"
    assert data_404["error"]["request_id"] == res_404.headers["x-request-id"]

    # 405 Method Not Allowed
    res_405 = client.post("/api/v1/health")
    assert res_405.status_code == 405
    data_405 = res_405.json()
    assert data_405["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert data_405["error"]["request_id"] == res_405.headers["x-request-id"]


def test_validation_error_sanitization(error_test_client: TestClient) -> None:
    """Verify validation errors are structured and omit raw sensitive inputs."""
    payload = {
        "name": "valid_name",
        "count": "not_an_int",
        "secret_token": "secret_key_1234567890",
    }
    response = error_test_client.post("/test/validation", json=payload)
    assert response.status_code == 422
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    assert data["error"]["request_id"] == response.headers["x-request-id"]
    assert isinstance(data["error"]["details"], list)

    # Ensure sensitive inputs are not echoed back
    assert "secret_key_1234567890" not in str(data)


def test_unhandled_exception_returns_safe_500(error_test_client: TestClient) -> None:
    """Verify unexpected crashes return safe generic 500 without stack trace."""
    response = error_test_client.get("/test/unhandled-crash")
    assert response.status_code == 500
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected internal error occurred."
    assert data["error"]["request_id"] == response.headers["x-request-id"]
    assert data["error"]["details"] is None

    # Verify zero stack trace, exception class, or credentials in response
    assert "RuntimeError" not in str(data)
    assert "Traceback" not in str(data)
    assert "superSecretPass" not in str(data)
    assert "postgresql" not in str(data)
