"""Tests for request/correlation ID middleware behavior."""

import re

from starlette.testclient import TestClient

from app.core.logging import get_current_request_id
from app.core.middleware import sanitize_or_generate_request_id


def test_sanitize_or_generate_request_id_valid() -> None:
    """Verify valid client-provided IDs are preserved."""
    assert sanitize_or_generate_request_id("my-req-123") == "my-req-123"
    assert sanitize_or_generate_request_id("req_abc_DEF_012") == "req_abc_DEF_012"


def test_sanitize_or_generate_request_id_sanitizes_malicious_inputs() -> None:
    """Verify invalid inputs are rejected and replaced with valid UUID4 hex."""
    # Carriage return / newline header injection attempt
    injected = "req-123\r\nSet-Cookie: stolen=true"
    result = sanitize_or_generate_request_id(injected)
    assert result != injected
    assert re.match(r"^[0-9a-f]{32}$", result)

    # Overly long string (>64 chars)
    too_long = "a" * 128
    result_long = sanitize_or_generate_request_id(too_long)
    assert result_long != too_long
    assert re.match(r"^[0-9a-f]{32}$", result_long)

    # None or empty string
    assert re.match(r"^[0-9a-f]{32}$", sanitize_or_generate_request_id(None))
    assert re.match(r"^[0-9a-f]{32}$", sanitize_or_generate_request_id(""))


def test_request_id_generated_when_header_absent(client: TestClient) -> None:
    """Verify request ID is generated in header when client does not supply one."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    header_val = response.headers["x-request-id"]
    assert re.match(r"^[0-9a-f]{32}$", header_val)


def test_request_id_propagated_when_header_supplied(client: TestClient) -> None:
    """Verify client-supplied valid request ID is preserved in response header."""
    custom_id = "client-trace-id-998877"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


def test_request_id_present_on_not_found_error_response(client: TestClient) -> None:
    """Verify request ID header is returned on 404 responses."""
    response = client.get("/api/v1/unmapped-endpoint")
    assert response.status_code == 404
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["error"]["request_id"] == response.headers["x-request-id"]


def test_request_id_present_on_method_not_allowed_error_response(
    client: TestClient,
) -> None:
    """Verify request ID header is returned on 405 responses."""
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert "x-request-id" in response.headers
    data = response.json()
    assert data["error"]["request_id"] == response.headers["x-request-id"]


def test_request_id_context_cleaned_up_after_request(client: TestClient) -> None:
    """Verify contextvar is cleaned up after request completes."""
    client.get("/api/v1/health")
    # Outside active request lifecycle, context request_id must be None
    assert get_current_request_id() is None
