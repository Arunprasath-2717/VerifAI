"""Middleware components for request correlation and lifecycle tracking."""

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import create_error_response
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


class BodySizeLimitMiddleware:
    """Reject request bodies larger than ``max_bytes`` before they are parsed.

    Oversized ``Content-Length`` headers are refused immediately; bodies without
    a length (chunked transfer) are counted as they stream and cut off once they
    cross the limit, answered with the same HTTP 413.
    """

    def __init__(
        self, app: ASGIApp, max_bytes: int, header_name: str = "X-Request-ID"
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self.max_bytes <= 0:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        declared = headers.get(b"content-length")
        if declared is not None:
            try:
                too_large = int(declared) > self.max_bytes
            except ValueError:
                too_large = False
            if too_large:
                await self._reject(scope, receive, send)
                return

        received = 0
        overflowed = False
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received, overflowed
            if overflowed:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    # Stop feeding the app; it sees a disconnect and whatever it
                    # responds with is replaced by the 413 below.
                    overflowed = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if overflowed:
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not overflowed:
                raise
        if overflowed and not response_started:
            await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = create_error_response(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=f"Request body exceeds the {self.max_bytes}-byte limit.",
            request_id=scope.get("state", {}).get("request_id"),
            header_name=self.header_name,
        )
        await response(scope, receive, send)
