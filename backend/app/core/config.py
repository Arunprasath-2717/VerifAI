"""Environment-driven configuration for VerifAI backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaults."""

    # Project Metadata
    PROJECT_NAME: str = "VerifAI"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "VerifAI — Cross-Generation Consistency Hallucination Risk Analysis Engine"
    )
    API_V1_STR: str = "/api/v1"

    # Environment & Debugging
    ENVIRONMENT: Literal["development", "test", "testing", "staging", "production"] = (
        "development"
    )
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Request & Correlation Tracking
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # CORS Configuration
    # NOTE: Default origins are strictly for local development and must be
    # explicitly overridden in production.
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # Database Configuration (PostgreSQL + asyncpg)
    # Using SecretStr ensures credentials are never leaked in repr, str, or logs
    DATABASE_URL: SecretStr | None = None
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_CONNECT_TIMEOUT: float = 3.0

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize and validate log level against standard Python levels."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.strip().upper()
        if upper_v not in allowed:
            raise ValueError(
                f"Invalid LOG_LEVEL '{v}'. Must be one of: {', '.join(sorted(allowed))}"
            )
        return upper_v

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins for security compliance."""
        if not v:
            return []
        return [origin.rstrip("/") for origin in v]

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: SecretStr | None) -> SecretStr | None:
        """Validate that database URL uses asynchronous asyncpg driver."""
        if v is None:
            return None
        secret_val = v.get_secret_value()
        allowed_schemes = ("postgresql+asyncpg://", "sqlite+aiosqlite://")
        if not any(secret_val.startswith(scheme) for scheme in allowed_schemes):
            raise ValueError(
                "DATABASE_URL must use an asynchronous driver "
                "(e.g. postgresql+asyncpg://...)"
            )
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings instance to enable deterministic test isolation."""
    get_settings.cache_clear()
