"""Authentication and ownership enforcement for the ingestion API.

Both POST /api/v1/ingest and GET /api/v1/ingest/{id} require a Bearer JWT. Records
are owned by the authenticated caller, and legacy ownerless rows are quarantined
(visible to ADMIN only).
"""

import asyncio
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pydantic import SecretStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.ingestion import IngestedPayload
from app.models.user import User

PASSWORD = "Password123!"
TEST_JWT_SECRET = "test-only-jwt-secret-0123456789abcdef0123456789abcdef"
PAYLOAD: dict[str, Any] = {
    "text": "Paris is the capital of France.",
    "source": "CHROME_EXTENSION",
    "verify_immediately": False,
}


def _helper_session_maker() -> async_sessionmaker:
    """Session maker for direct DB writes in tests.

    Uses NullPool so each asyncio.run() gets its own connection. The app's shared
    engine is bound to the TestClient's event loop and cannot be reused here.
    """
    settings = get_settings()
    assert settings.DATABASE_URL is not None
    engine = create_async_engine(
        settings.DATABASE_URL.get_secret_value(), poolclass=NullPool
    )
    return async_sessionmaker(engine, expire_on_commit=False)


def _make_client(**overrides: Any) -> TestClient:
    values: dict[str, Any] = {"ENVIRONMENT": "testing", "DEBUG": True, **overrides}
    settings = Settings(**values)
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def _register_and_login(client: TestClient) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:10]
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner_{suffix}@test.com",
            "username": f"owner_{suffix}",
            "password": PASSWORD,
            "terms_accepted": True,
        },
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": f"owner_{suffix}", "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"], reg.json()["id"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _set_role(user_id: str, role: str) -> None:
    async def _update() -> None:
        async with _helper_session_maker()() as session:
            await session.execute(
                update(User).where(User.id == uuid.UUID(user_id)).values(role=role)
            )
            await session.commit()

    asyncio.run(_update())


def _insert_legacy_row() -> uuid.UUID:
    """Insert an ownerless row, mirroring pre-migration data (owner_id NULL)."""
    record_id = uuid.uuid4()

    async def _insert() -> None:
        async with _helper_session_maker()() as session:
            session.add(
                IngestedPayload(
                    id=record_id,
                    source="CHROME_EXTENSION",
                    captured_text="legacy capture",
                    status="RECEIVED",
                    owner_id=None,
                )
            )
            await session.commit()

    asyncio.run(_insert())
    return record_id


@pytest.fixture
def owner() -> Generator[tuple[TestClient, str, str], None, None]:
    client = _make_client()
    token, user_id = _register_and_login(client)
    with client:
        yield client, token, user_id


class TestAnonymousRejected:
    def test_anonymous_post_is_rejected(self) -> None:
        client = _make_client()
        response = client.post("/api/v1/ingest", json=PAYLOAD)
        assert response.status_code == 401

    def test_anonymous_get_is_rejected(self) -> None:
        client = _make_client()
        response = client.get(f"/api/v1/ingest/{uuid.uuid4()}")
        assert response.status_code == 401

    def test_anonymous_rejected_even_in_development(self) -> None:
        """Development isolation: anonymous ingestion is never allowed, even locally."""
        client = _make_client(ENVIRONMENT="development", DEBUG=True)
        assert client.post("/api/v1/ingest", json=PAYLOAD).status_code == 401

    def test_malformed_bearer_is_rejected(self) -> None:
        client = _make_client()
        response = client.post(
            "/api/v1/ingest", json=PAYLOAD, headers=_bearer("not-a-jwt")
        )
        assert response.status_code == 401

    def test_forged_signature_is_rejected(self) -> None:
        client = _make_client()
        forged = create_access_token(
            subject=str(uuid.uuid4()),
            role="ADMIN",
            settings=Settings(ENVIRONMENT="testing", JWT_SECRET=SecretStr("x" * 40)),
        )[0]
        response = client.post("/api/v1/ingest", json=PAYLOAD, headers=_bearer(forged))
        assert response.status_code == 401


class TestOwnership:
    def test_owner_post_sets_owner_and_owner_can_read(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token, user_id = owner
        created = client.post("/api/v1/ingest", json=PAYLOAD, headers=_bearer(token))
        assert created.status_code == 201, created.text
        ingestion_id = created.json()["ingestion_id"]

        read = client.get(f"/api/v1/ingest/{ingestion_id}", headers=_bearer(token))
        assert read.status_code == 200
        assert read.json()["ingestion_id"] == ingestion_id

    def test_cross_user_read_is_rejected(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token_a, _ = owner
        created = client.post("/api/v1/ingest", json=PAYLOAD, headers=_bearer(token_a))
        ingestion_id = created.json()["ingestion_id"]

        token_b, _ = _register_and_login(client)
        response = client.get(
            f"/api/v1/ingest/{ingestion_id}", headers=_bearer(token_b)
        )
        assert response.status_code == 403
        assert "do not own" in response.json()["error"]["message"].lower()

    def test_spoofed_owner_id_in_verification_options_is_rejected(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token_a, _ = owner
        _, other_id = _register_and_login(client)
        payload = {**PAYLOAD, "options": {"owner_id": other_id}}
        response = client.post("/api/v1/ingest", json=payload, headers=_bearer(token_a))
        assert response.status_code == 403

    def test_quarantined_legacy_row_hidden_from_users(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token, _ = owner
        legacy_id = _insert_legacy_row()
        response = client.get(f"/api/v1/ingest/{legacy_id}", headers=_bearer(token))
        assert response.status_code == 403

    def test_quarantined_legacy_row_visible_to_admin_only(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token, user_id = owner
        legacy_id = _insert_legacy_row()
        _set_role(user_id, "ADMIN")
        # Role lives in the DB, so the already-issued token now resolves as ADMIN.
        response = client.get(f"/api/v1/ingest/{legacy_id}", headers=_bearer(token))
        assert response.status_code == 200
        _set_role(user_id, "USER")

    def test_unknown_ingestion_id_still_404_for_authenticated_user(
        self, owner: tuple[TestClient, str, str]
    ) -> None:
        client, token, _ = owner
        response = client.get(f"/api/v1/ingest/{uuid.uuid4()}", headers=_bearer(token))
        assert response.status_code == 404


class TestProductionMode:
    def test_debug_true_does_not_bypass_auth_in_production(self) -> None:
        """DEBUG=True must never open anonymous ingestion when is_development=False.

        Settings validation already refuses DEBUG=True in production. This test
        bypasses that validator on purpose (plain attribute assignment after
        construction) to prove the auth path does not depend on DEBUG at all.
        """
        settings = Settings(
            ENVIRONMENT="production",
            JWT_SECRET=SecretStr(TEST_JWT_SECRET),
        )
        settings.DEBUG = True
        assert settings.is_development is False
        app = create_app(settings=settings)
        app.dependency_overrides[get_settings] = lambda: settings
        client = TestClient(app)
        assert client.post("/api/v1/ingest", json=PAYLOAD).status_code == 401
        assert client.get(f"/api/v1/ingest/{uuid.uuid4()}").status_code == 401
