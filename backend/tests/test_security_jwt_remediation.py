"""Security regression tests for JWT configuration, secret validation, and production invariants."""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import INSECURE_DEV_JWT_SECRET, Settings
from app.core.security import create_access_token, decode_access_token
from app.schemas.auth import UserRole


class TestSecurityJWTRemediation:
    """Regression suite for VERIFAI-FIND-001 and VERIFAI-FIND-003."""

    def test_production_missing_or_default_secret_raises_validation_error(self) -> None:
        """Verify production environment fails closed when JWT_SECRET is default or missing."""
        # Case A: Default dev secret in production
        with pytest.raises(ValidationError) as exc_info:
            Settings(ENVIRONMENT="production")
        err_msg = str(exc_info.value)
        assert (
            "Default development JWT_SECRET is strictly forbidden in 'production'"
            in err_msg
        )

        # Case B: Staging environment also fails closed
        with pytest.raises(ValidationError) as exc_info_staging:
            Settings(ENVIRONMENT="staging")
        assert (
            "Default development JWT_SECRET is strictly forbidden in 'staging'"
            in str(exc_info_staging.value)
        )

    def test_production_empty_secret_raises_validation_error(self) -> None:
        """Verify production environment fails closed if JWT_SECRET is empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(ENVIRONMENT="production", JWT_SECRET=SecretStr(""))
        assert "JWT_SECRET must be configured and non-empty" in str(exc_info.value)

    def test_production_short_secret_raises_validation_error(self) -> None:
        """Verify production environment requires high-entropy secret (>=32 characters)."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET=SecretStr("short_key_under_32_characters"),
            )
        assert "JWT_SECRET must be at least 32 characters long" in str(exc_info.value)

    def test_production_valid_secret_succeeds(self) -> None:
        """Verify production environment succeeds with compliant 32+ character secret."""
        strong_secret = "c2VjdXJlX3JhbmRvbV9wcm9kdWN0aW9uX2tleV8zMl9jaGFyc19taW4h"
        settings = Settings(
            ENVIRONMENT="production", JWT_SECRET=SecretStr(strong_secret)
        )
        assert settings.ENVIRONMENT == "production"
        assert settings.JWT_SECRET.get_secret_value() == strong_secret

    def test_development_default_secret_functional(self) -> None:
        """Verify development and test environments permit the default development secret."""
        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.ENVIRONMENT == "development"
        assert dev_settings.JWT_SECRET.get_secret_value() == INSECURE_DEV_JWT_SECRET

        test_settings = Settings(ENVIRONMENT="test")
        assert test_settings.ENVIRONMENT == "test"
        assert test_settings.JWT_SECRET.get_secret_value() == INSECURE_DEV_JWT_SECRET

    def test_jwt_signing_and_verification_cycle(self) -> None:
        """Verify tokens created with Settings are correctly verified by decode_access_token."""
        strong_secret = "custom_production_secret_key_exceeding_32_bytes_length!"
        settings = Settings(
            ENVIRONMENT="production", JWT_SECRET=SecretStr(strong_secret)
        )

        token, expires_in = create_access_token(
            subject="test-user-uuid-1234",
            role=UserRole.USER,
            settings=settings,
        )
        assert isinstance(token, str)
        assert expires_in > 0

        decoded = decode_access_token(token, settings=settings)
        assert decoded["sub"] == "test-user-uuid-1234"
        assert decoded["role"] == "USER"
        assert decoded["iss"] == settings.JWT_ISSUER
        assert decoded["aud"] == settings.JWT_AUDIENCE

    def test_obsolete_jwt_secret_key_not_read_by_settings(self) -> None:
        """Verify the obsolete JWT_SECRET_KEY env variable is not silently used instead of JWT_SECRET."""
        with patch.dict(
            os.environ, {"JWT_SECRET_KEY": "some_obsolete_env_var_value"}, clear=False
        ):
            # When JWT_SECRET is not provided, settings must use its canonical default, NOT JWT_SECRET_KEY
            settings = Settings(ENVIRONMENT="development")
            assert settings.JWT_SECRET.get_secret_value() == INSECURE_DEV_JWT_SECRET
