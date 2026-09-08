"""Structured logging configuration and formatters."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict


# Patterns to redact sensitive data from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(authorization\s*:\s*Bearer\s+)[^\s",]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(api[_-]?key\s*[:=]\s*)[^\s",]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(password\s*[:=]\s*)[^\s",]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(token\s*[:=]\s*)[^\s",]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(postgres(?:ql)?://[^:]+:)[^@]+(@)', re.IGNORECASE), r'\1[REDACTED]\2'),
]


def redact_sensitive_data(message: str) -> str:
    """Scrub sensitive credentials and tokens from log messages."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class StructuredJSONFormatter(logging.Formatter):
    """JSON log formatter for production and machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_data(record.getMessage()),
        }

        # Include custom request attributes if present
        for attr in ("request_id", "http_method", "request_path", "status_code", "duration_ms"):
            val = getattr(record, attr, None)
            if val is not None:
                log_data[attr] = val

        if record.exc_info and record.exc_text:
            log_data["exception"] = redact_sensitive_data(record.exc_text)

        return json.dumps(log_data)


class DevelopmentFormatter(logging.Formatter):
    """Readable human-friendly formatter for development and testing."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        message = redact_sensitive_data(record.getMessage())

        # Include contextual details if present
        ctx_parts = []
        if getattr(record, "request_id", None):
            ctx_parts.append(f"req={record.request_id[:8]}")
        if getattr(record, "http_method", None) and getattr(record, "request_path", None):
            ctx_parts.append(f"{record.http_method} {record.request_path}")
        if getattr(record, "status_code", None) is not None:
            ctx_parts.append(f"status={record.status_code}")
        if getattr(record, "duration_ms", None) is not None:
            ctx_parts.append(f"{record.duration_ms:.2f}ms")

        context = f" [{', '.join(ctx_parts)}]" if ctx_parts else ""
        return f"[{timestamp}] [{record.levelname:<7}] [{record.name}]{context} {message}"


def setup_logging(log_level: str = "INFO", environment: str = "development") -> logging.Logger:
    """Configure structured logging for the application."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to prevent duplicate logs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if environment == "production":
        console_handler.setFormatter(StructuredJSONFormatter())
    else:
        console_handler.setFormatter(DevelopmentFormatter())

    root_logger.addHandler(console_handler)

    # Set external libraries to a quieter level
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    logger = logging.getLogger("verifai")
    logger.setLevel(numeric_level)
    return logger


logger = logging.getLogger("verifai")
