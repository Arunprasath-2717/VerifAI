"""Tests for application factory and lifespan management."""

import pytest
from app.core.config import Settings
from app.factory import create_app, lifespan


def test_create_app_structure():
    """Verify application factory sets up required routes and documentation."""
    settings = Settings(ENVIRONMENT="testing", DEBUG=False)
    app = create_app(settings)

    assert app.title == "VerifAI API"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"

    # Verify registered routes via OpenAPI specification
    paths = list(app.openapi()["paths"].keys())
    assert "/health" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/ready" in paths
    assert "/api/v1/metrics" in paths
    assert "/api/v1/test-validation" in paths

    # Verify create_app() with default None settings
    default_app = create_app()
    assert default_app is not None


@pytest.mark.asyncio
async def test_lifespan_lifecycle():
    """Verify startup and shutdown hooks execute cleanly in lifespan."""
    settings = Settings(ENVIRONMENT="testing", DEBUG=False)
    app = create_app(settings)

    # Execute lifespan context manager
    async with lifespan(app):
        # Startup completed
        assert hasattr(app.state, "settings")
    # Shutdown completed without raising exceptions


def test_main_asgi_entrypoint():
    """Verify app.main instantiates the ASGI application instance."""
    from app.main import app as asgi_app

    assert asgi_app is not None
    assert asgi_app.title == "VerifAI API"

