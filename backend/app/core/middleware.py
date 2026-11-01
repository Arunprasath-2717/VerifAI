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

# Response headers applied to every HTTP response. The API serves JSON only, so
# a fully locked-down CSP is correct here; the browser SPA sets its own policy.
API_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cache-Control": "no-store",
}
HSTS_HEADER = "max-age=31536000; includeSubDomains"


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
    """Pure ASGI middleware: correlation IDs, body-size limit, security headers."""

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        max_body_bytes: int = 0,
        enable_hsts: bool = False,
    ) -> None:
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.lower().encode("latin1")
        # 0 disables the limit. Otherwise bodies over this many bytes get 413,
        # whether or not the client declared a Content-Length.
        self.max_body_bytes = max_body_bytes
        self.enable_hsts = enable_hsts

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

        # Enforce the body cap before the application sees the request. A declared
        # oversize body is rejected immediately; an undeclared (streamed) body is
        # buffered up to the cap, so the app never parses a truncated body.
        if self.max_body_bytes:
            declared = _declared_content_length(headers)
            if declared is not None and declared > self.max_body_bytes:
                await self._send_too_large(scope, receive, send, request_id)
                request_id_ctx.reset(token)
                return
            buffered = await self._buffer_within_limit(receive)
            if buffered is None:
                await self._send_too_large(scope, receive, send, request_id)
                request_id_ctx.reset(token)
                return
            receive = _replay_receive(buffered)

        start_time = time.perf_counter()
        method = scope.get("method", "GET")
        path = scope.get("path", "")
        status_code = 500
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message.get("status", 200)
                res_headers = MutableHeaders(scope=message)
                res_headers[self.header_name] = request_id
                for name, value in API_SECURITY_HEADERS.items():
                    res_headers.setdefault(name, value)
                if self.enable_hsts:
                    res_headers.setdefault("Strict-Transport-Security", HSTS_HEADER)
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

    async def _buffer_within_limit(self, receive: Receive) -> list[Message] | None:
        """Read the whole request body up to the cap. None means it overflowed."""
        messages: list[Message] = []
        received = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                messages.append(message)
                return messages
            chunk = message.get("body", b"")
            received += len(chunk)
            if received > self.max_body_bytes:
                return None
            messages.append(message)
            if not message.get("more_body", False):
                return messages

    async def _send_too_large(
        self, scope: Scope, receive: Receive, send: Send, request_id: str
    ) -> None:
        from app.core.errors import create_error_response

        response = create_error_response(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=(
                "Request payload exceeds maximum allowed size of "
                f"{self.max_body_bytes} bytes."
            ),
            request_id=request_id,
            header_name=self.header_name,
            headers={"Connection": "close"},
        )
        await response(scope, receive, send)


def _replay_receive(messages: list[Message]) -> Receive:
    """Serve the already-buffered request messages to the application in order."""
    queue = list(messages)

    async def replay() -> Message:
        if queue:
            return queue.pop(0)
        # Body fully delivered; further reads wait for disconnect semantics.
        return {"type": "http.disconnect"}

    return replay


def _declared_content_length(headers: dict[bytes, bytes]) -> int | None:
    raw = headers.get(b"content-length")
    if raw is None:
        return None
    try:
        return int(raw.decode("latin1"))
    except ValueError:
        return None
