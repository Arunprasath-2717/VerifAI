"""Structured logging configuration for VerifAI backend."""

import contextvars
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

# ContextVar for propagating request/correlation ID across async execution flows
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_current_request_id() -> str | None:
    """Retrieve the active request correlation ID from context."""
    return request_id_ctx.get()


def set_current_request_id(request_id: str | None) -> contextvars.Token[Any]:
    """Set the active request correlation ID in context and return reset token."""
    return request_id_ctx.set(request_id)


# Compiled regex patterns for secret redaction in log messages
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Database connection strings with passwords: scheme://user:pass@host
    (re.compile(r"([a-zA-Z+]+://[^:]+:)([^@]+)(@)"), r"\g<1>***\g<3>"),
    # Bearer and Basic authentication tokens
    (
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        r"\g<1>[REDACTED]",
    ),
    (re.compile(r"(Basic\s+)[A-Za-z0-9+/=]+", re.IGNORECASE), r"\g<1>[REDACTED]"),
    # Common sensitive key-value pairs (password, secret, token, api_key, etc.)
    (
        re.compile(
            r'(?i)\b(password|secret|token|api_key|access_token|private_key)\b\s*([:=])\s*(["\']?)([^"\'\s,]+)\3'
        ),
        r"\1\2\3***\3",
    ),
]


def mask_secrets(text: str) -> str:
    """Scrub known secret and credential patterns from text before emission."""
    if not text:
        return text
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class StructuredLogFormatter(logging.Formatter):
    """Structured log formatter with ISO 8601 UTC timestamps and request correlation."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format timestamp in ISO 8601 UTC format."""
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        return dt.strftime(datefmt or "%Y-%m-%dT%H:%M:%SZ")

    def format(self, record: logging.LogRecord) -> str:
        """Inject request ID, format message, and scrub any sensitive tokens."""
        if not hasattr(record, "request_id") or not record.request_id:
            record.request_id = get_current_request_id() or "-"

        formatted = super().format(record)
        return mask_secrets(formatted)


_logging_configured = False


def setup_logging(log_level: str = "INFO", force: bool = False) -> logging.Logger:
    """Configure centralized application logging idempotently.

    Clears existing root and application handlers on initial or forced setup
    to prevent duplicate log records upon repeated application imports or calls.
    """
    global _logging_configured
    if _logging_configured and not force:
        return logging.getLogger("app")

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers from root logger to prevent duplicate handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    formatter = StructuredLogFormatter(
        fmt=(
            "%(asctime)s [%(levelname)s] [%(name)s] [request_id=%(request_id)s]"
            " %(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Align standard Uvicorn and FastAPI loggers with application formatting
    for name in ("app", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        log = logging.getLogger(name)
        log.setLevel(level)
        for h in list(log.handlers):
            log.removeHandler(h)
        log.propagate = True

    _logging_configured = True
    return logging.getLogger("app")
