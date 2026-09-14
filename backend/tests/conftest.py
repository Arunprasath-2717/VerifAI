"""Shared test fixtures for the VerifAI backend."""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.database import database_manager
from app.core.metrics import metrics_collector
from app.factory import create_app


@pytest.fixture(autouse=True)
def reset_metrics_state():
    """Ensure clean metrics before each test run."""
    metrics_collector.reset()
    yield
    metrics_collector.reset()


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing testing settings."""
    return Settings(
        APP_NAME="VerifAI API (Test)",
        APP_VERSION="0.1.0-test",
        ENVIRONMENT="testing",
        DEBUG=False,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS=["http://localhost:3000", "http://testserver"],
        DATABASE_URL="postgresql://test:test@localhost:5432/test_verifai",
    )


@pytest.fixture
def app(test_settings: Settings):
    """FastAPI application instance for testing."""
    return create_app(test_settings)


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client bound to the FastAPI test application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
def mock_db_connected(monkeypatch):
    """Mock database check_health to return connected status."""
    async def mock_check_health(timeout: float = 2.0):
        return True, "connected", 1.5

    monkeypatch.setattr(database_manager, "check_health", mock_check_health)
    monkeypatch.setattr(database_manager, "_is_connected", True)
    return mock_check_health


@pytest.fixture
def mock_db_disconnected(monkeypatch):
    """Mock database check_health to return disconnected status."""
    async def mock_check_health(timeout: float = 2.0):
        return False, "disconnected", 0.0

    monkeypatch.setattr(database_manager, "check_health", mock_check_health)
    monkeypatch.setattr(database_manager, "_is_connected", False)
    return mock_check_health
