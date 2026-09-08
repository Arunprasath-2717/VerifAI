"""Tests for global error handling, validation, and production error safety."""

import pytest
from fastapi import APIRouter, HTTPException
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_not_found_handling(client: AsyncClient):
    """Verify 404 responses conform to standard error format."""
    response = await client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "NOT_FOUND"
    assert "Not Found" in body["error"]["message"]


@pytest.mark.asyncio
async def test_validation_endpoint_success(client: AsyncClient):
    """Verify valid request to test-validation returns 200."""
    response = await client.post(
        "/api/v1/test-validation",
        json={"name": "Valid Test", "score": 85.5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["echo_name"] == "Valid Test"
    assert body["data"]["echo_score"] == 85.5


@pytest.mark.asyncio
async def test_validation_error_missing_fields(client: AsyncClient):
    """Verify missing required fields return 422 with standard format."""
    response = await client.post("/api/v1/test-validation", json={})
    assert response.status_code == 422
    body = response.json()

    assert body["success"] is False
    assert body["error"]["type"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    details = body["error"]["details"]
    assert isinstance(details, list)
    field_names = [d["field"] for d in details]
    assert "name" in field_names
    assert "score" in field_names


@pytest.mark.asyncio
async def test_validation_error_invalid_types(client: AsyncClient):
    """Verify out-of-range or invalid types return 422 with field paths."""
    response = await client.post(
        "/api/v1/test-validation",
        json={"name": "A", "score": 999.0},  # name too short (<2), score > 100
    )
    assert response.status_code == 422
    body = response.json()
    details = body["error"]["details"]
    assert any("name" in d["field"] for d in details)
    assert any("score" in d["field"] for d in details)


@pytest.mark.asyncio
async def test_unhandled_exception_no_stack_trace_leak(app, client: AsyncClient):
    """Verify unhandled exceptions return 500 without leaking stack traces or internal secrets."""
    test_router = APIRouter()

    @test_router.get("/test-internal-crash")
    async def crash_endpoint():
        raise RuntimeError("Secret credentials and internal system traceback details")

    app.include_router(test_router)

    response = await client.get("/test-internal-crash")
    assert response.status_code == 500

    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"] == "An internal server error occurred"
    # Ensure sensitive internal error message and stack trace are NEVER returned in response
    assert "Secret credentials" not in str(body)
    assert "traceback" not in str(body).lower()
    assert "RuntimeError" not in str(body)


@pytest.mark.asyncio
async def test_custom_http_exception(app, client: AsyncClient):
    """Verify custom HTTPException with dict details formats properly."""
    test_router = APIRouter()

    @test_router.get("/test-forbidden")
    async def forbidden_endpoint():
        raise HTTPException(
            status_code=403,
            detail={"type": "ACCESS_DENIED", "message": "You cannot access this resource", "details": {"reason": "test"}},
        )

    app.include_router(test_router)

    response = await client.get("/test-forbidden")
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "ACCESS_DENIED"
    assert body["error"]["message"] == "You cannot access this resource"
    assert body["error"]["details"]["reason"] == "test"
