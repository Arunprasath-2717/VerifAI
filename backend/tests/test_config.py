"""Tests for environment configuration and production safeguards."""

import pytest
from app.core.config import Settings


def test_development_config():
    """Verify default development configuration."""
    settings = Settings(ENVIRONMENT="development")
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True
    assert len(settings.CORS_ORIGINS) > 0


def test_testing_config():
    """Verify testing configuration forces DEBUG=False."""
    settings = Settings(ENVIRONMENT="testing", DEBUG=True)
    assert settings.ENVIRONMENT == "testing"
    assert settings.DEBUG is False


def test_production_safety_blocks_debug():
    """Verify production settings fail if DEBUG=True."""
    with pytest.raises(ValueError, match="DEBUG must be False in production"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            DATABASE_URL="postgresql://user:pass@remote.supabase.co:5432/verifai",
            CORS_ORIGINS=["https://verifai.app"],
        )


def test_production_safety_blocks_localhost_database():
    """Verify production settings fail if DATABASE_URL points to localhost."""
    with pytest.raises(ValueError, match="Valid remote DATABASE_URL is required"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://user:pass@localhost:5432/verifai",
            CORS_ORIGINS=["https://verifai.app"],
        )


def test_production_safety_blocks_wildcard_cors():
    """Verify production settings reject wildcard CORS."""
    with pytest.raises(ValueError, match="Wildcard CORS"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://user:pass@remote.supabase.co:5432/verifai",
            CORS_ORIGINS=["*"],
        )


def test_production_valid_configuration():
    """Verify valid production settings initialize cleanly."""
    settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        DATABASE_URL="postgresql://user:pass@remote.supabase.co:5432/verifai",
        CORS_ORIGINS=["https://verifai.app"],
        LOG_LEVEL="INFO",
    )
    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False


def test_cors_origins_parsing():
    """Verify string parsing of comma-separated CORS origins."""
    settings = Settings(CORS_ORIGINS="https://app.example.com, https://admin.example.com")
    assert "https://app.example.com" in settings.CORS_ORIGINS
    assert "https://admin.example.com" in settings.CORS_ORIGINS


def test_invalid_log_level():
    """Verify invalid log level raises ValueError."""
    with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
        Settings(LOG_LEVEL="SUPER_VERBOSE")
