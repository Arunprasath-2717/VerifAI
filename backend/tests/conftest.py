"""Test configuration and fixtures for VerifAI backend."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


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


@pytest.fixture(autouse=True)
def _reset_token_budget_singletons() -> Generator[None, None, None]:
    """Isolate per-process analysis cache and daily quota state between tests."""
    from app.modules.token_budget import AnalysisCacheService, UserDailyBudgetTracker

    AnalysisCacheService.reset_for_test()
    UserDailyBudgetTracker.reset_for_test()
    yield
    AnalysisCacheService.reset_for_test()
    UserDailyBudgetTracker.reset_for_test()
