"""Tests for structured logging, secret masking, and handler deduplication."""

import logging

from app.core.logging import (
    StructuredLogFormatter,
    get_current_request_id,
    mask_secrets,
    request_id_ctx,
    set_current_request_id,
    setup_logging,
)


def test_mask_secrets_database_credentials() -> None:
    """Verify that database connection URLs have passwords scrubbed."""
    raw = "Connecting to postgresql+asyncpg://postgres:superSecretPass123@localhost:5432/verifai"
    masked = mask_secrets(raw)
    assert "superSecretPass123" not in masked
    assert "postgresql+asyncpg://postgres:***@localhost:5432/verifai" in masked


def test_mask_secrets_bearer_and_basic_tokens() -> None:
    """Verify that Bearer and Basic authentication headers are redacted."""
    bearer_msg = "Header Authorization: Bearer secret_jwt_token_value_abc123"
    assert "secret_jwt_token_value_abc123" not in mask_secrets(bearer_msg)
    assert "Bearer [REDACTED]" in mask_secrets(bearer_msg)

    basic_msg = "Header Authorization: Basic dXNlcjpwYXNzd29yZA=="
    assert "dXNlcjpwYXNzd29yZA==" not in mask_secrets(basic_msg)
    assert "Basic [REDACTED]" in mask_secrets(basic_msg)


def test_mask_secrets_key_value_assignments() -> None:
    """Verify sensitive key-value pairs (password, token, api_key) are redacted."""
    msg = 'User login with password="mySecretPassword!" and token=abc987654321'
    masked = mask_secrets(msg)
    assert "mySecretPassword!" not in masked
    assert "abc987654321" not in masked
    assert 'password="***"' in masked
    assert "token=***" in masked


def test_structured_log_formatter_includes_required_fields() -> None:
    """Verify log record includes ISO 8601 timestamp, level, name, request_id, msg."""
    fmt = (
        "%(asctime)s [%(levelname)s] [%(name)s] [request_id=%(request_id)s] %(message)s"
    )
    formatter = StructuredLogFormatter(fmt=fmt)
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test event message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "[INFO]" in formatted
    assert "[app.test]" in formatted
    assert "[request_id=-]" in formatted
    assert "Test event message" in formatted
    # Timestamp verification: ISO 8601 Zulu format YYYY-MM-DDTHH:MM:SSZ
    assert "T" in formatted.split()[0]
    assert formatted.split()[0].endswith("Z")


def test_structured_log_formatter_uses_context_request_id() -> None:
    """Verify formatter pulls active request ID from contextvar."""
    fmt = (
        "%(asctime)s [%(levelname)s] [%(name)s] [request_id=%(request_id)s] %(message)s"
    )
    formatter = StructuredLogFormatter(fmt=fmt)
    token = set_current_request_id("corr-abc-123")
    try:
        assert get_current_request_id() == "corr-abc-123"
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=20,
            msg="Contextual event",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "[request_id=corr-abc-123]" in formatted
    finally:
        request_id_ctx.reset(token)

    assert get_current_request_id() is None


def test_setup_logging_idempotency_prevents_duplicate_handlers() -> None:
    """Verify setup_logging does not duplicate handlers when invoked repeatedly."""
    setup_logging(log_level="INFO", force=True)
    root = logging.getLogger()
    initial_count = len(root.handlers)
    assert initial_count >= 1

    # Call repeatedly without force
    setup_logging(log_level="INFO", force=False)
    setup_logging(log_level="INFO", force=False)
    assert len(root.handlers) == initial_count

    # Call with force=True should reset rather than accumulate
    setup_logging(log_level="DEBUG", force=True)
    assert len(root.handlers) == 1
    assert root.level == logging.DEBUG
