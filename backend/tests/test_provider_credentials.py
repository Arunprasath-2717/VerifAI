"""BYOK provider credential tests: auth, encryption, ownership, and safe errors.

Runs against the isolated test database named by DATABASE_URL. Upstream
provider calls are replaced with an httpx MockTransport; no network is used.
"""

import uuid

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.main import create_app
from app.models.provider_credential import UserProviderCredential
from app.modules.providers import connection_validator as validator
from app.modules.providers.credential_crypto import decrypt_credential

PASSWORD = "StrongPassword2026!"
RAW_KEY = "sk-test-raw-secret-ABCDEFGH1234"


def _settings(key: str | None) -> Settings:
    base = get_settings()
    return base.model_copy(
        update={
            "PROVIDER_CREDENTIAL_ENCRYPTION_KEY": None if key is None else _secret(key),
        }
    )


def _secret(value: str):
    from pydantic import SecretStr

    return SecretStr(value)


@pytest.fixture
def enc_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def client(enc_key: str):
    settings = _settings(enc_key)
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client: TestClient, label: str) -> tuple[dict[str, str], str]:
    username = f"byok_{label}_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": PASSWORD,
            "terms_accepted": True,
        },
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": username, "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, reg.json()["id"]


def test_unauthenticated_requests_are_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/providers").status_code == 401
    assert (
        client.post(
            "/api/v1/providers/prov-openai/key", json={"apiKey": RAW_KEY}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/providers/prov-openai/test").status_code == 401
    assert client.delete("/api/v1/providers/prov-openai/key").status_code == 401


def test_save_returns_masked_key_and_never_raw(client: TestClient) -> None:
    headers, _ = _login(client, "save")
    resp = client.post(
        "/api/v1/providers/prov-openai/key", json={"apiKey": RAW_KEY}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "Connected"
    assert body["keyMasked"] != RAW_KEY
    assert RAW_KEY not in resp.text


def test_credential_persists_and_is_encrypted_at_rest(
    client: TestClient, enc_key: str
) -> None:
    headers, user_id = _login(client, "persist")
    client.post(
        "/api/v1/providers/prov-openai/key", json={"apiKey": RAW_KEY}, headers=headers
    )

    listed = client.get("/api/v1/providers", headers=headers).json()
    openai = next(p for p in listed if p["id"] == "prov-openai")
    assert openai["status"] == "Connected"
    assert RAW_KEY not in str(listed)

    # Read the stored row directly and confirm only ciphertext is persisted.
    import asyncio

    from app.core.database import get_async_session_maker

    async def _read_row() -> UserProviderCredential | None:
        maker = get_async_session_maker()
        async with maker() as session:
            res = await session.execute(
                select(UserProviderCredential).where(
                    UserProviderCredential.user_id == uuid.UUID(user_id),
                    UserProviderCredential.provider_id == "prov-openai",
                )
            )
            return res.scalar_one_or_none()

    row = asyncio.run(_read_row())
    assert row is not None
    assert RAW_KEY not in row.encrypted_api_key
    assert row.encrypted_api_key.startswith("gAAAA")  # Fernet token prefix
    assert decrypt_credential(_settings(enc_key), row.encrypted_api_key) == RAW_KEY


def test_missing_encryption_key_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(None)
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        headers, _ = _login(c, "nokey")
        resp = c.post(
            "/api/v1/providers/prov-openai/key",
            json={"apiKey": RAW_KEY},
            headers=headers,
        )
        assert resp.status_code == 503
        assert "PROVIDER_CREDENTIAL_ENCRYPTION_KEY" in resp.json()["error"]["message"]
        assert RAW_KEY not in resp.text
        # Nothing was written: the provider still reports Not Connected.
        listed = c.get("/api/v1/providers", headers=headers).json()
        assert (
            next(p for p in listed if p["id"] == "prov-openai")["status"]
            == "Not Connected"
        )
    app.dependency_overrides.clear()


def test_cross_user_access_is_isolated(client: TestClient) -> None:
    alice, _ = _login(client, "alice")
    bob, _ = _login(client, "bob")
    client.post(
        "/api/v1/providers/prov-groq/key", json={"apiKey": RAW_KEY}, headers=alice
    )

    # Bob sees only his own (empty) state.
    bob_view = client.get("/api/v1/providers", headers=bob).json()
    assert (
        next(p for p in bob_view if p["id"] == "prov-groq")["status"] == "Not Connected"
    )

    # Bob cannot test or delete Alice's credential: he has none, so these fail.
    assert (
        client.post("/api/v1/providers/prov-groq/test", headers=bob).status_code == 404
    )
    unlink = client.delete("/api/v1/providers/prov-groq/key", headers=bob)
    assert unlink.status_code == 200
    assert unlink.json()["unlinked"] is False

    # Alice's credential is untouched by Bob's delete attempt.
    alice_view = client.get("/api/v1/providers", headers=alice).json()
    assert (
        next(p for p in alice_view if p["id"] == "prov-groq")["status"] == "Connected"
    )


def test_unknown_provider_is_rejected(client: TestClient) -> None:
    headers, _ = _login(client, "unknown")
    assert (
        client.post(
            "/api/v1/providers/prov-evil/key", json={"apiKey": RAW_KEY}, headers=headers
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    ("upstream", "expected"),
    [
        (httpx.Response(200, json={"data": []}), validator.VALID),
        (
            httpx.Response(401, json={"error": f"bad key {RAW_KEY}"}),
            validator.INVALID_KEY,
        ),
        (httpx.Response(403, text="forbidden"), validator.INVALID_KEY),
        (httpx.Response(429, text="slow down"), validator.RATE_LIMITED),
        (httpx.Response(500, text=RAW_KEY), validator.UPSTREAM_ERROR),
    ],
)
def test_validator_classifies_upstream_status_without_leaking(
    upstream: httpx.Response, expected: str
) -> None:
    import asyncio

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization", "")
        return upstream

    result = asyncio.run(
        validator.validate_api_key(
            "prov-openai", RAW_KEY, transport=httpx.MockTransport(handler)
        )
    )
    assert result.status == expected
    assert seen["auth"] == f"Bearer {RAW_KEY}"  # key sent upstream only
    assert RAW_KEY not in result.message


def test_validator_timeout_and_transport_error_are_sanitized() -> None:
    import asyncio

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    def network_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"refused {RAW_KEY}", request=request)

    t = asyncio.run(
        validator.validate_api_key(
            "prov-openai", RAW_KEY, transport=httpx.MockTransport(timeout_handler)
        )
    )
    n = asyncio.run(
        validator.validate_api_key(
            "prov-openai", RAW_KEY, transport=httpx.MockTransport(network_handler)
        )
    )
    assert t.status == validator.TIMEOUT
    assert n.status == validator.UPSTREAM_ERROR
    assert RAW_KEY not in n.message


def test_unsupported_provider_has_no_live_check() -> None:
    import asyncio

    result = asyncio.run(validator.validate_api_key("prov-ollama", RAW_KEY))
    assert result.status == validator.UNSUPPORTED


def test_test_route_uses_stored_key_and_persists_status(
    client: TestClient, enc_key: str
) -> None:
    from app.api.v1.endpoints import providers as providers_module

    headers, _ = _login(client, "testroute")
    client.post(
        "/api/v1/providers/prov-openai/key", json={"apiKey": RAW_KEY}, headers=headers
    )

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"data": []})

    token = providers_module._CHECK_TRANSPORT.set(httpx.MockTransport(handler))
    try:
        resp = client.post("/api/v1/providers/prov-openai/test", headers=headers)
    finally:
        providers_module._CHECK_TRANSPORT.reset(token)

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["status"] == "VALID"
    assert seen["auth"] == f"Bearer {RAW_KEY}"
    assert RAW_KEY not in resp.text
