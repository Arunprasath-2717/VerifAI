"""Middleware components for request correlation and lifecycle tracking."""

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_ctx

logger = logging.getLogger("app.middleware")

# Pattern for sanitizing client request IDs (alphanumeric, dashes, underscores <=64)
SAFE_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def sanitize_or_generate_request_id(raw_id: str | None) -> str:
    """Validate client-supplied request ID or generate a fresh UUID4 hex identifier.

    Rejects any IDs with control characters, whitespace, newlines, or excessive length
    to prevent log and header injection vulnerabilities.
    """
    if raw_id:
        clean_id = raw_id.strip()
        if SAFE_REQUEST_ID_PATTERN.match(clean_id):
            return clean_id
    return uuid.uuid4().hex


class RequestIDMiddleware:
    """Pure ASGI middleware managing correlation IDs and safe request logging."""

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.lower().encode("latin1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract client-supplied request ID header if present
        headers = dict(scope.get("headers", []))
        raw_header = headers.get(self.header_name_bytes, b"").decode("latin1")
        request_id = sanitize_or_generate_request_id(raw_header)

        # Store request_id in contextvar and request state
        token = request_id_ctx.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id

        start_time = time.perf_counter()
        method = scope.get("method", "GET")
        path = scope.get("path", "")
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                res_headers = MutableHeaders(scope=message)
                res_headers[self.header_name] = request_id
            await send(message)

        try:
            logger.info("Request started: %s %s", method, path)
            await self.app(scope, receive, send_wrapper)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Request completed: %s %s - status=%d duration=%.2fms",
                method,
                path,
                status_code,
                duration_ms,
            )
        finally:
            request_id_ctx.reset(token)
