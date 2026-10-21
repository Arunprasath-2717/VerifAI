"""Test configuration and fixtures for VerifAI backend."""

import os

# Parametrized matrices send hundreds of requests through one app instance;
# rate limiting is disabled suite-wide and covered by dedicated tests instead.
# Set before importing the app so the module-level settings pick it up.
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from app.core.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated test settings."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        PROJECT_NAME="VerifAI Backend Test",
        API_V1_STR="/api/v1",
    )


@pytest.fixture
def app(test_settings: Settings) -> Generator[FastAPI, None, None]:
    """Fixture providing a fresh FastAPI application instance with test settings."""
    application = create_app(settings=test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Fixture providing a synchronous TestClient for hermetic API testing."""
    with TestClient(app) as test_client:
        yield test_client
