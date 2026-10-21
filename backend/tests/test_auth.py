"""Tests for API-key authentication, namespace isolation, and rate limiting."""

import uuid
from collections.abc import Generator

import pytest
from pydantic import SecretStr, ValidationError
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.modules.knowledge.service import clear_ephemeral_kb

ALICE_KEY = "alice-key-0123456789abcdef"
BOB_KEY = "bob-key-0123456789abcdef00"
ALICE = {"X-API-Key": ALICE_KEY}
BOB = {"X-API-Key": BOB_KEY}


def _client(**overrides: object) -> TestClient:
    settings = Settings(**{"ENVIRONMENT": "testing", **overrides})  # type: ignore[arg-type]
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


@pytest.fixture
def keyed_client() -> Generator[TestClient, None, None]:
    clear_ephemeral_kb()
    with _client(
        API_KEYS={"alice": SecretStr(ALICE_KEY), "bob": SecretStr(BOB_KEY)}
    ) as client:
        yield client
    clear_ephemeral_kb()


def _add_alice_doc(client: TestClient) -> str:
    response = client.post(
        "/api/v1/knowledge/documents",
        json={
            "title": "HR",
            "filename": "hr.txt",
            "text": "Alice salary is 250000 dollars per year at Acme Corp.",
        },
        headers=ALICE,
    )
    assert response.status_code == 201
    assert response.json()["owner_id"] == "alice"
    return str(response.json()["id"])


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/knowledge/documents"),
        ("post", "/api/v1/knowledge/search"),
        ("post", "/api/v1/verification"),
        ("post", "/api/v1/ingest"),
        ("get", f"/api/v1/verification/{uuid.uuid4()}"),
    ],
)
def test_missing_api_key_rejected(
    keyed_client: TestClient, method: str, path: str
) -> None:
    response = getattr(keyed_client, method)(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "ApiKey"


def test_invalid_api_key_rejected(keyed_client: TestClient) -> None:
    response = keyed_client.get(
        "/api/v1/knowledge/documents", headers={"X-API-Key": "x" * 32}
    )
    assert response.status_code == 401


def test_health_probes_stay_public(keyed_client: TestClient) -> None:
    assert keyed_client.get("/api/v1/health").status_code == 200


def test_owner_is_derived_from_key_not_request(keyed_client: TestClient) -> None:
    _add_alice_doc(keyed_client)
    bob_list = keyed_client.get("/api/v1/knowledge/documents", headers=BOB)
    assert bob_list.status_code == 200
    assert bob_list.json()["owner_id"] == "bob"
    assert bob_list.json()["total_documents"] == 0


def test_cross_namespace_owner_id_is_forbidden(keyed_client: TestClient) -> None:
    _add_alice_doc(keyed_client)
    listing = keyed_client.get(
        "/api/v1/knowledge/documents", params={"owner_id": "alice"}, headers=BOB
    )
    assert listing.status_code == 403
    search = keyed_client.post(
        "/api/v1/knowledge/search",
        json={"query": "Alice salary Acme Corp", "owner_id": "alice"},
        headers=BOB,
    )
    assert search.status_code == 403
    verify = keyed_client.post(
        "/api/v1/verification",
        json={"text": "Alice salary is 100 dollars.", "options": {"owner_id": "alice"}},
        headers=BOB,
    )
    assert verify.status_code == 403


def test_other_owner_cannot_read_or_delete_document(keyed_client: TestClient) -> None:
    doc_id = _add_alice_doc(keyed_client)
    path = f"/api/v1/knowledge/documents/{doc_id}"
    assert keyed_client.get(path, headers=BOB).status_code == 404
    assert keyed_client.delete(path, headers=BOB).status_code == 404
    assert keyed_client.get(path, headers=ALICE).status_code == 200


def test_kb_search_only_sees_own_namespace(keyed_client: TestClient) -> None:
    _add_alice_doc(keyed_client)
    bob = keyed_client.post(
        "/api/v1/knowledge/search",
        json={"query": "Alice salary Acme Corp"},
        headers=BOB,
    )
    assert bob.status_code == 200
    assert bob.json()["results"] == []
    alice = keyed_client.post(
        "/api/v1/knowledge/search",
        json={"query": "Alice salary Acme Corp"},
        headers=ALICE,
    )
    assert len(alice.json()["results"]) == 1


def test_verification_result_scoped_to_owner(keyed_client: TestClient) -> None:
    created = keyed_client.post(
        "/api/v1/verification",
        json={"text": "Water freezes at 0 degrees Celsius."},
        headers=ALICE,
    )
    assert created.status_code == 200
    path = f"/api/v1/verification/{created.json()['verification_id']}"
    assert keyed_client.get(path, headers=ALICE).status_code == 200
    assert keyed_client.get(path, headers=BOB).status_code == 404


def test_production_without_keys_rejects_requests() -> None:
    with _client(ENVIRONMENT="production") as client:
        assert client.get("/api/v1/health").status_code == 200
        response = client.get("/api/v1/knowledge/documents")
        assert response.status_code == 401


def test_debug_flag_does_not_enable_anonymous_production_access() -> None:
    with _client(ENVIRONMENT="production", DEBUG=True) as client:
        assert client.get("/api/v1/knowledge/documents").status_code == 401


def test_development_without_keys_allows_anonymous() -> None:
    with _client() as client:
        assert client.get("/api/v1/knowledge/documents").status_code == 200


def test_rate_limit_enforced_per_principal() -> None:
    clear_ephemeral_kb()
    with _client(
        API_KEYS={"alice": SecretStr(ALICE_KEY), "bob": SecretStr(BOB_KEY)},
        RATE_LIMIT_PER_MINUTE=2,
    ) as client:
        body = {"query": "anything at all"}
        for _ in range(2):
            ok = client.post("/api/v1/knowledge/search", json=body, headers=ALICE)
            assert ok.status_code == 200
        limited = client.post("/api/v1/knowledge/search", json=body, headers=ALICE)
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "TOO_MANY_REQUESTS"
        assert limited.headers["retry-after"] == "60"
        # Budgets are independent per principal.
        other = client.post("/api/v1/knowledge/search", json=body, headers=BOB)
        assert other.status_code == 200


@pytest.mark.parametrize(
    "keys",
    [
        {"alice": "short"},
        {"alice": ALICE_KEY, "bob": ALICE_KEY},
        {" ": ALICE_KEY},
    ],
)
def test_invalid_api_key_configuration_rejected(keys: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        Settings(API_KEYS=keys)  # type: ignore[arg-type]


def test_api_keys_not_exposed_in_settings_repr() -> None:
    settings = Settings(API_KEYS={"alice": ALICE_KEY})  # type: ignore[arg-type]
    assert ALICE_KEY not in repr(settings)
    assert ALICE_KEY not in str(settings.model_dump())
