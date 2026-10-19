"""Environment-driven configuration for VerifAI backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_JWT_SECRET: str = (
    "verifai_insecure_development_secret_key_change_in_production_32chars!"
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaults."""

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

    # ===========================================================================
    # Database Configuration (PostgreSQL + asyncpg)
    # Using SecretStr ensures credentials are never leaked in repr, str, or logs.
    # DATABASE_URL is REQUIRED at startup — there is no in-memory fallback.
    # ===========================================================================
    DATABASE_URL: SecretStr | None = None
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_CONNECT_TIMEOUT: float = 3.0

    # ===========================================================================
    # Authentication — Firebase Auth (RS256 via Google JWKS)
    # ===========================================================================
    FIREBASE_AUTH_ENABLED: bool = True
    FIREBASE_API_KEY: str = "AIzaSyDag7_lFm6ayphrJUDYWK2EQmZmFdaU_5s"
    FIREBASE_PROJECT_ID: str = "verifai-22c4b"
    FIREBASE_AUTH_DOMAIN: str = "verifai-22c4b.firebaseapp.com"
    FIREBASE_STORAGE_BUCKET: str = "verifai-22c4b.firebasestorage.app"
    FIREBASE_MESSAGING_SENDER_ID: str = "501647364420"
    FIREBASE_APP_ID: str = "1:501647364420:web:9848f5dc7ba7d236704711"
    FIREBASE_MEASUREMENT_ID: str = "G-4LPP8CZGG3"

    # ===========================================================================
    # Legal & Compliance Configuration
    # Authoritative versions and effective dates for Terms & Privacy Policy
    # ===========================================================================
    TERMS_VERSION: str = "2026.1"
    PRIVACY_POLICY_VERSION: str = "2026.1"
    TERMS_EFFECTIVE_DATE: str = "October 10, 2026"
    PRIVACY_EFFECTIVE_DATE: str = "October 10, 2026"
    LEGAL_CONTACT_EMAIL: str = "[CONFIGURED_LEGAL_CONTACT_EMAIL]"
    GOVERNING_LAW: str = "[CONFIGURED_GOVERNING_JURISDICTION_PLACEHOLDER]"
    MINIMUM_AGE_REQUIREMENT: str = "[CONFIGURED_MINIMUM_AGE_PLACEHOLDER]"

    # Internal JWT for session tokens issued after Firebase verification
    # NOTE: These are VerifAI-issued session tokens, NOT Firebase tokens.
    JWT_SECRET: SecretStr = Field(
        default=SecretStr(INSECURE_DEV_JWT_SECRET),
        description=(
            "Secret key for signing session JWT tokens. "
            "Must be overridden in production with a high-entropy secret (>=32 chars)."
        ),
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "verifai-backend"
    JWT_AUDIENCE: str = "verifai-client"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Trusted Reverse Proxy IP Configuration
    FORWARDED_ALLOW_IPS: list[str] = Field(
        default_factory=list,
        description=(
            "List of trusted reverse proxy IP addresses or CIDR blocks. "
            "If empty, X-Forwarded-For headers are ignored and socket IP is used."
        ),
    )

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_ENABLED_IN_TEST: bool = False
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 5
    RATE_LIMIT_VERIFY_PER_MINUTE: int = 30
    RATE_LIMIT_KB_UPLOAD_PER_MINUTE: int = 20
    RATE_LIMIT_KB_SEARCH_PER_MINUTE: int = 40

    # Resource Concurrency Controls
    MAX_CONCURRENT_VERIFICATIONS_PER_USER: int = 3

    # Verification Engine Configuration
    VERIFICATION_MAX_INPUT_CHARS: int = 20000
    VERIFICATION_MAX_CLAIMS: int = 20
    RETRIEVAL_TIMEOUT_SECONDS: float = 8.0
    ENABLE_LIVE_SEARCH: bool = False

    # ===========================================================================
    # LLM Provider & Multi-Model Execution Configuration
    # ===========================================================================
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_BASE_URL: str | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None
    GEMINI_API_KEY: SecretStr | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENROUTER_API_KEY: SecretStr | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GROQ_API_KEY: SecretStr | None = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    OMNIROUTE_API_KEY: SecretStr | None = None
    OMNIROUTE_BASE_URL: str = "https://api.cheaperinference.com/v1"
    DEFAULT_LLM_MODELS: list[str] = Field(
        default_factory=lambda: [
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "gemini-1.5-flash",
        ]
    )
    MAX_LLMS_PER_PROMPT: int = 3
    LLM_TIMEOUT_SECONDS: float = 30.0

    # ===========================================================================
    # Knowledge Base (KB) Configuration
    # ===========================================================================
    DEFAULT_OWNER_ID: str = "default_dev_user"
    KB_RELEVANCE_THRESHOLD: float = 0.15
    KB_MIN_OVERLAP_TOKENS: int = 2
    KB_MAX_DOCUMENT_BYTES: int = 5 * 1024 * 1024  # 5 MB
    KB_MAX_PASSAGES: int = 3
    KB_CHUNK_SIZE: int = 600
    KB_CHUNK_OVERLAP: int = 100
    KB_CORROBORATION_MODE: bool = False

    # ===========================================================================
    # Tavily Web Search (primary live evidence retrieval)
    # Obtain key from: https://tavily.com
    # ===========================================================================
    TAVILY_API_KEY: SecretStr | None = None
    TAVILY_MAX_RESULTS: int = 5
    TAVILY_SEARCH_DEPTH: str = "basic"  # "basic" or "advanced"
    TAVILY_TIMEOUT_SECONDS: float = 8.0

    # ===========================================================================
    # DuckDuckGo Search (secondary fallback — no API key required)
    # ===========================================================================
    ENABLE_DUCKDUCKGO_FALLBACK: bool = True
    DUCKDUCKGO_MAX_RESULTS: int = 5
    DUCKDUCKGO_TIMEOUT_SECONDS: float = 6.0

    # ===========================================================================
    # Nightcrawler / Wikipedia REST API (tertiary safe fallback)
    # Uses Wikipedia REST API as the final controlled retrieval fallback.
    # ===========================================================================
    ENABLE_NIGHTCRAWLER_FALLBACK: bool = True
    NIGHTCRAWLER_TIMEOUT_SECONDS: float = 5.0

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

    @field_validator("JWT_ALGORITHM", mode="after")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Enforce strict whitelist of permitted cryptographic algorithms."""
        allowed = {"HS256"}
        if v not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            raise ValueError(
                f"Unsupported JWT_ALGORITHM '{v}'. Strictly permitted: {allowed_list}"
            )
        return v

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

    @model_validator(mode="after")
    def validate_production_security_invariants(self) -> "Settings":
        """Enforce fail-closed production security invariants."""
        if self.ENVIRONMENT in ("production", "staging"):
            # 1. JWT_SECRET must be explicitly configured and non-default
            secret = self.JWT_SECRET.get_secret_value() if self.JWT_SECRET else ""
            if not secret or not secret.strip():
                raise ValueError(
                    f"FATAL: JWT_SECRET must be configured and non-empty in "
                    f"'{self.ENVIRONMENT}' environment."
                )
            if secret == INSECURE_DEV_JWT_SECRET or "insecure_development" in secret:
                raise ValueError(
                    f"FATAL: Default development JWT_SECRET is strictly forbidden in "
                    f"'{self.ENVIRONMENT}' environment. You must provide a secure, "
                    f"high-entropy secret via JWT_SECRET environment variable."
                )
            if len(secret) < 32:
                raise ValueError(
                    f"FATAL: JWT_SECRET must be at least 32 characters long in "
                    f"'{self.ENVIRONMENT}' environment (got {len(secret)} characters)."
                )

            # 2. DEBUG must not be True in production
            if self.DEBUG:
                raise ValueError(
                    f"FATAL: DEBUG mode cannot be enabled when ENVIRONMENT is "
                    f"'{self.ENVIRONMENT}'."
                )
        return self

    model_config = SettingsConfigDict(
        # Search for .env in backend/ first (Docker / CI), then repo root.
        env_file=(".env", "backend/.env"),
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
