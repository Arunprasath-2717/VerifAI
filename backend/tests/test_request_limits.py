"""Tests for request-body size limits and the in-memory KB storage quota."""

from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.modules.knowledge.service import clear_ephemeral_kb


def _client(**overrides: object) -> TestClient:
    settings = Settings(**{"ENVIRONMENT": "testing", **overrides})  # type: ignore[arg-type]
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_declared_oversized_body_rejected_with_413() -> None:
    with _client(MAX_REQUEST_BODY_BYTES=100) as client:
        response = client.post(
            "/api/v1/verification", json={"text": "Water is wet. " * 50}
        )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert "x-request-id" in response.headers


def test_streamed_oversized_body_rejected_with_413() -> None:
    def chunks() -> Iterator[bytes]:
        yield b'{"text": "'
        for _ in range(20):
            yield b"x" * 50
        yield b'"}'

    with _client(MAX_REQUEST_BODY_BYTES=200) as client:
        response = client.post(
            "/api/v1/verification",
            content=chunks(),
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 413


def test_body_within_limit_accepted() -> None:
    with _client(MAX_REQUEST_BODY_BYTES=10_000) as client:
        response = client.post("/api/v1/verification", json={"text": "Water is wet."})
    assert response.status_code == 200


def test_persistent_owner_kb_quota_enforced() -> None:
    clear_ephemeral_kb()
    try:
        with _client(KB_MAX_OWNER_BYTES=120) as client:
            first = client.post(
                "/api/v1/knowledge/documents",
                json={"title": "a", "text": "alpha " * 15},
            )
            assert first.status_code == 201
            second = client.post(
                "/api/v1/knowledge/documents",
                json={"title": "b", "text": "beta " * 15},
            )
        assert second.status_code == 507
        assert second.json()["error"]["code"] == "STORAGE_QUOTA_EXCEEDED"
    finally:
        clear_ephemeral_kb()


@pytest.mark.parametrize("size", [0])
def test_zero_disables_body_limit(size: int) -> None:
    with _client(MAX_REQUEST_BODY_BYTES=size) as client:
        response = client.post(
            "/api/v1/verification", json={"text": "Water is wet. " * 50}
        )
    assert response.status_code == 200
