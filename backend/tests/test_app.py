"""Tests for FastAPI application startup, structure, and OpenAPI documentation."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_app_instantiation(test_settings: Settings) -> None:
    """Verify create_app instantiates a FastAPI instance with given settings."""
    application = create_app(settings=test_settings)
    assert isinstance(application, FastAPI)
    assert application.title == test_settings.PROJECT_NAME
    assert application.version == test_settings.VERSION


def test_openapi_schema_generation(client: TestClient) -> None:
    """Verify OpenAPI JSON schema exposes exclusively versioned /api/v1 routes."""
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    schema = openapi_response.json()
    assert "openapi" in schema
    assert schema["info"]["title"] == "VerifAI Backend Test"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/ready" in schema["paths"]
    # Verify unversioned routes are NOT present in OpenAPI
    assert "/health" not in schema["paths"]
    assert "/ready" not in schema["paths"]

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200


def test_cors_middleware_configured(client: TestClient) -> None:
    """Verify that CORS middleware headers are properly applied."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_wildcard_disallows_credentials_security() -> None:
    """Security verification: Wildcard CORS origin must not allow credentials."""
    wildcard_settings = Settings(
        ENVIRONMENT="testing",
        BACKEND_CORS_ORIGINS=["*"],
    )
    application = create_app(settings=wildcard_settings)
    with TestClient(application) as test_client:
        response = test_client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://external-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-credentials") is None
