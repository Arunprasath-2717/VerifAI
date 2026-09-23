"""Consistent API error models, application exceptions, and exception handlers."""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_current_request_id

logger = logging.getLogger("app.errors")

# Mapping of standard HTTP status codes to stable error code strings
STATUS_CODE_TO_ERROR_CODE: dict[int, str] = {
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


class AppError(Exception):
    """Base application exception for handled operational errors."""

    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class BadRequestError(AppError):
    """Malformed or invalid request exception."""

    def __init__(self, message: str = "Bad request", details: Any = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ServiceUnavailableError(AppError):
    """Service or upstream dependency unavailable exception."""

    def __init__(self, message: str = "Service unavailable", details: Any = None):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None = None,
    details: Any = None,
    headers: Mapping[str, str] | None = None,
    header_name: str = "X-Request-ID",
) -> JSONResponse:
    """Build standardized JSON error response with correlation header."""
    req_id = request_id or get_current_request_id() or "-"
    response_headers = dict(headers or {})
    response_headers[header_name] = req_id

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": req_id,
                "details": details,
            }
        },
        headers=response_headers,
    )


async def app_error_handler(
    request: Request, exc: AppError, header_name: str = "X-Request-ID"
) -> JSONResponse:
    """Handle custom application-level exceptions."""
    req_id = getattr(request.state, "request_id", None) or get_current_request_id()
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=req_id,
        details=exc.details,
        header_name=header_name,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
    header_name: str = "X-Request-ID",
) -> JSONResponse:
    """Handle Starlette and FastAPI HTTP exceptions with stable codes."""
    req_id = getattr(request.state, "request_id", None) or get_current_request_id()
    code = STATUS_CODE_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if exc.detail else "An HTTP error occurred."
    return create_error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        request_id=req_id,
        details=None,
        headers=exc.headers,
        header_name=header_name,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
    header_name: str = "X-Request-ID",
) -> JSONResponse:
    """Handle FastAPI request validation errors safely.

    Sanitizes validation errors by preserving field locations, messages, and types,
    while omitting raw input values that may contain passwords or tokens.
    """
    req_id = getattr(request.state, "request_id", None) or get_current_request_id()
    sanitized_errors = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", [])]
        sanitized_errors.append(
            {
                "location": loc,
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        request_id=req_id,
        details=sanitized_errors,
        header_name=header_name,
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception, header_name: str = "X-Request-ID"
) -> JSONResponse:
    """Handle unexpected server exceptions safely without leaking internals.

    Logs traceback server-side with request correlation; returns a generic 500 error.
    """
    req_id = getattr(request.state, "request_id", None) or get_current_request_id()
    logger.exception(
        "Unhandled server exception during %s %s [request_id=%s]: %s",
        request.method,
        request.url.path,
        req_id,
        str(exc),
    )
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal error occurred.",
        request_id=req_id,
        details=None,
        header_name=header_name,
    )


def register_error_handlers(app: FastAPI, header_name: str = "X-Request-ID") -> None:
    """Register standardized error handlers with the FastAPI application."""

    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return await app_error_handler(request, exc, header_name=header_name)

    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return await http_exception_handler(request, exc, header_name=header_name)

    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return await validation_exception_handler(request, exc, header_name=header_name)

    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return await unhandled_exception_handler(request, exc, header_name=header_name)

    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)  # type: ignore[arg-type]
