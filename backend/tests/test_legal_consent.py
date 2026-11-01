"""Automated tests for Terms & Conditions, Privacy Policy, and user consent audit records."""

import uuid
from datetime import UTC, datetime

from starlette.testclient import TestClient

from app.core.config import get_settings


def test_legal_versions_endpoint(client: TestClient) -> None:
    """Verify that GET /api/v1/legal/versions returns authoritative config."""
    settings = get_settings()
    res = client.get("/api/v1/legal/versions")
    assert res.status_code == 200
    data = res.json()

    assert data["terms_version"] == settings.TERMS_VERSION
    assert data["privacy_version"] == settings.PRIVACY_POLICY_VERSION
    assert data["terms_effective_date"] == settings.TERMS_EFFECTIVE_DATE
    assert data["privacy_effective_date"] == settings.PRIVACY_EFFECTIVE_DATE
    assert data["legal_contact_email"] == settings.LEGAL_CONTACT_EMAIL
    assert data["governing_law"] == settings.GOVERNING_LAW
    assert data["minimum_age_requirement"] == settings.MINIMUM_AGE_REQUIREMENT


def test_registration_blocked_without_consent(client: TestClient) -> None:
    """Verify that registration fails with 422/400 if terms_accepted is missing or False."""
    # 1. Missing terms_accepted entirely
    res1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "noconsent1@example.com",
            "username": "noconsent_01",
            "password": "ValidPassword123!",
        },
    )
    assert res1.status_code == 422

    # 2. Explicitly False terms_accepted
    res2 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "noconsent2@example.com",
            "username": "noconsent_02",
            "password": "ValidPassword123!",
            "terms_accepted": False,
        },
    )
    assert res2.status_code == 422
    assert "terms & conditions" in str(res2.json()).lower()


def test_registration_succeeds_with_consent_and_persists_audit(
    client: TestClient,
) -> None:
    """Verify that registration succeeds with consent and records authoritative server-UTC audit entry."""
    settings = get_settings()
    email = f"consenting_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"

    payload = {
        "email": email,
        "username": username,
        "password": "SafePassword2026!",
        "terms_accepted": True,
    }

    start_utc = datetime.now(UTC)
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    user_data = res.json()
    user_id = user_data["id"]

    # Log in to access authenticated /api/v1/legal/consent endpoint
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": email, "password": "SafePassword2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Verify user's consent record
    consent_res = client.get(
        "/api/v1/legal/consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert consent_res.status_code == 200
    consents = consent_res.json()
    assert len(consents) >= 1

    latest = consents[0]
    assert latest["user_id"] == user_id
    assert latest["terms_version"] == settings.TERMS_VERSION
    assert latest["privacy_version"] == settings.PRIVACY_POLICY_VERSION
    assert latest["action_source"] == "signup_form"

    # Verify timestamp is server-generated UTC
    consented_dt = datetime.fromisoformat(latest["consented_at"])
    assert consented_dt >= start_utc


def test_consent_user_isolation(client: TestClient) -> None:
    """Verify that User A cannot view User B's consent records."""
    # Create User A
    user_a_email = f"usera_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": user_a_email,
            "username": f"user_a_{uuid.uuid4().hex[:6]}",
            "password": "PasswordA123!",
            "terms_accepted": True,
        },
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user_a_email, "password": "PasswordA123!"},
    )
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user_id"]

    # Create User B
    user_b_email = f"userb_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": user_b_email,
            "username": f"user_b_{uuid.uuid4().hex[:6]}",
            "password": "PasswordB123!",
            "terms_accepted": True,
        },
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user_b_email, "password": "PasswordB123!"},
    )
    token_b = login_b.json()["access_token"]
    user_b_id = login_b.json()["user_id"]

    # Query consents as User A
    res_a = client.get(
        "/api/v1/legal/consent",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    consents_a = res_a.json()
    assert all(c["user_id"] == str(user_a_id) for c in consents_a)
    assert not any(c["user_id"] == str(user_b_id) for c in consents_a)

    # Query consents as User B
    res_b = client.get(
        "/api/v1/legal/consent",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    consents_b = res_b.json()
    assert all(c["user_id"] == str(user_b_id) for c in consents_b)
    assert not any(c["user_id"] == str(user_a_id) for c in consents_b)


def test_reacceptance_records_new_consent_entry(client: TestClient) -> None:
    """Verify that re-accepting terms creates a new audit record without overwriting previous ones."""
    email = f"reaccept_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"reaccept_{uuid.uuid4().hex[:6]}",
            "password": "Password123!",
            "terms_accepted": True,
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": email, "password": "Password123!"},
    )
    token = login.json()["access_token"]

    # Post explicit re-acceptance
    reaccept_res = client.post(
        "/api/v1/legal/consent",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "terms_version": "2026.2",
            "privacy_version": "2026.2",
            "action_source": "policy_update_modal",
        },
    )
    assert reaccept_res.status_code == 201
    entry = reaccept_res.json()
    assert entry["terms_version"] == "2026.2"
    assert entry["action_source"] == "policy_update_modal"

    # List consents: both historical and new should be preserved
    list_res = client.get(
        "/api/v1/legal/consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    consents = list_res.json()
    assert len(consents) == 2
    assert consents[0]["terms_version"] == "2026.2"
    assert consents[1]["terms_version"] == "2026.1"
