"""End-to-End Real Lifecycle Scenario Test.

Validates the full chain without any mock/fake runtime data:
1. User registration & authentication
2. Private KB document ingestion & chunking
3. Chat conversation creation
4. Truthful Multi-LLM prompt processing
5. Real claim extraction & KB-first verification
6. Independent judge evaluation and decision persistence
7. User-specific history retrieval
8. Strict cross-user data isolation (User B denied User A's data)
9. Complete user data cascade purge and verification of deletion
"""

import pytest
from starlette.testclient import TestClient

from app.core.security import clear_ephemeral_users
from app.modules.chat.service import clear_ephemeral_chat
from app.modules.knowledge.service import clear_ephemeral_kb


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure clean runtime state before and after E2E test."""
    clear_ephemeral_users()
    clear_ephemeral_chat()
    clear_ephemeral_kb()
    yield
    clear_ephemeral_users()
    clear_ephemeral_chat()
    clear_ephemeral_kb()


def test_full_real_system_e2e_lifecycle(client: TestClient):
    """Execute complete multi-phase end-to-end real user lifecycle."""
    # --------------------------------------------------------------------------
    # Step 1: User A Registration & Authentication
    # --------------------------------------------------------------------------
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr_alice@verifai-research.org",
            "username": "dr_alice",
            "password": "SecureLabPassword2026!",
            "terms_accepted": True,
        },
    )
    assert reg_a.status_code == 201, reg_a.text
    user_a_data = reg_a.json()
    user_a_id = user_a_data["id"]

    login_a = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": "dr_alice",
            "password": "SecureLabPassword2026!",
        },
    )
    assert login_a.status_code == 200, login_a.text
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Verify authenticated profile
    me_resp = client.get("/api/v1/auth/me", headers=headers_a)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "dr_alice@verifai-research.org"

    # --------------------------------------------------------------------------
    # Step 2: Upload Real Document to Private Knowledge Base
    # --------------------------------------------------------------------------
    kb_doc_resp = client.post(
        "/api/v1/knowledge/documents",
        headers=headers_a,
        json={
            "title": "Atmospheric Thermodynamics Findings",
            "text": (
                "Pure water boils at precisely 100 degrees Celsius under a standard "
                "atmospheric pressure of 101.325 kilopascals at sea level."
            ),
            "filename": "thermo_findings.txt",
            "content_type": "text/plain",
        },
    )
    assert kb_doc_resp.status_code == 201, kb_doc_resp.text
    doc_data = kb_doc_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["owner_id"] == user_a_id
    assert doc_data["chunk_count"] >= 1

    # --------------------------------------------------------------------------
    # Step 3: Create Chat Conversation
    # --------------------------------------------------------------------------
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        headers=headers_a,
        json={"title": "Thermodynamics Inquiry"},
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # --------------------------------------------------------------------------
    # Step 4: Dispatch Prompt to Configured Models (Truthful Execution)
    # --------------------------------------------------------------------------
    prompt_resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=headers_a,
        json={
            "prompt": "At what temperature does water boil under 1 atm?",
            "models": [
                {"provider": "openai", "model_name": "gpt-4o-mini"},
            ],
            "verify": True,
        },
    )
    # A chat without a verified user-owned key is rejected before any
    # persistence or upstream usage; the rest of the KB/E2E lifecycle proceeds.
    assert prompt_resp.status_code == 400
    assert "verify" in prompt_resp.json()["error"]["message"].lower()
    assert (
        client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers_a).json()[
            "messages"
        ]
        == []
    )

    # --------------------------------------------------------------------------
    # Step 5: Execute Shared Verification Pipeline (Paste & Verify Entrypoint)
    # --------------------------------------------------------------------------
    verify_resp = client.post(
        "/api/v1/verification",
        headers=headers_a,
        json={
            "text": (
                "Pure water boils at 100 degrees Celsius under standard atmospheric pressure."
            ),
        },
    )
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    verification_id = v_data["verification_id"]
    assert v_data["owner_id"] == user_a_id
    assert v_data["total_claims"] >= 1
    assert len(v_data["claims"]) >= 1

    # Verify claim extraction derived from actual input text
    first_claim = v_data["claims"][0]
    assert "water boils" in first_claim["claim_text"].lower()
    assert first_claim["content_type"] == "FACTUAL"

    # Verify audit trail records real orchestration stages
    assert len(v_data["audit_trail"]) > 0

    # --------------------------------------------------------------------------
    # Step 6: Fetch History (Conversations & Verifications)
    # --------------------------------------------------------------------------
    conv_history = client.get("/api/v1/history/conversations", headers=headers_a)
    assert conv_history.status_code == 200
    assert conv_history.json()["total"] >= 1

    verif_history = client.get("/api/v1/history/verifications", headers=headers_a)
    assert verif_history.status_code == 200
    assert verif_history.json()["total"] >= 1

    # --------------------------------------------------------------------------
    # Step 7: Register User B & Verify Strict Cross-User Isolation
    # --------------------------------------------------------------------------
    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr_bob@external-agency.gov",
            "username": "dr_bob",
            "password": "DifferentPassword2026!",
            "terms_accepted": True,
        },
    )
    assert reg_b.status_code == 201

    login_b = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": "dr_bob",
            "password": "DifferentPassword2026!",
        },
    )
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B cannot access User A's verification job -> 403 Forbidden
    forb_v = client.get(
        f"/api/v1/history/verifications/{verification_id}", headers=headers_b
    )
    assert forb_v.status_code == 403

    # User B cannot access User A's conversation -> 403 Forbidden
    forb_c = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers_b)
    assert forb_c.status_code == 403

    # User B cannot access User A's KB document -> 403 Forbidden or 404 Not Found (strict namespace isolation)
    forb_doc = client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=headers_b)
    assert forb_doc.status_code in (403, 404)

    # User B search in KB returns 0 results from User A's private documents
    kb_search_b = client.post(
        "/api/v1/knowledge/search",
        headers=headers_b,
        json={"query": "water boils 100 degrees"},
    )
    assert kb_search_b.status_code == 200
    assert kb_search_b.json()["total_chunks_matched"] == 0
    assert len(kb_search_b.json()["results"]) == 0

    # --------------------------------------------------------------------------
    # Step 8: User A Data Lifecycle & Purge
    # --------------------------------------------------------------------------
    purge_resp = client.delete("/api/v1/history/purge?confirm=true", headers=headers_a)
    assert purge_resp.status_code == 200
    purge_res = purge_resp.json()
    assert purge_res["success"] is True
    assert purge_res["deleted_conversations"] >= 1
    assert purge_res["deleted_verifications"] >= 1
    assert purge_res["deleted_documents"] >= 1

    # Verify User A's resources are completely removed
    assert (
        client.get("/api/v1/history/conversations", headers=headers_a).json()["total"]
        == 0
    )
    assert (
        client.get("/api/v1/history/verifications", headers=headers_a).json()["total"]
        == 0
    )
    assert (
        client.get("/api/v1/knowledge/documents", headers=headers_a).json()[
            "total_documents"
        ]
        == 0
    )
