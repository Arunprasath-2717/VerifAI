"""Account username ownership is case-insensitive and enforced in the DB.

All tests use the isolated VERIFAI_TEST_DATABASE_URL test database.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_async_engine


def register(client: TestClient, username: str, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "StrongPassword2026!",
            "terms_accepted": True,
        },
    )


def test_case_insensitive_username_availability_and_login(client: TestClient) -> None:
    handle = "Arun_" + uuid.uuid4().hex[:10]
    normalized = handle.lower()
    url = "/api/v1/auth/username-availability"

    before = client.get(url, params={"username": handle.upper()})
    assert before.status_code == 200
    assert before.json() == {"username": normalized, "available": True}

    created = register(client, handle, normalized + "@example.invalid")
    assert created.status_code == 201, created.text
    assert created.json()["username"] == normalized
    assert "hashed_password" not in created.text

    after = client.get(url, params={"username": handle.upper()})
    assert after.status_code == 200
    assert after.json() == {"username": normalized, "available": False}

    duplicate = register(client, handle.upper(), uuid.uuid4().hex + "@example.invalid")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["details"]["field"] == "username"

    authenticated = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": handle.upper(), "password": "StrongPassword2026!"},
    )
    assert authenticated.status_code == 200, authenticated.text
    assert authenticated.json()["access_token"]
    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer " + authenticated.json()["access_token"]},
    )
    assert profile.status_code == 200
    assert profile.json()["username"] == normalized


def test_username_api_rejects_invalid_input(client: TestClient) -> None:
    for name in ("ab", "bad name", "bad.name", "a" * 65, "a@b"):
        result = client.get(
            "/api/v1/auth/username-availability", params={"username": name}
        )
        assert result.status_code == 422, (name, result.text)


def test_database_has_atomic_case_insensitive_unique_index() -> None:
    """Database DDL protects against concurrent requests bypassing the pre-check."""

    async def check():
        from sqlalchemy import text

        engine = get_async_engine()
        if engine.dialect.name != "postgresql":
            pytest.skip("PostgreSQL functional-index DDL is database-specific")
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM pg_indexes "
                    "WHERE tablename='users' AND indexname='uq_users_username_lower' "
                    "AND indexdef ILIKE '%UNIQUE%'"
                )
            )
            assert result.scalar_one() == 1

    import asyncio

    asyncio.run(check())
