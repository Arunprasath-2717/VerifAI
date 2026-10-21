"""Regression tests: endpoint errors must propagate through the DB session dependency.

Previously the optional session dependency wrapped ``yield`` in ``try/except``,
so any exception raised by an endpoint while a database was configured was
swallowed and re-raised as ``RuntimeError("generator didn't stop")`` -> HTTP 500.
"""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def db_client() -> Generator[tuple[TestClient, AsyncMock], None, None]:
    settings = Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        DATABASE_URL=SecretStr("postgresql+asyncpg://u:p@db.invalid:5432/verifai"),
    )
    session = AsyncMock()
    empty_result = MagicMock()
    empty_result.scalar_one_or_none.return_value = None
    empty_result.scalars.return_value.first.return_value = None
    session.execute.return_value = empty_result

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    maker = MagicMock(return_value=session_cm)

    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with (
        patch("app.core.dependencies.get_async_session_maker", return_value=maker),
        TestClient(app) as client,
    ):
        yield client, session


def test_missing_verification_returns_404_with_db(db_client) -> None:
    client, _ = db_client
    response = client.get(f"/api/v1/verification/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_missing_ingestion_returns_404_with_db(db_client) -> None:
    client, _ = db_client
    response = client.get(f"/api/v1/ingest/{uuid.uuid4()}")
    assert response.status_code == 404


def test_missing_kb_document_returns_404_with_db(db_client) -> None:
    client, _ = db_client
    response = client.get(f"/api/v1/knowledge/documents/{uuid.uuid4()}")
    assert response.status_code == 404


def test_validation_error_returns_422_with_db(db_client) -> None:
    client, _ = db_client
    response = client.post("/api/v1/knowledge/documents", json={"text": "x"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
