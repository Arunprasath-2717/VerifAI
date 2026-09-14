"""Middleware stack: CORS, Security Headers, Request Logging, and Metrics Timing."""

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.metrics import metrics_collector

logger = logging.getLogger("verifai.request")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject defensive HTTP security headers into all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Apply Content-Security-Policy safely (accommodating Swagger/ReDoc CDNs on docs paths)
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class RequestLoggingAndMetricsMiddleware(BaseHTTPMiddleware):
    """Measure request duration, record operational metrics, and log structured request data."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Attach request_id to request state for access across handlers
        request.state.request_id = request_id

        metrics_collector.record_request_start()
        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            from app.core.errors import generic_exception_handler
            status_code = 500
            response = await generic_exception_handler(request, exc)
        finally:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            metrics_collector.record_request_end(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            # Structured request log without sensitive data
            logger.info(
                "%s %s -> %d (took %.2fms)",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "http_method": request.method,
                    "request_path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response


def configure_middleware(app, settings: Settings) -> None:
    """Register all middlewares in appropriate evaluation order."""
    # Starlette evaluates middleware in reverse of addition (onion model)
    # Logging/Timing -> Security Headers -> CORS -> App
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingAndMetricsMiddleware)
