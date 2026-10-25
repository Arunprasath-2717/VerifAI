"""Native OpenAI, Anthropic and Gemini BYOK integration with bounded review."""

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
from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT


@pytest.fixture
def app_client():
    settings = get_settings().model_copy(
        update={
            "PROVIDER_CREDENTIAL_ENCRYPTION_KEY": SecretStr(
                Fernet.generate_key().decode()
            ),
            "FIREBASE_AUTH_ENABLED": False,
            "TOKEN_BUDGET_MAX_RETRIES": 0,
        }
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as browser:
        yield browser
    app.dependency_overrides.clear()


def identity(client: TestClient, label: str):
    name = label + uuid.uuid4().hex[:9]
    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": name + "@example.invalid",
            "username": name,
            "password": "TemporaryUnitTestPassword123!",
            "terms_accepted": True,
        },
    )
    assert created.status_code == 201, created.text
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": name,
            "password": "TemporaryUnitTestPassword123!",
        },
    )
    assert login.status_code == 200, login.text
    return {"Authorization": "Bearer " + login.json()["access_token"]}


MODELS = {
    "openai": "gpt-5-mini-test",
    "anthropic": "claude-sonnet-test",
    "google": "gemini-3-flash-test",
}


def vendor(request):
    host = request.url.host or ""
    if "anthropic.com" in host:
        return "anthropic"
    if "googleapis.com" in host:
        return "google"
    if "openai.com" in host:
        return "openai"
    raise AssertionError("Unexpected host")


def catalog(request):
    provider = vendor(request)
    if provider == "google":
        return httpx.Response(
            200,
            json={
                "models": [
                    {
                        "name": "models/" + MODELS["google"],
                        "supportedGenerationMethods": ["generateContent"],
                    }
                ]
            },
        )
    return httpx.Response(200, json={"data": [{"id": MODELS[provider]}]})


def test_three_native_vendors_and_on_demand_summary(app_client: TestClient):
    client = app_client
    owner = identity(client, "vendors_")
    for provider in MODELS:
        saved = client.post(
            f"/api/v1/providers/prov-{provider}/key",
            headers=owner,
            json={"apiKey": "test-only-" + provider},
        )
        assert saved.status_code == 200, saved.text

    checking = provider_routes._CHECK_TRANSPORT.set(httpx.MockTransport(catalog))
    try:
        for provider in MODELS:
            check = client.post(
                f"/api/v1/providers/prov-{provider}/test", headers=owner
            )
            assert check.status_code == 200 and check.json()["success"], check.text
    finally:
        provider_routes._CHECK_TRANSPORT.reset(checking)

    discovering = provider_routes._DISCOVERY_TRANSPORT.set(httpx.MockTransport(catalog))
    active = 0
    maximum = 0
    invoked = []

    async def completion(request):
        nonlocal active, maximum
        provider = vendor(request)
        headers = request.headers
        key = "test-only-" + provider
        if provider == "google":
            assert headers["x-goog-api-key"] == key
        elif provider == "anthropic":
            assert headers["x-api-key"] == key
        else:
            assert headers["authorization"] == "Bearer " + key
        json.loads(request.content)
        invoked.append(provider)
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.025)
        active -= 1
        if provider == "google":
            data = {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Integrated idea with a scoped MVP."}]
                        }
                    }
                ]
            }
        elif provider == "anthropic":
            data = {
                "content": [
                    {"type": "text", "text": "Integrated idea with an API and tests."}
                ]
            }
        else:
            data = {
                "choices": [
                    {
                        "message": {
                            "content": "Integrated idea with user stories and architecture."
                        }
                    }
                ]
            }
        return httpx.Response(200, json=data)

    executing = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(completion))
    try:
        listing = client.get("/api/v1/providers/chat-models", headers=owner)
        assert listing.status_code == 200, listing.text
        assert {item["provider"] for item in listing.json()["models"]} == set(MODELS)

        for provider, model in MODELS.items():
            probe = client.post(
                "/api/v1/providers/chat-models/probe",
                headers=owner,
                json={"provider": provider, "model_name": model},
            )
            assert probe.status_code == 200 and probe.json()["working"], probe.text

        conv = client.post(
            "/api/v1/chat/conversations",
            headers=owner,
            json={"title": "Multi-vendor project"},
        ).json()["id"]
        reply = client.post(
            f"/api/v1/chat/conversations/{conv}/messages",
            headers=owner,
            json={
                "prompt": "Build a project requirements proposal.",
                "models": [
                    {"provider": key, "model_name": model}
                    for key, model in MODELS.items()
                ],
                "verify": False,
            },
        )
        assert reply.status_code == 200, reply.text
        body = reply.json()
        assert maximum >= 2
        assert len(body["runs"]) == 3
        assert all(item["status"] == "COMPLETED" for item in body["runs"])
        assert body["synthesis"] is None
        assert len(invoked) == 6  # three probes, three independent drafts
        history = client.get(f"/api/v1/chat/conversations/{conv}", headers=owner).json()
        assert history["messages"][0]["synthesis"] is None

        summary_url = f"/api/v1/chat/conversations/{conv}/messages/{body['user_message_id']}/summarize"
        combined = client.post(summary_url, headers=owner)
        assert combined.status_code == 200, combined.text
        combined_data = combined.json()
        assert combined_data["method"] == "LLM_SYNTHESIS"
        assert combined_data["status"] == "UNVERIFIED"
        assert len(combined_data["source_models"]) == 3
        assert len(invoked) == 7  # one additional inference only after clicking
        assert combined_data["selected_model"]["provider"] == "openai"

        again = client.post(summary_url, headers=owner)
        assert again.status_code == 200
        assert again.json() == combined_data
        assert len(invoked) == 7  # returning saved summary is idempotent

        history = client.get(f"/api/v1/chat/conversations/{conv}", headers=owner).json()
        assert history["messages"][0]["synthesis"]["text"] == combined_data["text"]

        outsider = identity(client, "summary_other_")
        forbidden = client.post(summary_url, headers=outsider)
        assert forbidden.status_code == 403
        assert len(invoked) == 7  # unauthorized users never trigger inference

        absent = client.post(
            f"/api/v1/chat/conversations/{conv}/messages/{uuid.uuid4()}/summarize",
            headers=owner,
        )
        assert absent.status_code == 404

        invalid = client.post(
            f"/api/v1/chat/conversations/{conv}/messages",
            headers=owner,
            json={
                "prompt": "wrong rounds",
                "models": [{"provider": "google", "model_name": MODELS["google"]}],
                "refinement_rounds": 3,
            },
        )
        assert invalid.status_code == 422
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(executing)
        provider_routes._DISCOVERY_TRANSPORT.reset(discovering)
