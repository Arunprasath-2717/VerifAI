"""Server-side consent enforcement on the Firebase sign-in path.

The Firebase token verifier is mocked; no Google or Firebase network calls are
made and no production data is touched. Runs against the isolated test DB.
"""

import uuid

import pytest
from sqlalchemy import select
from starlette.testclient import TestClient

import app.api.v1.endpoints.auth as auth_endpoint
from app.core.config import Settings, get_settings
from app.core.database import get_async_session_maker
from app.models.user import User
from app.models.user_consent import UserConsent


def _payload(uid: str) -> dict:
    return {
        "sub": uid,
        "email": f"{uid}@example.com",
        "name": "Consent Tester",
        "email_verified": True,
        "iss": "https://securetoken.google.com/verifai-22c4b",
        "aud": "verifai-22c4b",
        "firebase": {"sign_in_provider": "password"},
    }


@pytest.fixture
def uid() -> str:
    return f"fb_consent_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def mock_firebase(monkeypatch: pytest.MonkeyPatch):
    state: dict[str, dict] = {}

    def _verify(token: str, settings):  # noqa: ANN001
        return state["payload"]

    monkeypatch.setattr(auth_endpoint, "verify_firebase_id_token", _verify)
    return state


def _post(client: TestClient, body: dict):
    return client.post("/api/v1/auth/firebase", json={"id_token": "mock.token", **body})


def _user_uuid(uid: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"firebase:{uid}")


async def _consent_rows(user_id: uuid.UUID) -> list[UserConsent]:
    async with get_async_session_maker()() as session:
        res = await session.execute(
            select(UserConsent).where(UserConsent.user_id == user_id)
        )
        return list(res.scalars().all())


async def _user_exists(user_id: uuid.UUID) -> bool:
    async with get_async_session_maker()() as session:
        res = await session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none() is not None


def test_new_account_without_acceptance_is_rejected_and_not_provisioned(
    client: TestClient, mock_firebase: dict, uid: str
) -> None:
    import asyncio

    mock_firebase["payload"] = _payload(uid)
    resp = _post(client, {})  # no terms_accepted, not a signup request
    assert resp.status_code == 400
    assert resp.json()["error"]["details"]["field"] == "terms_accepted"
    # The server must not create the account or any consent record.
    assert asyncio.run(_user_exists(_user_uuid(uid))) is False
    assert asyncio.run(_consent_rows(_user_uuid(uid))) == []


def test_new_account_with_explicit_false_is_rejected(
    client: TestClient, mock_firebase: dict, uid: str
) -> None:
    import asyncio

    mock_firebase["payload"] = _payload(uid)
    resp = _post(client, {"terms_accepted": False, "is_signup": False})
    assert resp.status_code == 400
    assert asyncio.run(_user_exists(_user_uuid(uid))) is False


def test_new_account_with_acceptance_succeeds_and_records_consent(
    client: TestClient, mock_firebase: dict, uid: str
) -> None:
    import asyncio

    settings = get_settings()
    mock_firebase["payload"] = _payload(uid)
    resp = _post(client, {"terms_accepted": True, "is_signup": True})
    assert resp.status_code == 200, resp.text

    rows = asyncio.run(_consent_rows(_user_uuid(uid)))
    assert len(rows) == 1
    assert rows[0].terms_version == settings.TERMS_VERSION
    assert rows[0].privacy_version == settings.PRIVACY_POLICY_VERSION
    assert rows[0].action_source == "signup_form"


def test_existing_user_with_current_consent_logs_in_without_new_record(
    client: TestClient, mock_firebase: dict, uid: str
) -> None:
    import asyncio

    mock_firebase["payload"] = _payload(uid)
    assert _post(client, {"terms_accepted": True, "is_signup": True}).status_code == 200
    before = len(asyncio.run(_consent_rows(_user_uuid(uid))))

    # Ordinary login: no acceptance sent, current consent on file -> allowed.
    assert _post(client, {}).status_code == 200
    # Re-sending acceptance while current must not duplicate the record.
    assert _post(client, {"terms_accepted": True}).status_code == 200
    assert len(asyncio.run(_consent_rows(_user_uuid(uid)))) == before


def test_outdated_consent_requires_reacceptance(
    client: TestClient, mock_firebase: dict, uid: str
) -> None:
    import asyncio

    mock_firebase["payload"] = _payload(uid)
    assert _post(client, {"terms_accepted": True, "is_signup": True}).status_code == 200

    # Simulate a published terms update: stored consent is now outdated. The test
    # app injects its own Settings through dependency_overrides, so override there.
    settings: Settings = client.app.dependency_overrides[get_settings]()
    bumped = settings.model_copy(update={"TERMS_VERSION": "2099.1"})
    client.app.dependency_overrides[get_settings] = lambda: bumped

    blocked = _post(client, {})
    assert blocked.status_code == 403
    assert blocked.json()["error"]["details"]["reason"] == "TERMS_REACCEPTANCE_REQUIRED"
    assert blocked.json()["error"]["details"]["terms_version"] == "2099.1"

    # Accepting the new version records a reacceptance row and allows sign-in.
    accepted = _post(client, {"terms_accepted": True})
    assert accepted.status_code == 200, accepted.text
    rows = asyncio.run(_consent_rows(_user_uuid(uid)))
    assert any(
        r.terms_version == "2099.1" and r.action_source == "reacceptance" for r in rows
    )
    client.app.dependency_overrides[get_settings] = lambda: settings


def test_invalid_firebase_token_is_rejected_before_any_consent_logic(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, uid: str
) -> None:
    from app.core.errors import UnauthorizedError

    def _reject(token: str, settings):  # noqa: ANN001
        raise UnauthorizedError(
            message="bad token", details={"reason": "invalid_firebase_token"}
        )

    monkeypatch.setattr(auth_endpoint, "verify_firebase_id_token", _reject)
    resp = _post(client, {"terms_accepted": True})
    assert resp.status_code == 401
