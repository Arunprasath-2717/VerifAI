"""Exhaustive tests for user ownership, namespace isolation, IDOR prevention, and RBAC."""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import (
    clear_ephemeral_users,
    create_access_token,
)
from app.models.user import User
from app.modules.knowledge.service import clear_ephemeral_kb
from app.schemas.auth import UserRole


@pytest.fixture(autouse=True)
def clean_stores() -> Generator[None, None, None]:
    """Reset ephemeral users and knowledge base stores before and after each test."""
    clear_ephemeral_users()
    clear_ephemeral_kb()
    yield
    clear_ephemeral_users()
    clear_ephemeral_kb()


def _register_and_login(
    client: TestClient, email: str, username: str
) -> tuple[str, str]:
    """Helper to register and login a test user, returning (token, user_id)."""
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "Password123!"},
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": username, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return token, user_id


def test_user_a_cannot_access_user_b_verification(client: TestClient) -> None:
    """Verify that User A cannot retrieve User B's verification job (IDOR prevention)."""
    token_a, id_a = _register_and_login(client, "alice@test.com", "alice_user")
    token_b, id_b = _register_and_login(client, "bob@test.com", "bob_user")

    # Bob creates a verification job
    bob_verify_res = client.post(
        "/api/v1/verification",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "text": "Water boils at 100 degrees Celsius under standard atmospheric pressure."
        },
    )
    assert bob_verify_res.status_code == 200
    bob_job_id = bob_verify_res.json()["verification_id"]
    assert bob_verify_res.json()["owner_id"] == id_b

    # Alice attempts to access Bob's verification job -> 403 Forbidden
    alice_access_res = client.get(
        f"/api/v1/verification/{bob_job_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alice_access_res.status_code == 403
    assert "access denied" in alice_access_res.json()["error"]["message"].lower()

    # Bob can access his own job -> 200 OK
    bob_access_res = client.get(
        f"/api/v1/verification/{bob_job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert bob_access_res.status_code == 200
    assert bob_access_res.json()["verification_id"] == bob_job_id


def test_user_cannot_spoof_owner_id_in_verification(client: TestClient) -> None:
    """Verify authenticated user cannot override owner_id with another user's ID."""
    token_a, id_a = _register_and_login(client, "alice_spoof@test.com", "alice_spoof")
    _, id_b = _register_and_login(client, "bob_target@test.com", "bob_target")

    # Alice passes options.owner_id = id_b
    response = client.post(
        "/api/v1/verification",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "text": "The Earth orbits the Sun.",
            "options": {"owner_id": id_b},
        },
    )
    assert response.status_code == 403
    assert (
        "cannot run verifications on behalf of another user"
        in response.json()["error"]["message"].lower()
    )


def test_user_a_cannot_access_user_b_kb_documents(client: TestClient) -> None:
    """Verify namespace isolation: User A cannot list or read User B's KB documents."""
    token_a, id_a = _register_and_login(client, "alice_kb@test.com", "alice_kb")
    token_b, id_b = _register_and_login(client, "bob_kb@test.com", "bob_kb")

    # Bob ingests a private document
    bob_doc_res = client.post(
        "/api/v1/knowledge/documents",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "title": "Bob Confidential Strategy",
            "text": "Project Falcon launch date is scheduled for Q4 2026.",
            "filename": "falcon.txt",
        },
    )
    assert bob_doc_res.status_code == 201
    bob_doc_id = bob_doc_res.json()["id"]
    assert bob_doc_res.json()["owner_id"] == id_b

    # Alice lists documents -> empty for Alice
    alice_list_res = client.get(
        "/api/v1/knowledge/documents",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alice_list_res.status_code == 200
    assert alice_list_res.json()["total_documents"] == 0
    assert len(alice_list_res.json()["documents"]) == 0

    # Alice attempts to access Bob's document directly -> 404 Not Found (namespace isolation)
    alice_get_res = client.get(
        f"/api/v1/knowledge/documents/{bob_doc_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alice_get_res.status_code == 404

    # Bob accesses his own document -> 200 OK
    bob_get_res = client.get(
        f"/api/v1/knowledge/documents/{bob_doc_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert bob_get_res.status_code == 200
    assert bob_get_res.json()["title"] == "Bob Confidential Strategy"


def test_user_a_cannot_search_user_b_kb_chunks(client: TestClient) -> None:
    """Verify search isolation: User A's search query never matches User B's chunks."""
    token_a, id_a = _register_and_login(client, "alice_s@test.com", "alice_s")
    token_b, id_b = _register_and_login(client, "bob_s@test.com", "bob_s")

    # Bob ingests document with distinctive keywords
    client.post(
        "/api/v1/knowledge/documents",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "title": "Quantum Falcon Algorithm",
            "text": "The quantum falcon encryption key is X992-DELTA-OMEGA-SECRET.",
            "filename": "quantum.txt",
        },
    )

    # Alice searches for the distinctive keywords
    alice_search_res = client.post(
        "/api/v1/knowledge/search",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"query": "quantum falcon encryption key"},
    )
    assert alice_search_res.status_code == 200
    # Alice's namespace has no matches
    assert alice_search_res.json()["total_chunks_matched"] == 0
    assert alice_search_res.json()["sufficiency"] == "KB_EMPTY"

    # Bob searches for the same keywords -> matches his document
    bob_search_res = client.post(
        "/api/v1/knowledge/search",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"query": "quantum falcon encryption key"},
    )
    assert bob_search_res.status_code == 200
    assert bob_search_res.json()["total_chunks_matched"] > 0
    assert bob_search_res.json()["sufficiency"] == "KB_RELEVANT"


def test_user_a_cannot_delete_user_b_document(client: TestClient) -> None:
    """Verify User A cannot delete User B's documents."""
    token_a, id_a = _register_and_login(client, "alice_del@test.com", "alice_del")
    token_b, id_b = _register_and_login(client, "bob_del@test.com", "bob_del")

    # Bob creates a document
    doc_res = client.post(
        "/api/v1/knowledge/documents",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Bob Doc", "text": "Content to protect.", "filename": "doc.txt"},
    )
    doc_id = doc_res.json()["id"]

    # Alice attempts to delete Bob's document -> 404 (does not exist in Alice's namespace)
    del_res = client.delete(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_res.status_code == 404

    # Document still exists for Bob
    get_res = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 200


def test_user_cannot_spoof_owner_in_kb_search(client: TestClient) -> None:
    """Verify User A cannot specify owner_id=user_b in KB search."""
    token_a, id_a = _register_and_login(
        client, "alice_kb_spoof@test.com", "alice_kb_spoof"
    )
    _, id_b = _register_and_login(client, "bob_kb_target@test.com", "bob_kb_target")

    search_res = client.post(
        "/api/v1/knowledge/search",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"query": "any query", "owner_id": id_b},
    )
    assert search_res.status_code == 403
    assert (
        "outside your user namespace" in search_res.json()["error"]["message"].lower()
    )


def test_random_uuid_probing_returns_404(client: TestClient) -> None:
    """Verify non-existent random UUIDs safely return 404 Not Found without leaking details."""
    token, _ = _register_and_login(client, "probe@test.com", "probe_user")
    random_id = uuid.uuid4()

    # Probing verifications
    v_res = client.get(
        f"/api/v1/verification/{random_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert v_res.status_code == 404
    assert v_res.json()["error"]["code"] == "NOT_FOUND"

    # Probing knowledge documents
    kb_res = client.get(
        f"/api/v1/knowledge/documents/{random_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert kb_res.status_code == 404
    assert kb_res.json()["error"]["code"] == "NOT_FOUND"


def test_admin_can_inspect_cross_user_resources(client: TestClient) -> None:
    """Verify ADMIN role has legitimate cross-namespace visibility."""
    _, id_b = _register_and_login(client, "bob_managed@test.com", "bob_managed")

    # Bob creates a verification job
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "bob_managed", "password": "Password123!"},
    )
    token_b = login_b.json()["access_token"]
    v_res = client.post(
        "/api/v1/verification",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "text": "The speed of sound in air is approximately 343 meters per second."
        },
    )
    bob_job_id = v_res.json()["verification_id"]

    # Generate an ADMIN user and token
    import asyncio
    import concurrent.futures

    from app.core.database import get_async_session_maker
    from app.core.security import hash_password

    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        email="admin@test.com",
        username="admin_user",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    async def _add_admin():
        maker = get_async_session_maker()
        async with maker() as session:
            session.add(admin_user)
            await session.commit()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, _add_admin()).result()

    admin_token, _ = create_access_token(
        subject=admin_id,
        role=UserRole.ADMIN,
        settings=get_settings(),
    )

    # Admin accesses Bob's verification job -> 200 OK
    admin_res = client.get(
        f"/api/v1/verification/{bob_job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["verification_id"] == bob_job_id
