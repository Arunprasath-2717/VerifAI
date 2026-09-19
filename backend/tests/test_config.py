"""Tests for backend configuration loading and validation."""

import os

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_settings() -> None:
    """Verify default configuration values."""
    settings = Settings()
    assert settings.PROJECT_NAME == "VerifAI"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT in [
        "development",
        "production",
        "testing",
        "test",
        "staging",
    ]
    assert settings.LOG_LEVEL == "INFO"
    assert settings.REQUEST_ID_HEADER == "X-Request-ID"
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)


def test_environment_override() -> None:
    """Verify that environment variables override defaults."""
    os.environ["PROJECT_NAME"] = "VerifAI Custom"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "debug"
    os.environ["REQUEST_ID_HEADER"] = "X-Correlation-ID"
    try:
        settings = Settings()
        assert settings.PROJECT_NAME == "VerifAI Custom"
        assert settings.ENVIRONMENT == "testing"
        assert settings.DEBUG is True
        assert settings.LOG_LEVEL == "DEBUG"  # Normalized to uppercase
        assert settings.REQUEST_ID_HEADER == "X-Correlation-ID"
    finally:
        os.environ.pop("PROJECT_NAME", None)
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("DEBUG", None)
        os.environ.pop("LOG_LEVEL", None)
        os.environ.pop("REQUEST_ID_HEADER", None)


def test_invalid_environment_negative_control() -> None:
    """Negative control: Verify invalid environment setting raises validation error."""
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="invalid_env_name")  # type: ignore[arg-type]


def test_invalid_log_level_negative_control() -> None:
    """Negative control: Verify invalid log level raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(LOG_LEVEL="TRACE")
    assert "Invalid LOG_LEVEL" in str(exc_info.value)


def test_clear_settings_cache() -> None:
    """Verify that clear_settings_cache resets the lru_cache."""
    from app.core.config import clear_settings_cache, get_settings

    s1 = get_settings()
    clear_settings_cache()
    s2 = get_settings()
    assert s1 is not s2
    assert s1.PROJECT_NAME == s2.PROJECT_NAME
