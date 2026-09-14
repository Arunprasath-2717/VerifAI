"""Tests for middleware stack: Security headers, CORS, timing, and log sanitization."""

import pytest
from httpx import AsyncClient
from app.core.logging import redact_sensitive_data


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """Verify defensive security headers on responses."""
    response = await client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-xss-protection"] == "1; mode=block"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers["permissions-policy"]
    assert headers["content-security-policy"] == "default-src 'self'"


@pytest.mark.asyncio
async def test_docs_security_headers_csp(client: AsyncClient):
    """Verify /docs endpoint receives relaxed CSP allowing CDN assets for Swagger UI."""
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "https://cdn.jsdelivr.net" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_request_id_and_timing_headers(client: AsyncClient):
    """Verify X-Request-ID and X-Response-Time headers."""
    # Without incoming X-Request-ID (generates one)
    response = await client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0
    assert "x-response-time" in response.headers
    assert response.headers["x-response-time"].endswith("ms")

    # With incoming custom X-Request-ID (propagates client ID)
    custom_id = "test-correlation-id-999"
    response_with_id = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response_with_id.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_cors_preflight(client: AsyncClient):
    """Verify CORS preflight headers for allowed origin."""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_log_sanitization():
    """Verify sensitive patterns are scrubbed from log strings."""
    raw_token = "User authorized with authorization: Bearer eyJhbGciOiJIUzI1NiJ9.secret"
    sanitized_token = redact_sensitive_data(raw_token)
    assert "eyJhbGciOiJIUzI1NiJ9" not in sanitized_token
    assert "[REDACTED]" in sanitized_token

    raw_pass = "Connection string postgresql://user:supersecretpass@db.supabase.co:5432/db"
    sanitized_pass = redact_sensitive_data(raw_pass)
    assert "supersecretpass" not in sanitized_pass
    assert "[REDACTED]" in sanitized_pass

    raw_api_key = "Connecting with api_key=ak_live_abcdef123456789"
    sanitized_api = redact_sensitive_data(raw_api_key)
    assert "ak_live_abcdef123456789" not in sanitized_api
    assert "[REDACTED]" in sanitized_api


def test_structured_json_formatter():
    """Verify production JSON log formatter outputs valid JSON with context attributes."""
    import json
    import logging
    from app.core.logging import StructuredJSONFormatter

    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="verifai.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test event with password=secret",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-12345"
    record.http_method = "GET"
    record.request_path = "/api/v1/health"
    record.status_code = 200
    record.duration_ms = 12.34

    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "verifai.test"
    assert parsed["request_id"] == "req-12345"
    assert parsed["http_method"] == "GET"
    assert parsed["request_path"] == "/api/v1/health"
    assert parsed["status_code"] == 200
    assert parsed["duration_ms"] == 12.34
    assert "[REDACTED]" in parsed["message"]
