"""Per-account brute-force protection for password login."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.account_lockout import AccountLockout, get_account_lockout
from app.core.errors import RateLimitError


@pytest.fixture
def lockout() -> Generator[AccountLockout, None, None]:
    instance = get_account_lockout()
    instance.clear()
    yield instance
    instance.clear()


def test_locks_after_max_failures(lockout: AccountLockout) -> None:
    for _ in range(lockout.max_failures):
        lockout.check_allowed("alice")
        lockout.record_failure("alice")
    with pytest.raises(RateLimitError) as exc:
        lockout.check_allowed("alice")
    assert exc.value.details["reason"] == "account_locked"
    assert exc.value.retry_after >= 1


def test_below_threshold_is_not_locked(lockout: AccountLockout) -> None:
    for _ in range(lockout.max_failures - 1):
        lockout.record_failure("alice")
    lockout.check_allowed("alice")  # must not raise


def test_lock_is_per_account_not_global(lockout: AccountLockout) -> None:
    for _ in range(lockout.max_failures):
        lockout.record_failure("alice")
    lockout.check_allowed("bob")  # bob is unaffected


def test_identifier_is_case_and_whitespace_insensitive(lockout: AccountLockout) -> None:
    for _ in range(lockout.max_failures):
        lockout.record_failure("  Alice@Example.com ")
    with pytest.raises(RateLimitError):
        lockout.check_allowed("alice@example.com")


def test_success_clears_failure_count(lockout: AccountLockout) -> None:
    for _ in range(lockout.max_failures - 1):
        lockout.record_failure("alice")
    lockout.record_success("alice")
    for _ in range(lockout.max_failures - 1):
        lockout.record_failure("alice")
    lockout.check_allowed("alice")  # counter restarted, still below threshold


def test_lock_expires_after_cooldown() -> None:
    instance = AccountLockout(max_failures=2, window_seconds=60, lock_seconds=0.05)
    instance.record_failure("alice")
    instance.record_failure("alice")
    with pytest.raises(RateLimitError):
        instance.check_allowed("alice")
    import time

    time.sleep(0.1)
    instance.check_allowed("alice")  # cooldown elapsed


def test_memory_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.core.account_lockout as mod

    monkeypatch.setattr(mod, "MAX_TRACKED_ACCOUNTS", 5)
    instance = AccountLockout()
    for i in range(50):
        instance.record_failure(f"user{i}")
    assert len(instance._records) <= 5


def test_login_endpoint_locks_account_even_with_correct_password(
    client: TestClient,
) -> None:
    """End to end: after repeated failures the correct password is refused too."""
    get_account_lockout().clear()
    username = "lockout_user"
    password = "Password123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "lockout@test.com",
            "username": username,
            "password": password,
            "terms_accepted": True,
        },
    )
    assert reg.status_code == 201, reg.text

    limit = get_account_lockout().max_failures
    for _ in range(limit):
        bad = client.post(
            "/api/v1/auth/login",
            json={"email_or_username": username, "password": "wrong-password-1"},
        )
        assert bad.status_code == 401

    locked = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": username, "password": password},
    )
    assert locked.status_code == 429
    assert locked.json()["error"]["details"]["reason"] == "account_locked"
    assert "retry-after" in locked.headers
    get_account_lockout().clear()


def test_unknown_account_failures_also_count(client: TestClient) -> None:
    """Failures for non-existent accounts lock too, so enumeration cannot tell them apart."""
    get_account_lockout().clear()
    limit = get_account_lockout().max_failures
    for _ in range(limit):
        client.post(
            "/api/v1/auth/login",
            json={
                "email_or_username": "ghost_user_xyz",
                "password": "wrong-password-1",
            },
        )
    response = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "ghost_user_xyz", "password": "wrong-password-1"},
    )
    assert response.status_code == 429
    get_account_lockout().clear()
