"""Tests for backend configuration loading and validation."""

import os

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_settings() -> None:
    """Verify default configuration values."""
    settings = Settings()
    assert settings.PROJECT_NAME == "VerifAI"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT in ["development", "production", "testing"]
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)


def test_environment_override() -> None:
    """Verify that environment variables override defaults."""
    os.environ["PROJECT_NAME"] = "VerifAI Custom"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    try:
        settings = Settings()
        assert settings.PROJECT_NAME == "VerifAI Custom"
        assert settings.ENVIRONMENT == "testing"
        assert settings.DEBUG is True
    finally:
        os.environ.pop("PROJECT_NAME", None)
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("DEBUG", None)


def test_invalid_environment_negative_control() -> None:
    """Negative control: Verify invalid environment setting raises validation error."""
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="invalid_env_name")  # type: ignore[arg-type]
