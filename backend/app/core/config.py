"""Application configuration module using Pydantic Settings."""

from functools import lru_cache
from typing import List, Literal, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-specific validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "VerifAI API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Database configuration (PostgreSQL / Supabase)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/verifai"
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 5
    DB_TIMEOUT: float = 5.0

    # Supabase Auth configuration
    SUPABASE_URL: str = "https://mock-supabase-project.supabase.co"
    SUPABASE_ANON_KEY: str = "mock-supabase-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "mock-supabase-service-role-key"

    # Verification engine configuration
    # Set GEMINI_API_KEY to enable LLM-based extraction, classification, and judging.
    # When absent or 'mock', the engine degrades gracefully (UNKNOWN verdicts).
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    # Max web sources fetched per claim during search
    ENGINE_MAX_SOURCES_PER_CLAIM: int = 5

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[List[str], str]) -> List[str]:
        """Parse comma-separated strings or string lists into a cleaned list."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Ensure valid log level string."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper().strip()
        if upper not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL '{value}'. Must be one of: {', '.join(valid_levels)}")
        return upper

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        """Enforce strict production safeguards."""
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("Production safety violation: DEBUG must be False in production.")
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError(
                    "Production safety violation: Valid remote DATABASE_URL is required in production."
                )
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Production safety violation: Wildcard CORS ('*') is not allowed in production."
                )
            if not self.SUPABASE_URL or "mock" in self.SUPABASE_URL:
                raise ValueError(
                    "Production safety violation: Valid SUPABASE_URL is required in production."
                )
            if not self.SUPABASE_ANON_KEY or "mock" in self.SUPABASE_ANON_KEY:
                raise ValueError(
                    "Production safety violation: Valid SUPABASE_ANON_KEY is required in production."
                )
        elif self.ENVIRONMENT == "testing":
            # Testing defaults
            self.DEBUG = False
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
