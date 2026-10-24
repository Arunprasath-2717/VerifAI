"""Test configuration and fixtures for VerifAI backend."""

import os
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from sqlalchemy.engine import make_url
from starlette.testclient import TestClient

# Override the application DB before importing app.main, which creates app at
# import time. Never fall through to a real development/production DB silently.
if os.environ.get("VERIFAI_TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["VERIFAI_TEST_DATABASE_URL"]

from app.core.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def _is_isolated_test_database(raw_url: str) -> bool:
    try:
        url = make_url(raw_url)
    except Exception:
        return False
    db_name = url.database or ""
    if url.get_backend_name() == "postgresql":
        return db_name.endswith("_test") or db_name.startswith("test_")
    if url.get_backend_name() == "sqlite":
        return db_name == ":memory:" or db_name.endswith("_test.sqlite")
    return False


def pytest_sessionstart(session: pytest.Session) -> None:
    """Refuse to run integration tests against an actual application database."""
    if session.config.option.collectonly:
        return
    configured = get_settings().DATABASE_URL
    if configured and not _is_isolated_test_database(configured.get_secret_value()):
        raise pytest.UsageError(
            "Refusing to run backend tests with a non-test DATABASE_URL. "
            "Use VERIFAI_TEST_DATABASE_URL pointing to an isolated *_test "
            "PostgreSQL database (or run hermetic tests with a test-only SQLite URL)."
        )


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
