"""Firebase bearer identity isolation and consent registration regressions."""

import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

import app.api.v1.endpoints.auth as auth_endpoint
import app.core.security as core_security


def _mock_firebase(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    monkeypatch.setattr(
        auth_endpoint, "verify_firebase_id_token", lambda token, settings: payload
    )
    monkeypatch.setattr(
        core_security, "verify_firebase_id_token", lambda token, settings: payload
    )
    original = jwt.get_unverified_header
    monkeypatch.setattr(
        jwt,
        "get_unverified_header",
        lambda token: (
            {"alg": "RS256", "kid": "test"}
            if token == "firebase.test.token"
            else original(token)
        ),
    )


def _payload(subject: str, email: str) -> dict:
    return {
        "sub": subject,
        "email": email,
        "name": "Verified Firebase Test",
        "email_verified": True,
        "iss": "https://securetoken.google.com/verifai-test-project",
        "aud": "verifai-test-project",
        "firebase": {"sign_in_provider": "password"},
    }


def test_uuid_shaped_firebase_subject_is_not_internal_user_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    subject = str(uuid.uuid4())
    expected = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{subject}")
    _mock_firebase(monkeypatch, _payload(subject, f"{subject}@example.org"))
    header = {"Authorization": "Bearer firebase.test.token"}
    before = client.get("/api/v1/auth/me", headers=header)
    assert before.status_code == 401
    assert before.json()["error"]["details"]["reason"] == "firebase_enrollment_required"
    registered = client.post(
        "/api/v1/auth/firebase",
        json={"id_token": "firebase.test.token", "terms_accepted": True},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user_id"] == str(expected)
    after = client.get("/api/v1/auth/me", headers=header)
    assert after.status_code == 200
    assert after.json()["id"] == str(expected)


def test_firebase_email_collision_never_inherits_local_account(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = f"existing_{uuid.uuid4().hex}@example.org"
    local = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"existing_{uuid.uuid4().hex[:9]}",
            "password": "StrongPassword2026!",
            "terms_accepted": True,
        },
    )
    assert local.status_code == 201, local.text
    local_id = local.json()["id"]

    subject = "unrelated_" + uuid.uuid4().hex
    _mock_firebase(monkeypatch, _payload(subject, email))
    response = client.post(
        "/api/v1/auth/firebase",
        json={"id_token": "firebase.test.token", "terms_accepted": True},
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"]["reason"] == "firebase_email_conflict"
    assert "access_token" not in response.text

    local_login = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": email, "password": "StrongPassword2026!"},
    )
    assert local_login.status_code == 200
    assert local_login.json()["user_id"] == local_id


def test_raw_firebase_token_requires_current_consent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    subject = "policy_" + uuid.uuid4().hex
    _mock_firebase(monkeypatch, _payload(subject, f"{subject}@example.org"))
    enrolled = client.post(
        "/api/v1/auth/firebase",
        json={"id_token": "firebase.test.token", "terms_accepted": True},
    )
    assert enrolled.status_code == 200
    from app.core.config import get_settings

    settings = client.app.dependency_overrides[get_settings]()
    previous = settings.TERMS_VERSION
    try:
        settings.TERMS_VERSION = "next-version-requires-acceptance"
        refused = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer firebase.test.token"},
        )
        assert refused.status_code == 403
        assert refused.json()["error"]["details"]["reason"] == (
            "TERMS_REACCEPTANCE_REQUIRED"
        )
    finally:
        settings.TERMS_VERSION = previous


def test_failed_local_consent_write_rolls_back_registration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    from sqlalchemy import select

    from app.core.database import get_async_session_maker
    from app.models.user import User
    from app.repositories.user_consent import UserConsentRepository

    email = f"rollback_local_{uuid.uuid4().hex}@example.org"

    async def fail_consent(self, *args, **kwargs):  # noqa: ANN001
        raise RuntimeError("simulated consent storage failure")

    monkeypatch.setattr(UserConsentRepository, "record_consent", fail_consent)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"rollback_{uuid.uuid4().hex[:10]}",
            "password": "SafePassword2026!",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 500
    assert "access_token" not in response.text

    async def stored() -> bool:
        async with get_async_session_maker()() as session:
            return (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none() is not None

    assert asyncio.run(stored()) is False


def test_failed_firebase_consent_write_rolls_back_registration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    from sqlalchemy import select

    from app.core.database import get_async_session_maker
    from app.models.user import User
    from app.repositories.user_consent import UserConsentRepository

    subject = "rollback_fb_" + uuid.uuid4().hex
    _mock_firebase(monkeypatch, _payload(subject, f"{subject}@example.org"))

    async def fail_consent(self, *args, **kwargs):  # noqa: ANN001
        raise RuntimeError("simulated consent storage failure")

    monkeypatch.setattr(UserConsentRepository, "record_consent", fail_consent)
    response = client.post(
        "/api/v1/auth/firebase",
        json={"id_token": "firebase.test.token", "terms_accepted": True},
    )
    assert response.status_code == 500
    assert "access_token" not in response.text
    expected = uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{subject}")

    async def stored() -> bool:
        async with get_async_session_maker()() as session:
            return (
                await session.execute(select(User).where(User.id == expected))
            ).scalar_one_or_none() is not None

    assert asyncio.run(stored()) is False
