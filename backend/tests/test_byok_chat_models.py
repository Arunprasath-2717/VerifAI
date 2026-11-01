"""Owner-isolated Groq/OpenRouter BYOK model discovery and execution regressions.

Requires a disposable *_test PostgreSQL database. Every provider call uses
MockTransport: no real keys, accounts, cost, or external network requests.
"""

import asyncio
import json
import uuid

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.v1.endpoints import providers as provider_routes
from app.core.config import get_settings
from app.main import create_app
from app.modules.chat.safety import contains_credentials, redact_credentials
from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT
from app.modules.providers.model_discovery import parse_chat_models

KEY_GROQ = "groq-phase-test-key-private"
KEY_ROUTER = "router-phase-test-key-private"


@pytest.fixture
def client():
    settings = get_settings().model_copy(
        update={
            "PROVIDER_CREDENTIAL_ENCRYPTION_KEY": SecretStr(
                Fernet.generate_key().decode()
            ),
            # A global key must never be used for a different user's BYOK chat.
            "GROQ_API_KEY": SecretStr("server-global-must-not-be-used"),
            "OPENROUTER_API_KEY": SecretStr("server-global-must-not-be-used"),
            "TOKEN_BUDGET_MAX_RETRIES": 0,
            "FIREBASE_AUTH_ENABLED": False,
        }
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, name: str) -> dict[str, str]:
    user = name + "_" + uuid.uuid4().hex[:8]
    result = client.post(
        "/api/v1/auth/register",
        json={
            "email": user + "@example.invalid",
            "username": user,
            "password": "TemporaryTestPassword!2026",
            "terms_accepted": True,
        },
    )
    assert result.status_code == 201, result.text
    login_result = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user, "password": "TemporaryTestPassword!2026"},
    )
    assert login_result.status_code == 200
    return {"Authorization": "Bearer " + login_result.json()["access_token"]}


def provider_transport(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("authorization") in (
        "Bearer " + KEY_GROQ,
        "Bearer " + KEY_ROUTER,
    )
    if request.url.path.endswith("/models"):
        if "groq" in request.url.host:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "llama-3.3-70b-versatile",
                            "active": True,
                            "context_window": 128000,
                        },
                        {"id": "whisper-large-v3", "active": True},
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "meta-llama/llama-3.3-8b-instruct:free",
                        "name": "Llama Free",
                        "context_length": 64000,
                        "pricing": {"prompt": "0", "completion": "0"},
                    },
                    {
                        "id": "a-paid/model",
                        "name": "Paid",
                        "pricing": {"prompt": "0.0001", "completion": "0.0001"},
                    },
                ]
            },
        )
    raise AssertionError("Unexpected provider discovery path")


def test_parse_filters_paid_and_non_chat_models():
    router = parse_chat_models(
        "prov-openrouter",
        {
            "data": [
                {"id": "free/test:free", "pricing": {"prompt": "0", "completion": "0"}},
                {"id": "paid/test", "pricing": {"prompt": "0", "completion": "0"}},
                {"id": "unknown-pricing:free"},
                {"id": "one-sided-pricing:free", "pricing": {"prompt": "0"}},
                {
                    "id": "negative-pricing:free",
                    "pricing": {"prompt": "-0.001", "completion": "0"},
                },
                {
                    "id": "paid/test:free",
                    "pricing": {"prompt": "0.01", "completion": "0"},
                },
                {
                    "id": "audio/test:free",
                    "architecture": {"output_modalities": ["audio"]},
                },
            ]
        },
    )
    assert [entry.id for entry in router] == ["free/test:free"]
    groq = parse_chat_models(
        "prov-groq",
        {
            "data": [
                {"id": "llama-3.3-70b-versatile"},
                {"id": "whisper-large-v3"},
                {"id": "llama-guard-3-8b"},
            ]
        },
    )
    assert [entry.id for entry in groq] == ["llama-3.3-70b-versatile"]


def test_keys_are_saved_then_verified_then_discovered_only_for_owner(client):
    assert client.get("/api/v1/providers/chat-models").status_code == 401
    alice, bob = login(client, "alice_byok"), login(client, "bob_byok")
    saved = client.post(
        "/api/v1/providers/prov-groq/key", json={"apiKey": KEY_GROQ}, headers=alice
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "Saved"
    assert KEY_GROQ not in saved.text

    pending = client.get("/api/v1/providers/chat-models", headers=alice).json()
    assert pending["models"] == []
    assert (
        next(p for p in pending["providers"] if p["providerId"] == "prov-groq")[
            "status"
        ]
        == "Saved"
    )
    assert (
        client.get("/api/v1/providers/chat-models", headers=bob).json()["models"] == []
    )

    t = provider_routes._CHECK_TRANSPORT.set(httpx.MockTransport(provider_transport))
    try:
        verified = client.post("/api/v1/providers/prov-groq/test", headers=alice)
    finally:
        provider_routes._CHECK_TRANSPORT.reset(t)
    assert verified.status_code == 200 and verified.json()["success"]

    t = provider_routes._DISCOVERY_TRANSPORT.set(
        httpx.MockTransport(provider_transport)
    )
    try:
        discovered = client.get("/api/v1/providers/chat-models", headers=alice)
    finally:
        provider_routes._DISCOVERY_TRANSPORT.reset(t)
    assert discovered.status_code == 200
    assert [item["id"] for item in discovered.json()["models"]] == [
        "llama-3.3-70b-versatile"
    ]
    assert (
        next(
            p for p in discovered.json()["providers"] if p["providerId"] == "prov-groq"
        )["modelsCount"]
        == 1
    )
    assert KEY_GROQ not in discovered.text

    # A successful connection belongs to Alice, not Bob.
    assert (
        client.get("/api/v1/providers/chat-models", headers=bob).json()["models"] == []
    )


def test_groq_and_free_openrouter_execute_with_owners_credentials(client):
    alice, bob = login(client, "execute_alice"), login(client, "execute_bob")
    for provider, key in (("prov-groq", KEY_GROQ), ("prov-openrouter", KEY_ROUTER)):
        assert (
            client.post(
                "/api/v1/providers/" + provider + "/key",
                json={"apiKey": key},
                headers=alice,
            ).status_code
            == 200
        )
    transport = httpx.MockTransport(provider_transport)
    t = provider_routes._CHECK_TRANSPORT.set(transport)
    try:
        for provider in ("prov-groq", "prov-openrouter"):
            tested = client.post(
                "/api/v1/providers/" + provider + "/test", headers=alice
            )
            assert tested.status_code == 200 and tested.json()["success"]
    finally:
        provider_routes._CHECK_TRANSPORT.reset(t)

    conv = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Isolated BYOK testing"},
        headers=alice,
    )
    assert conv.status_code == 201
    conversation_id = conv.json()["id"]
    seen = []

    def answer(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert request.headers.get("authorization") in (
            "Bearer " + KEY_GROQ,
            "Bearer " + KEY_ROUTER,
        )
        body = __import__("json").loads(request.content)
        seen.append((request.url.host, body["model"], body["messages"][-1]["content"]))
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "choices": [{"message": {"content": "Real mocked upstream response"}}],
                "usage": {"prompt_tokens": 8, "completion_tokens": 7},
            },
        )

    t = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(answer))
    try:
        prompted = client.post(
            "/api/v1/chat/conversations/" + conversation_id + "/messages",
            json={
                "prompt": "Hello from Alice",
                "models": [
                    {"provider": "groq", "model_name": "llama-3.3-70b-versatile"},
                    {
                        "provider": "openrouter",
                        "model_name": "meta-llama/llama-3.3-8b-instruct:free",
                    },
                ],
                "verify": False,
            },
            headers=alice,
        )
        assert prompted.status_code == 200, prompted.text
        assert [run["status"] for run in prompted.json()["runs"]] == [
            "COMPLETED",
            "COMPLETED",
        ]
        assert len(seen) == 2  # Only the two independent model answers.
        assert prompted.json()["synthesis"] is None
        assert all("global" not in str(item) for item in seen)

        summary_response = client.post(
            "/api/v1/chat/conversations/"
            + conversation_id
            + "/messages/"
            + prompted.json()["user_message_id"]
            + "/summarize",
            headers=alice,
        )
        assert summary_response.status_code == 200, summary_response.text
        summary = summary_response.json()
        assert summary["method"] == "LLM_SYNTHESIS"
        assert summary["status"] == "UNVERIFIED"
        assert len(seen) == 3  # One extra call only after explicit Summarize.

        # Browser reload reconstructs the runs from persisted user message.
        detail = client.get(
            "/api/v1/chat/conversations/" + conversation_id, headers=alice
        ).json()
        assert len(detail["messages"]) == 1
        assert detail["messages"][0]["role"] == "USER"
        assert len(detail["messages"][0]["llm_runs"]) == 2
        assert detail["messages"][0]["synthesis"]["text"] == summary["text"]

        # Paid OpenRouter routes fail *before* another message is recorded.
        blocked = client.post(
            "/api/v1/chat/conversations/" + conversation_id + "/messages",
            json={
                "prompt": "Do not bill me",
                "models": [{"provider": "openrouter", "model_name": "a-paid/model"}],
                "verify": False,
            },
            headers=alice,
        )
        assert blocked.status_code == 400
        assert (
            len(
                client.get(
                    "/api/v1/chat/conversations/" + conversation_id, headers=alice
                ).json()["messages"]
            )
            == 1
        )

        # Bob's request with no BYOK must not invoke the Alice/global credential.
        bob_conv = client.post(
            "/api/v1/chat/conversations",
            json={"title": "Bob BYOK isolation"},
            headers=bob,
        ).json()["id"]
        before = len(seen)
        bob_result = client.post(
            "/api/v1/chat/conversations/" + bob_conv + "/messages",
            json={
                "prompt": "No borrowed keys",
                "models": [
                    {"provider": "groq", "model_name": "llama-3.3-70b-versatile"}
                ],
                "verify": False,
            },
            headers=bob,
        )
        assert bob_result.status_code == 400
        assert len(seen) == before
        assert (
            client.get("/api/v1/chat/conversations/" + bob_conv, headers=bob).json()[
                "messages"
            ]
            == []
        )
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(t)


def test_sensitive_inputs_are_blocked_before_provider_or_persistence(client):
    owner = login(client, "safety_owner")
    conversation = client.post(
        "/api/v1/chat/conversations",
        json={"title": "No credential transmission"},
        headers=owner,
    ).json()["id"]
    secret = "gsk_" + "z" * 38
    counted = []

    def transport(request: httpx.Request) -> httpx.Response:
        counted.append(str(request.url))
        raise AssertionError("Secret-bearing prompt must never reach a provider.")

    t = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(transport))
    try:
        response = client.post(
            "/api/v1/chat/conversations/" + conversation + "/messages",
            headers=owner,
            json={
                "prompt": "My API key is " + secret,
                "models": [
                    {"provider": "groq", "model_name": "llama-3.3-70b-versatile"}
                ],
                "verify": False,
            },
        )
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(t)

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"]["reason"] == "SENSITIVE_CREDENTIAL"
    assert secret not in response.text
    assert not counted
    messages = client.get(
        "/api/v1/chat/conversations/" + conversation, headers=owner
    ).json()["messages"]
    assert messages == []
    rejected_title = client.post(
        "/api/v1/chat/conversations",
        headers=owner,
        json={"title": "password = HardToGuessPassword2026!"},
    )
    assert rejected_title.status_code == 400
    assert "HardToGuessPassword2026" not in rejected_title.text
    rejected_stream = client.post(
        f"/api/v1/chat/conversations/{conversation}/messages/stream",
        headers=owner,
        json={
            "prompt": "key = " + secret,
            "models": [{"provider": "groq", "model_name": "llama-3.3-70b-versatile"}],
        },
    )
    assert rejected_stream.status_code == 400
    assert "REQUEST_ACCEPTED" not in rejected_stream.text
    assert not counted
    assert not contains_credentials("Design a PRD for secure API key management")
    assert contains_credentials("password: HardToGuessPassword2026!")
    assert redact_credentials("Use token " + secret).endswith("[REDACTED_CREDENTIAL]")


def test_real_model_probe_checks_response_and_owner_isolation(client):
    owner = login(client, "probe_owner")
    other = login(client, "probe_other")
    assert (
        client.post(
            "/api/v1/providers/prov-groq/key",
            headers=owner,
            json={"apiKey": KEY_GROQ},
        ).status_code
        == 200
    )
    transport = httpx.MockTransport(provider_transport)
    t = provider_routes._CHECK_TRANSPORT.set(transport)
    try:
        assert client.post("/api/v1/providers/prov-groq/test", headers=owner).json()[
            "success"
        ]
    finally:
        provider_routes._CHECK_TRANSPORT.reset(t)

    requests = []

    def real_probe(req: httpx.Request) -> httpx.Response:
        requests.append(req.url.path)
        assert req.headers["authorization"] == "Bearer " + KEY_GROQ
        if req.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "llama-3.3-70b-versatile", "active": True},
                        {"id": "temporarily-unavailable-model", "active": True},
                    ]
                },
            )
        if req.url.path.endswith("/chat/completions"):
            payload = json.loads(req.content)
            if payload["model"] == "temporarily-unavailable-model":
                return httpx.Response(429, json={"error": "rate limited"})
            return httpx.Response(
                200,
                json={
                    "model": payload["model"],
                    "choices": [{"message": {"content": "READY"}}],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 1},
                },
            )
        raise AssertionError("Unexpected endpoint")

    t1 = provider_routes._DISCOVERY_TRANSPORT.set(httpx.MockTransport(real_probe))
    t2 = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(real_probe))
    try:
        path = "/api/v1/providers/chat-models/probe"
        request = {"provider": "groq", "model_name": "llama-3.3-70b-versatile"}
        unauth = client.post(path, headers=other, json=request)
        assert unauth.status_code == 400
        assert not requests
        working = client.post(path, headers=owner, json=request)
        assert working.status_code == 200, working.text
        assert working.json()["working"] is True
        assert working.json()["status"] == "WORKING"
        failing = client.post(
            path,
            headers=owner,
            json={"provider": "groq", "model_name": "temporarily-unavailable-model"},
        )
        assert failing.status_code == 200
        assert failing.json()["working"] is False
        assert failing.json()["status"] == "UNAVAILABLE"
        blocked = client.post(
            path,
            headers=owner,
            json={"provider": "openrouter", "model_name": "paid/model"},
        )
        assert blocked.status_code == 400
        not_in_catalog = client.post(
            path,
            headers=owner,
            json={"provider": "groq", "model_name": "invented-paid-route"},
        )
        assert not_in_catalog.status_code == 400
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(t2)
        provider_routes._DISCOVERY_TRANSPORT.reset(t1)


def test_three_independent_models_run_concurrently_and_synthesize(client):
    user = login(client, "concurrent_owner")
    for provider, key in (
        ("prov-groq", KEY_GROQ),
        ("prov-openrouter", KEY_ROUTER),
    ):
        assert (
            client.post(
                f"/api/v1/providers/{provider}/key",
                headers=user,
                json={"apiKey": key},
            ).status_code
            == 200
        )

    async def catalog(req: httpx.Request) -> httpx.Response:
        if "groq" in req.url.host:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "groq-chat-a", "active": True},
                        {"id": "groq-chat-b", "active": True},
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "router-chat:free",
                        "pricing": {"prompt": "0", "completion": "0"},
                    }
                ]
            },
        )

    t1 = provider_routes._CHECK_TRANSPORT.set(httpx.MockTransport(catalog))
    try:
        for provider in ("prov-groq", "prov-openrouter"):
            result = client.post(f"/api/v1/providers/{provider}/test", headers=user)
            assert result.json()["success"]
    finally:
        provider_routes._CHECK_TRANSPORT.reset(t1)

    conv = client.post(
        "/api/v1/chat/conversations",
        headers=user,
        json={"title": "Three-way architectural review"},
    ).json()["id"]

    active = 0
    max_active = 0
    calls = []

    async def execute(req: httpx.Request) -> httpx.Response:
        nonlocal active, max_active
        assert req.headers["authorization"] in (
            "Bearer " + KEY_GROQ,
            "Bearer " + KEY_ROUTER,
        )
        body = json.loads(req.content)
        active += 1
        max_active = max(active, max_active)
        calls.append(body)
        await asyncio.sleep(0.075)
        active -= 1
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "choices": [
                    {
                        "message": {
                            "content": "Architecture: split API service, worker, and database."
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 12},
            },
        )

    t = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(execute))
    try:
        response = client.post(
            f"/api/v1/chat/conversations/{conv}/messages",
            headers=user,
            json={
                "prompt": "Draft a safe project architecture.",
                "models": [
                    {"provider": "groq", "model_name": "groq-chat-a"},
                    {"provider": "groq", "model_name": "groq-chat-b"},
                    {"provider": "openrouter", "model_name": "router-chat:free"},
                ],
                "verify": False,
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["runs"]) == 3
        assert all(run["status"] == "COMPLETED" for run in body["runs"])
        assert max_active >= 2, "Independent model calls were serialized."
        assert len(calls) == 3, "Only three independent answers expected."
        assert body["synthesis"] is None

        summary_response = client.post(
            f"/api/v1/chat/conversations/{conv}/messages/{body['user_message_id']}/summarize",
            headers=user,
        )
        assert summary_response.status_code == 200, summary_response.text
        summary = summary_response.json()
        assert len(calls) == 4
        assert summary["method"] == "LLM_SYNTHESIS"
        assert summary["status"] == "UNVERIFIED"
        assert len(summary["source_models"]) == 3

        persisted = client.get(
            f"/api/v1/chat/conversations/{conv}", headers=user
        ).json()
        assert persisted["messages"][0]["synthesis"]["text"] == summary["text"]
        assert len(persisted["messages"][0]["llm_runs"]) == 3

        # A single model may not be sent three times as distinct lanes.
        duplicate = client.post(
            f"/api/v1/chat/conversations/{conv}/messages",
            headers=user,
            json={
                "prompt": "second",
                "models": [
                    {"provider": "groq", "model_name": "groq-chat-a"},
                    {"provider": "groq", "model_name": "groq-chat-a"},
                ],
                "verify": False,
            },
        )
        assert duplicate.status_code == 400
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(t)
