"""Global exception handlers for standardizing API error responses."""

import logging
from typing import Any, Dict, List
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("verifai.errors")


def _format_http_error_type(status_code: int) -> str:
    """Derive standard machine-readable error type from HTTP status code."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard FastAPI/Starlette HTTPExceptions."""
    error_type = _format_http_error_type(exc.status_code)
    message = str(exc.detail) if exc.detail else "An HTTP error occurred"
    details: Dict[str, Any] = {}

    # If detail was passed as a dict, extract type/details
    if isinstance(exc.detail, dict):
        error_type = exc.detail.get("type", error_type)
        message = exc.detail.get("message", message)
        details = exc.detail.get("details", {})

    logger.warning(
        "HTTP exception: %s %s -> status=%d type=%s message=%s",
        request.method,
        request.url.path,
        exc.status_code,
        error_type,
        message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "details": details,
            },
        },
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors (HTTP 422)."""
    formatted_errors: List[Dict[str, Any]] = []

    for err in exc.errors():
        loc = err.get("loc", ())
        field_path = " -> ".join(str(item) for item in loc if item != "body") or "body"
        formatted_errors.append(
            {
                "field": field_path,
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )

    logger.info(
        "Validation error: %s %s -> %d field errors",
        request.method,
        request.url.path,
        len(formatted_errors),
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "type": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": formatted_errors,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled unexpected exceptions (HTTP 500).

    Never exposes stack traces or sensitive internal paths to the client.
    """
    logger.exception(
        "Unhandled exception processing %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": {},
            },
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all global error handlers on the FastAPI application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(500, generic_exception_handler)
