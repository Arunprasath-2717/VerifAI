"""Automated tests for Chat, Multi-LLM execution, SSE streaming, and History lifecycle."""

import json

import pytest
from starlette.testclient import TestClient

from app.core.security import clear_ephemeral_users
from app.modules.chat.service import clear_ephemeral_chat


@pytest.fixture(autouse=True)
def setup_chat_fixtures():
    """Ensure clean test environment before each test."""
    clear_ephemeral_chat()
    clear_ephemeral_users()
    yield
    clear_ephemeral_chat()
    clear_ephemeral_users()


def _register_and_login(
    client: TestClient, email: str, username: str
) -> tuple[str, str]:
    """Helper to register and login a test user, returning (token, user_id)."""
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "StrongPassword2026!"},
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": username, "password": "StrongPassword2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return token, user_id


def test_conversation_crud_and_isolation(client: TestClient):
    """Verify conversation lifecycle and strict cross-user access boundaries."""
    token_a, user_a_id = _register_and_login(
        client, "alice_conv@example.com", "alice_conv"
    )
    token_b, user_b_id = _register_and_login(client, "bob_conv@example.com", "bob_conv")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A creates conversation
    create_resp = client.post(
        "/api/v1/chat/conversations",
        headers=headers_a,
        json={"title": "Physics Discussion"},
    )
    assert create_resp.status_code == 201
    conv_data = create_resp.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Physics Discussion"
    assert conv_data["owner_id"] == user_a_id

    # 2. User A retrieves conversation
    get_resp = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers_a)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv_id

    # 3. User B direct access attempt -> Forbidden (403)
    forbidden_resp = client.get(
        f"/api/v1/chat/conversations/{conv_id}", headers=headers_b
    )
    assert forbidden_resp.status_code == 403

    # 4. User A lists conversations -> sees own
    list_resp = client.get("/api/v1/chat/conversations", headers=headers_a)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # 5. User B lists conversations -> sees 0
    list_b_resp = client.get("/api/v1/chat/conversations", headers=headers_b)
    assert list_b_resp.status_code == 200
    assert list_b_resp.json()["total"] == 0

    # 6. User B cannot delete User A's conversation
    del_forbidden = client.delete(
        f"/api/v1/chat/conversations/{conv_id}", headers=headers_b
    )
    assert del_forbidden.status_code == 403

    # 7. User A deletes conversation -> 200 OK
    del_resp = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers_a)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # 8. Subsequent fetch returns 404
    fetch_deleted = client.get(
        f"/api/v1/chat/conversations/{conv_id}", headers=headers_a
    )
    assert fetch_deleted.status_code == 404


def test_multi_llm_model_limits_validation(client: TestClient):
    """Enforce minimum 1 and maximum 3 models per prompt (reject 0 or 4 models)."""
    token, user_id = _register_and_login(client, "limits@example.com", "limits_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Create conversation
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        headers=headers,
        json={"title": "Limits Test"},
    )
    conv_id = conv_resp.json()["id"]

    # 0 models -> Validation error (422)
    resp_0 = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=headers,
        json={"prompt": "Hello", "models": []},
    )
    assert resp_0.status_code == 422

    # 4 models -> Validation error (422)
    resp_4 = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=headers,
        json={
            "prompt": "Hello",
            "models": [
                {"provider": "openai", "model_name": "gpt-4o-mini"},
                {"provider": "anthropic", "model_name": "claude-3-haiku"},
                {"provider": "google", "model_name": "gemini-1.5-flash"},
                {"provider": "ollama", "model_name": "llama3"},
            ],
        },
    )
    assert resp_4.status_code == 422


def test_multi_llm_truthful_unavailable_state(client: TestClient):
    """Verify that unconfigured LLM credentials return truthful UNAVAILABLE status without mock text."""
    token, user_id = _register_and_login(
        client, "truthful@example.com", "truthful_user"
    )
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post(
        "/api/v1/chat/conversations",
        headers=headers,
        json={"title": "Truthfulness Check"},
    )
    conv_id = conv_resp.json()["id"]

    # Request 2 models without API keys configured in test environment
    prompt_resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=headers,
        json={
            "prompt": "Explain quantum entanglement briefly.",
            "models": [
                {"provider": "openai", "model_name": "gpt-4o"},
                {"provider": "anthropic", "model_name": "claude-3-opus"},
            ],
            "verify": True,
        },
    )
    assert prompt_resp.status_code == 200
    data = prompt_resp.json()

    assert data["conversation_id"] == conv_id
    assert len(data["runs"]) == 2

    # Zero mock text returned; structured UNAVAILABLE state
    for run in data["runs"]:
        assert run["status"] == "UNAVAILABLE"
        assert run["error_code"] == "CREDENTIALS_MISSING"
        assert "not configured" in run["error_message"].lower()
        assert run["response"] is None


def test_chat_sse_streaming_lifecycle_events(client: TestClient):
    """Verify that Server-Sent Events (SSE) stream authentic lifecycle events."""
    token, user_id = _register_and_login(
        client, "streamer@example.com", "streamer_user"
    )
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post(
        "/api/v1/chat/conversations",
        headers=headers,
        json={"title": "SSE Stream Test"},
    )
    conv_id = conv_resp.json()["id"]

    stream_resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages/stream",
        headers=headers,
        json={
            "prompt": "What is the capital of France?",
            "models": [{"provider": "openai", "model_name": "gpt-4o-mini"}],
            "verify": False,
        },
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]

    events = []
    for line in stream_resp.text.strip().split("\n\n"):
        if not line:
            continue
        event_name = None
        event_data = None
        for subline in line.split("\n"):
            if subline.startswith("event: "):
                event_name = subline.replace("event: ", "").strip()
            elif subline.startswith("data: "):
                event_data = json.loads(subline.replace("data: ", "").strip())
        if event_name and event_data:
            events.append((event_name, event_data))

    event_types = [e[0] for e in events]
    assert "REQUEST_ACCEPTED" in event_types
    assert "MODEL_REQUEST_STARTED" in event_types
    assert "MODEL_FAILED" in event_types or "MODEL_RESPONSE_COMPLETED" in event_types
    assert "COMPLETE" in event_types


def test_history_endpoints_and_filtering(client: TestClient):
    """Verify history endpoints (/history/conversations, /history/audit) and query filtering."""
    token_a, user_a_id = _register_and_login(
        client, "history_a@example.com", "history_a"
    )
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create 2 conversations
    client.post(
        "/api/v1/chat/conversations", headers=headers_a, json={"title": "Topic Alpha"}
    )
    client.post(
        "/api/v1/chat/conversations", headers=headers_a, json={"title": "Topic Beta"}
    )

    # Fetch history conversations
    hist_resp = client.get(
        "/api/v1/history/conversations?limit=10&offset=0", headers=headers_a
    )
    assert hist_resp.status_code == 200
    data = hist_resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Fetch audit history
    audit_resp = client.get("/api/v1/history/audit?limit=20", headers=headers_a)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert "items" in audit_data


def test_history_purge_data_lifecycle(client: TestClient):
    """Verify complete user data purge (/history/purge) cascades across all user resources."""
    token, user_id = _register_and_login(client, "purger@example.com", "purger_user")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create conversation and document
    conv_resp = client.post(
        "/api/v1/chat/conversations", headers=headers, json={"title": "To Delete"}
    )
    assert conv_resp.status_code == 201

    doc_resp = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={"title": "Purge Notes", "text": "Sample knowledge note to purge."},
    )
    assert doc_resp.status_code == 201

    # 2. Check conversation exists
    assert (
        client.get("/api/v1/chat/conversations", headers=headers).json()["total"] == 1
    )

    # 3. Purge user data
    purge_resp = client.delete("/api/v1/history/purge?confirm=true", headers=headers)
    assert purge_resp.status_code == 200
    purge_data = purge_resp.json()
    assert purge_data["success"] is True
    assert purge_data["deleted_conversations"] >= 1
    assert purge_data["deleted_documents"] >= 1

    # 4. Verify conversations and documents are now 0
    assert (
        client.get("/api/v1/chat/conversations", headers=headers).json()["total"] == 0
    )
    assert (
        client.get("/api/v1/knowledge/documents", headers=headers).json()[
            "total_documents"
        ]
        == 0
    )
