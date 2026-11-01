"""Bearer JWT authentication, ownership enforcement, and development isolation.

Bearer JWT is the sole user identity mechanism. There is no API-key path.
"""

import asyncio
import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from pydantic import SecretStr
from sqlalchemy import update
from starlette.testclient import TestClient

from app.core.config import INSECURE_DEV_JWT_SECRET, Settings, get_settings
from app.core.database import get_async_session_maker
from app.core.security import clear_ephemeral_users
from app.main import create_app
from app.models.user import User
from app.modules.knowledge.service import clear_ephemeral_kb

# Test-only secret. Production settings reject the insecure default, so every
# production-mode test supplies this explicit non-default value (32+ chars).
TEST_JWT_SECRET = "test-only-jwt-secret-0123456789abcdef0123456789abcdef"
PASSWORD = "Password123!"
PROTECTED_READ = "/api/v1/knowledge/documents"


def _client(**overrides: Any) -> TestClient:
    values: dict[str, Any] = {"ENVIRONMENT": "testing", **overrides}
    if values.get("ENVIRONMENT") in ("production", "staging"):
        values.setdefault("JWT_SECRET", SecretStr(TEST_JWT_SECRET))
    settings = Settings(**values)
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(
    client: TestClient, email: str, username: str
) -> tuple[str, str]:
    """Register and log in through the real endpoints. Returns (token, user_id)."""
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
    return login.json()["access_token"], reg.json()["id"]


def _set_user_column(user_id: str, **values: Any) -> None:
    async def _update() -> None:
        maker = get_async_session_maker()
        async with maker() as session:
            await session.execute(
                update(User).where(User.id == uuid.UUID(user_id)).values(**values)
            )
            await session.commit()

    asyncio.run(_update())


def _forge(claims: dict[str, Any], secret: str | None = None) -> str:
    """Sign claims with the secret the default test app is configured with."""
    key = secret or get_settings().JWT_SECRET.get_secret_value()
    return jwt.encode(claims, key, algorithm="HS256")


def _claims(subject: str | None = None, **overrides: Any) -> dict[str, Any]:
    settings = get_settings()
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject or str(uuid.uuid4()),
        "role": "USER",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    claims.update(overrides)
    return claims


@pytest.fixture(autouse=True)
def _reset_state() -> Generator[None, None, None]:
    clear_ephemeral_kb()
    clear_ephemeral_users()
    yield
    clear_ephemeral_kb()
    clear_ephemeral_users()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with _client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Bearer token validation matrix on a protected user-data route
# ---------------------------------------------------------------------------


def test_missing_bearer_rejected_in_production() -> None:
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_malformed_bearer_rejected() -> None:
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ, headers=_bearer("not-a-jwt"))
        assert response.status_code == 401
        assert response.json()["error"]["details"]["reason"] == "unparseable_header"


def test_expired_token_rejected() -> None:
    past = int((datetime.now(UTC) - timedelta(minutes=1)).timestamp())
    token = _forge(_claims(exp=past), secret=TEST_JWT_SECRET)
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ, headers=_bearer(token))
        assert response.status_code == 401
        assert response.json()["error"]["details"]["reason"] == "token_expired"


def test_invalid_signature_rejected() -> None:
    token = _forge(_claims(), secret="attacker-controlled-secret-0123456789abcdef")
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ, headers=_bearer(token))
        assert response.status_code == 401
        assert response.json()["error"]["details"]["reason"] == "invalid_token"


def test_alg_none_token_rejected() -> None:
    token = jwt.encode(_claims(), key="", algorithm="none")
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ, headers=_bearer(token))
        assert response.status_code == 401


def test_wrong_audience_rejected() -> None:
    token = _forge(_claims(aud="some-other-service"), secret=TEST_JWT_SECRET)
    with _client(ENVIRONMENT="production") as client:
        response = client.get(PROTECTED_READ, headers=_bearer(token))
        assert response.status_code == 401
        assert response.json()["error"]["details"]["reason"] == "invalid_token"


def test_valid_signature_for_unknown_user_rejected(client: TestClient) -> None:
    response = client.get(PROTECTED_READ, headers=_bearer(_forge(_claims())))
    assert response.status_code == 401
    assert "does not exist" in response.json()["error"]["message"].lower()


def test_valid_token_for_registered_user_accepted(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "valid@test.com", "valid_user")
    response = client.get(PROTECTED_READ, headers=_bearer(token))
    assert response.status_code == 200
    assert response.json()["owner_id"] == user_id


def test_deactivated_user_token_rejected(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "gone@test.com", "gone_user")
    _set_user_column(user_id, is_active=False)
    response = client.get(PROTECTED_READ, headers=_bearer(token))
    assert response.status_code == 401
    assert "deactivated" in response.json()["error"]["message"].lower()


# ---------------------------------------------------------------------------
# Production gating: anonymous access and DEBUG never bypass authentication
# ---------------------------------------------------------------------------


def test_production_without_token_rejects_knowledge_read() -> None:
    with _client(ENVIRONMENT="production") as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get(PROTECTED_READ).status_code == 401


def test_production_anonymous_verification_read_is_rejected() -> None:
    """Regression: a job UUID alone must not grant read access in production."""
    with _client(ENVIRONMENT="production") as client:
        response = client.get(f"/api/v1/verification/{uuid.uuid4()}")
        assert response.status_code == 401


def test_production_anonymous_verification_create_is_rejected() -> None:
    with _client(ENVIRONMENT="production") as client:
        response = client.post(
            "/api/v1/verification", json={"text": "Water freezes at 0 degrees Celsius."}
        )
        assert response.status_code == 401


def test_debug_true_is_rejected_in_production_settings() -> None:
    """DEBUG cannot be enabled in production, so it cannot unlock anonymous access."""
    with pytest.raises(ValueError, match="DEBUG mode cannot be enabled"):
        Settings(
            ENVIRONMENT="production", DEBUG=True, JWT_SECRET=SecretStr(TEST_JWT_SECRET)
        )


def test_production_rejects_insecure_default_jwt_secret() -> None:
    with pytest.raises(ValueError, match="strictly forbidden"):
        Settings(
            ENVIRONMENT="production", JWT_SECRET=SecretStr(INSECURE_DEV_JWT_SECRET)
        )


def test_debug_does_not_widen_knowledge_owner_resolution() -> None:
    """Production owner resolution must refuse anonymous callers even with DEBUG set.

    DEBUG cannot be combined with production, so this exercises the resolver
    directly on a non-development settings object with DEBUG forced on.
    """
    from app.modules.knowledge.service import resolve_owner_id

    prod = Settings(ENVIRONMENT="production", JWT_SECRET=SecretStr(TEST_JWT_SECRET))
    prod_debug = prod.model_copy(update={"DEBUG": True})
    with pytest.raises(ValueError, match="strictly required in production"):
        resolve_owner_id(None, prod_debug)


# ---------------------------------------------------------------------------
# Development isolation: anonymous callers never reach a real user's job
# ---------------------------------------------------------------------------


def test_development_anonymous_verification_uses_default_namespace(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/verification", json={"text": "Water freezes at 0 degrees Celsius."}
    )
    assert response.status_code == 200
    assert response.json()["owner_id"] == get_settings().DEFAULT_OWNER_ID


def test_development_anonymous_cannot_read_authenticated_users_job(
    client: TestClient,
) -> None:
    token, _ = _register_and_login(client, "dev_owner@test.com", "dev_owner")
    created = client.post(
        "/api/v1/verification",
        headers=_bearer(token),
        json={"text": "Water freezes at 0 degrees Celsius."},
    )
    assert created.status_code == 200
    job_id = created.json()["verification_id"]
    assert client.get(f"/api/v1/verification/{job_id}").status_code == 403


# ---------------------------------------------------------------------------
# Authorization boundaries with valid JWTs
# ---------------------------------------------------------------------------


def test_user_cannot_read_another_users_verification(client: TestClient) -> None:
    token_a, _ = _register_and_login(client, "alice_v@test.com", "alice_v")
    token_b, _ = _register_and_login(client, "bob_v@test.com", "bob_v")
    created = client.post(
        "/api/v1/verification",
        headers=_bearer(token_b),
        json={"text": "Water freezes at 0 degrees Celsius."},
    )
    assert created.status_code == 200
    job_path = f"/api/v1/verification/{created.json()['verification_id']}"
    assert client.get(job_path, headers=_bearer(token_b)).status_code == 200
    assert client.get(job_path, headers=_bearer(token_a)).status_code == 403


def test_user_cannot_create_verification_in_another_namespace(
    client: TestClient,
) -> None:
    token_a, _ = _register_and_login(client, "alice_ns@test.com", "alice_ns")
    _, id_b = _register_and_login(client, "bob_ns@test.com", "bob_ns")
    response = client.post(
        "/api/v1/verification",
        headers=_bearer(token_a),
        json={"text": "The Earth orbits the Sun.", "options": {"owner_id": id_b}},
    )
    assert response.status_code == 403
    assert "another user namespace" in response.json()["error"]["message"].lower()


def test_user_cannot_read_or_delete_another_users_document(client: TestClient) -> None:
    token_a, _ = _register_and_login(client, "alice_doc@test.com", "alice_doc")
    token_b, _ = _register_and_login(client, "bob_doc@test.com", "bob_doc")
    created = client.post(
        "/api/v1/knowledge/documents",
        headers=_bearer(token_a),
        json={
            "title": "HR",
            "filename": "hr.txt",
            "text": "Alice salary is 250000 dollars per year at Acme Corp.",
        },
    )
    assert created.status_code == 201
    path = f"/api/v1/knowledge/documents/{created.json()['id']}"
    assert client.get(path, headers=_bearer(token_b)).status_code == 404
    assert client.delete(path, headers=_bearer(token_b)).status_code == 404
    assert client.get(path, headers=_bearer(token_a)).status_code == 200


def test_user_cannot_list_another_users_documents_via_owner_param(
    client: TestClient,
) -> None:
    token_a, id_a = _register_and_login(client, "alice_list@test.com", "alice_list")
    token_b, _ = _register_and_login(client, "bob_list@test.com", "bob_list")
    listing = client.get(
        PROTECTED_READ, params={"owner_id": id_a}, headers=_bearer(token_b)
    )
    assert listing.status_code == 403


def test_random_job_uuid_returns_404_for_authenticated_user(client: TestClient) -> None:
    token, _ = _register_and_login(client, "probe@test.com", "probe_user")
    response = client.get(
        f"/api/v1/verification/{uuid.uuid4()}", headers=_bearer(token)
    )
    assert response.status_code == 404


def test_admin_can_inspect_another_users_verification(client: TestClient) -> None:
    owner_token, _ = _register_and_login(client, "owner_admin@test.com", "owner_admin")
    admin_token, admin_id = _register_and_login(client, "admin_u@test.com", "admin_u")
    _set_user_column(admin_id, role="ADMIN")
    created = client.post(
        "/api/v1/verification",
        headers=_bearer(owner_token),
        json={"text": "Water freezes at 0 degrees Celsius."},
    )
    job_id = created.json()["verification_id"]
    response = client.get(
        f"/api/v1/verification/{job_id}", headers=_bearer(admin_token)
    )
    assert response.status_code == 200
