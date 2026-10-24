"""Hermetic regression for owner-key model routing and honest inference status."""
import asyncio
import json

import httpx

from app.modules.llm.providers.byok_transport import CHAT_PROVIDER_TRANSPORT
from app.modules.llm.providers.owner_openai import OwnerOpenAICompatibleProvider
from app.modules.providers.model_discovery import parse_chat_models


def run_with_mock(provider: str, model: str, handler, *, max_tokens: int = 256):
    token = CHAT_PROVIDER_TRANSPORT.set(httpx.MockTransport(handler))
    try:
        adapter = OwnerOpenAICompatibleProvider(
            provider_id=provider, provider_name=provider,
            base_url=None, api_key="isolated-test-not-real",
        )
        return asyncio.run(adapter.execute(
            model_name=model, prompt="Say READY.", max_tokens=max_tokens,
        ))
    finally:
        CHAT_PROVIDER_TRANSPORT.reset(token)


def test_groq_uses_official_https_endpoint_and_reasoning_budget():
    def handler(request: httpx.Request):
        assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer isolated-test-not-real"
        data = json.loads(request.content)
        assert data["model"] == "openai/gpt-oss-120b"
        assert data["max_completion_tokens"] == 256
        assert data["reasoning_effort"] == "low"
        assert "max_tokens" not in data
        return httpx.Response(200, json={"choices":[{"message":{"content":"READY"}}]})
    result = run_with_mock("groq","openai/gpt-oss-120b",handler)
    assert result.status == "COMPLETED"
    assert result.response == "READY"
    assert result.error_code is None


def test_openrouter_free_model_preserves_exact_id_without_rewriting():
    def handler(request: httpx.Request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        data = json.loads(request.content)
        assert data["model"] == "google/gemma-4-26b-a4b-it:free"
        return httpx.Response(200, json={"choices":[{"message":{"content":"READY"}}]})
    result = run_with_mock("openrouter","google/gemma-4-26b-a4b-it:free",handler)
    assert result.status == "COMPLETED"


def test_nvidia_nim_uses_official_host_and_supports_structured_text():
    def handler(request: httpx.Request):
        assert str(request.url) == "https://integrate.api.nvidia.com/v1/chat/completions"
        return httpx.Response(200, json={"choices":[{"message":{"content":[{"type":"text","text":"READY"}]}}]})
    result = run_with_mock("nvidia","openai/gpt-oss-20b",handler)
    assert result.status == "COMPLETED"
    assert result.response == "READY"


def test_a_token_budget_exhaustion_is_not_mistaken_for_success():
    result = run_with_mock("groq","openai/gpt-oss-120b",lambda request:
        httpx.Response(200, json={"choices":[{"finish_reason":"length","message":{"content":None}}]}))
    assert result.status == "FAILED"
    assert result.error_code == "EMPTY_OUTPUT_BUDGET"
    assert result.response is None


def test_provider_error_has_safe_status_without_upstream_body():
    result = run_with_mock("openrouter","test/free:free",lambda request:
        httpx.Response(403, json={"error":{"message":"secret fake-key leaked"}}))
    assert result.status == "FAILED"
    assert result.error_code == "HTTP_403"
    assert "secret fake-key" not in (result.error_message or "")


def test_catalog_excludes_non_chat_and_orders_reasoning_models_first():
    catalog = parse_chat_models("prov-groq", {"data":[
        {"id":"canopylabs/orpheus-arabic-saudi"},
        {"id":"nvidia/nemotron-3.5-content-safety"},
        {"id":"allam-2-7b"},
        {"id":"qwen/qwen3.8-27b","context_window":131072},
        {"id":"openai/gpt-oss-20b","context_window":131072},
        {"id":"openai/gpt-oss-120b","context_window":131072}
    ]})
    assert [model.id for model in catalog] == [
        "openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3.8-27b"
    ]
