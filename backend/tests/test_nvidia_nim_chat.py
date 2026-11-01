"""NVIDIA NIM compatibility and user-owned custom-model execution regressions.

All provider traffic is mocked; user credentials and paid upstream quotas
must never be used in these tests.
"""

from __future__ import annotations

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
from app.modules.chat.safety import contains_credentials
from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT
from app.modules.providers.openai_compatible import resolve_openai_base_url


@pytest.fixture
def client():
    config = get_settings().model_copy(
        update={
            "PROVIDER_CREDENTIAL_ENCRYPTION_KEY": SecretStr(
                Fernet.generate_key().decode()
            ),
            "FIREBASE_AUTH_ENABLED": False,
            "GROQ_API_KEY": SecretStr("do-not-use-server-global-groq"),
            "OPENROUTER_API_KEY": SecretStr("do-not-use-server-global-router"),
            "TOKEN_BUDGET_MAX_RETRIES": 0,
        }
    )
    app = create_app(settings=config)
    app.dependency_overrides[get_settings] = lambda: config
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def identity(client: TestClient, prefix: str) -> dict[str, str]:
    name = prefix + uuid.uuid4().hex[:7]
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{name}@example.invalid",
            "username": name,
            "password": "SafeTestPassword2026!",
            "terms_accepted": True,
        },
    )
    assert registered.status_code == 201, registered.text
    logged_in = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": name,
            "password": "SafeTestPassword2026!",
        },
    )
    assert logged_in.status_code == 200, logged_in.text
    return {"Authorization": "Bearer " + logged_in.json()["access_token"]}


def test_custom_nvidia_link_discover_probe_and_parallel_chat(client: TestClient):
    owner = identity(client, "nim_alice_")
    other = identity(client, "nim_bob_")
    provider_id = "prov-custom-nvidia-6187"
    secret = "nvapi-synthetic-test-not-an-actual-secret"
    model_a = "nvidia/nemotron-mini-test"
    model_b = "meta/llama-instruct-test"
    saved = client.post(
        f"/api/v1/providers/{provider_id}/key",
        headers=owner,
        json={
            "apiKey": secret,
            "name": "Nvidia",
            # Old app default must NEVER be used to forward this credential.
            "baseUrl": "http://localhost:8000/v1",
            "category": "cloud",
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "Saved"
    assert saved.json()["baseUrl"] == "https://integrate.api.nvidia.com/v1"
    assert secret not in saved.text

    def models(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "integrate.api.nvidia.com"
        assert request.url.path == "/v1/models"
        assert request.headers["authorization"] == "Bearer " + secret
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": model_a, "active": True, "context_window": 32768},
                    {"id": model_b, "active": True, "context_window": 32768},
                    {"id": "nvidia/audio-embed-test", "active": True},
                ]
            },
        )

    check = provider_routes._CHECK_TRANSPORT.set(httpx.MockTransport(models))
    try:
        tested = client.post(f"/api/v1/providers/{provider_id}/test", headers=owner)
        assert tested.status_code == 200 and tested.json()["success"], tested.text
    finally:
        provider_routes._CHECK_TRANSPORT.reset(check)

    catalog_transport = provider_routes._DISCOVERY_TRANSPORT.set(
        httpx.MockTransport(models)
    )
    seen = []
    active = 0
    max_parallel = 0

    async def completion(request: httpx.Request) -> httpx.Response:
        nonlocal active, max_parallel
        assert request.url.host == "integrate.api.nvidia.com"
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer " + secret
        payload = json.loads(request.content)
        seen.append(payload)
        active += 1
        max_parallel = max(active, max_parallel)
        await asyncio.sleep(0.03)
        active -= 1
        return httpx.Response(
            200,
            json={
                "model": payload["model"],
                "choices": [
                    {"message": {"content": "Separate verified upstream sample."}}
                ],
            },
        )

    chat_transport = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(completion))
    try:
        discovered = client.get("/api/v1/providers/chat-models", headers=owner)
        assert discovered.status_code == 200, discovered.text
        selected_models = [
            x for x in discovered.json()["models"] if x["providerId"] == provider_id
        ]
        assert len(selected_models) == 2
        assert all(m["provider"] == provider_id for m in selected_models)
        assert discovered.json()["providers"][-1]["name"] == "Nvidia"
        assert secret not in discovered.text

        # Bob cannot enumerate or test Alice's models/credential.
        bob_catalog = client.get("/api/v1/providers/chat-models", headers=other).json()
        assert not any(x["providerId"] == provider_id for x in bob_catalog["models"])
        probe_url = "/api/v1/providers/chat-models/probe"
        unauthorized = client.post(
            probe_url,
            headers=other,
            json={
                "provider": provider_id,
                "model_name": model_a,
            },
        )
        assert unauthorized.status_code == 400
        assert not seen

        tested_model = client.post(
            probe_url,
            headers=owner,
            json={
                "provider": provider_id,
                "model_name": model_a,
            },
        )
        assert tested_model.status_code == 200, tested_model.text
        assert tested_model.json()["working"] is True

        conversation = client.post(
            "/api/v1/chat/conversations",
            headers=owner,
            json={"title": "NVIDIA design session"},
        ).json()["id"]
        inference = client.post(
            f"/api/v1/chat/conversations/{conversation}/messages",
            headers=owner,
            json={
                "prompt": "Propose a trustworthy product requirements document.",
                "models": [
                    {"provider": provider_id, "model_name": model_a},
                    {"provider": provider_id, "model_name": model_b},
                ],
                "verify": False,
            },
        )
        assert inference.status_code == 200, inference.text
        body = inference.json()
        assert len(body["runs"]) == 2
        assert all(run["status"] == "COMPLETED" for run in body["runs"])
        assert max_parallel >= 2
        assert body["synthesis"] is None
        assert len(seen) == 3  # Probe + two concurrent generations.
        combined = client.post(
            f"/api/v1/chat/conversations/{conversation}/messages/{body['user_message_id']}/summarize",
            headers=owner,
        )
        assert combined.status_code == 200, combined.text
        summary = combined.json()
        assert summary["source_models"] == [
            f"{provider_id}/{model_a}",
            f"{provider_id}/{model_b}",
        ]
        assert len(seen) == 4  # One extra call after Summarize.
        detail = client.get(
            f"/api/v1/chat/conversations/{conversation}", headers=owner
        ).json()
        assert detail["messages"][0]["synthesis"]["text"] == summary["text"]
        assert secret not in inference.text
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(chat_transport)
        provider_routes._DISCOVERY_TRANSPORT.reset(catalog_transport)


def test_nvidia_first_class_uses_hosted_url_and_custom_local_is_rejected(client):
    assert contains_credentials("nvapi-" + "X" * 35)
    alice = identity(client, "nim_preset_")
    key = "nvapi-fake-for-unit-tests"
    hosted = client.post(
        "/api/v1/providers/prov-nvidia/key",
        headers=alice,
        json={"apiKey": key, "name": "NVIDIA NIM"},
    )
    assert hosted.status_code == 200, hosted.text
    assert hosted.json()["baseUrl"] == "https://integrate.api.nvidia.com/v1"
    assert (
        resolve_openai_base_url(
            "prov-custom-nvidia-old", "http://localhost:8000/v1", "Nvidia"
        )
        == "https://integrate.api.nvidia.com/v1"
    )

    unsafe = client.post(
        "/api/v1/providers/prov-custom-untrusted/key",
        headers=alice,
        json={
            "apiKey": "unsafe-example-secret",
            "name": "Untrusted endpoint",
            "baseUrl": "http://127.0.0.1:8000/v1",
        },
    )
    assert unsafe.status_code == 400
    assert "unsafe-example-secret" not in unsafe.text

    missing_url = client.post(
        "/api/v1/providers/prov-custom-no-host/key",
        headers=alice,
        json={"apiKey": "fake", "name": "Custom without a host"},
    )
    assert missing_url.status_code == 400
