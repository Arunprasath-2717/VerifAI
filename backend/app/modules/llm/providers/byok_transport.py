"""MockTransport seam for isolated provider integration tests only.

Production requests use the standard HTTPS transport. Never put credentials
in logs, mocks, or frontend HTTP responses.
"""

from contextvars import ContextVar

import httpx

CHAT_PROVIDER_TRANSPORT: ContextVar[httpx.AsyncBaseTransport | None] = ContextVar(
    "byok_provider_transport", default=None
)
