"""Regression guards for production schema startup and container defaults."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from app.core.config import Settings
from app.main import lifespan

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("environment", ["production", "staging"])
def test_schema_initialization_failure_blocks_non_development_startup(environment):
    settings = Settings(
        _env_file=None,
        ENVIRONMENT=environment,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test_only_random_length_32_plus_chars_0123456789",
    )

    async def boot():
        async with lifespan(FastAPI()):
            pass

    with (
        patch("app.main.get_settings", return_value=settings),
        patch(
            "app.core.database.init_db",
            new=AsyncMock(side_effect=RuntimeError("simulated DB schema error")),
        ),
        pytest.raises(RuntimeError, match="Database schema initialization failed"),
    ):
        asyncio.run(boot())


def test_compose_requires_secrets_without_public_database_or_source_mount():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
    assert "${POSTGRES_PASSWORD:?" in compose
    assert "${JWT_SECRET:?" in compose
    assert "${PROVIDER_CREDENTIAL_ENCRYPTION_KEY:?" in compose
    assert "${POSTGRES_BIND_HOST:-127.0.0.1}" in compose
    assert "${BACKEND_BIND_HOST:-127.0.0.1}" in compose
    assert "verifai_dev_secret" not in compose
    assert "./backend:/app/backend" not in compose


def test_docker_context_excludes_local_credentials():
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text().splitlines()
    assert ".env" in dockerignore
    assert "**/.env" in dockerignore
    assert "**/.env.*" in dockerignore
    assert "/api/v1/ready" in (PROJECT_ROOT / "Dockerfile").read_text()
