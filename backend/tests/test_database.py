"""Tests for database configuration, engine lifecycle, sessions, and connectivity."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.core.database import (
    check_database_connectivity,
    dispose_async_engine,
    get_async_engine,
)
from app.core.dependencies import get_async_session


def test_default_database_settings_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that default settings have DATABASE_URL as None (unconfigured)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.DATABASE_URL is None
    assert settings.DATABASE_POOL_SIZE == 5
    assert settings.DATABASE_MAX_OVERFLOW == 10
    assert settings.DATABASE_POOL_TIMEOUT == 30
    assert settings.DATABASE_CONNECT_TIMEOUT == 3.0


def test_database_url_secret_masking() -> None:
    """Verify DATABASE_URL uses SecretStr and never leaks secrets in repr or str."""
    raw_url = "postgresql+asyncpg://admin_user:super_secret_password@localhost:5432/verifai_db"
    settings = Settings(DATABASE_URL=SecretStr(raw_url))
    assert settings.DATABASE_URL is not None
    # Confirm raw password is never exposed in repr or str
    assert "super_secret_password" not in str(settings.DATABASE_URL)
    assert "super_secret_password" not in repr(settings.DATABASE_URL)
    assert "super_secret_password" not in repr(settings)
    # Secret can be accessed explicitly when needed by the engine factory
    assert settings.DATABASE_URL.get_secret_value() == raw_url


def test_database_url_invalid_driver_negative_control() -> None:
    """Negative control: Synchronous or non-asyncpg URL must be rejected."""
    sync_url = "postgresql://user:pass@localhost:5432/verifai"
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL=SecretStr(sync_url))


def test_database_url_valid_async_driver() -> None:
    """Verify that valid postgresql+asyncpg URL is accepted."""
    valid_url = "postgresql+asyncpg://user:pass@localhost:5432/verifai"
    settings = Settings(DATABASE_URL=SecretStr(valid_url))
    assert settings.DATABASE_URL is not None
    assert settings.DATABASE_URL.get_secret_value() == valid_url


@pytest.mark.anyio
async def test_engine_creation_and_disposal() -> None:
    """Verify AsyncEngine creation is lazy and can be cleanly disposed."""
    test_url = "postgresql+asyncpg://user:pass@localhost:5432/verifai"
    settings = Settings(DATABASE_URL=SecretStr(test_url))

    engine = get_async_engine(settings)
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+asyncpg"

    # Engine disposal must execute cleanly
    await dispose_async_engine(engine)


@pytest.mark.anyio
async def test_session_lifecycle() -> None:
    """Verify async session factory and dependency session generator."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_maker = MagicMock()
    mock_maker.return_value.__aenter__.return_value = mock_session
    mock_maker.return_value.__aexit__.return_value = None

    async for session in get_async_session(session_maker=mock_maker):
        assert session == mock_session

    # Verify session was closed cleanly in finally block
    mock_session.close.assert_awaited_once()


@pytest.mark.anyio
async def test_connectivity_check_unconfigured() -> None:
    """Verify connectivity check returns unconfigured when DATABASE_URL is None."""
    settings = Settings(DATABASE_URL=None)
    result = await check_database_connectivity(settings=settings, engine=None)
    assert result == {
        "configured": False,
        "status": "unconfigured",
    }


@pytest.mark.anyio
async def test_connectivity_check_available_mocked() -> None:
    """Verify connectivity check returns available when query succeeds (mocked)."""
    test_url = "postgresql+asyncpg://user:pass@localhost:5432/verifai"
    settings = Settings(DATABASE_URL=SecretStr(test_url))

    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_conn = AsyncMock()
    mock_engine.connect.return_value.__aenter__.return_value = mock_conn

    result = await check_database_connectivity(settings=settings, engine=mock_engine)
    assert result == {
        "configured": True,
        "status": "available",
    }
    mock_conn.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_connectivity_check_unavailable_mocked() -> None:
    """Verify connectivity check returns unavailable on failures (mocked)."""
    test_url = "postgresql+asyncpg://user:pass@localhost:5432/verifai"
    settings = Settings(DATABASE_URL=SecretStr(test_url))

    mock_engine = AsyncMock(spec=AsyncEngine)
    # Simulate connection error with sensitive server info
    mock_engine.connect.side_effect = ConnectionRefusedError(
        "FATAL: password authentication failed for user 'secret_user'"
    )

    result = await check_database_connectivity(settings=settings, engine=mock_engine)
    assert result == {
        "configured": True,
        "status": "unavailable",
    }
    # Ensure no exception text or credentials leaked in result dictionary
    assert "secret_user" not in str(result)
    assert "FATAL" not in str(result)


@pytest.mark.anyio
async def test_production_database_persistence_failure_raises_503() -> None:
    """Regression test: Production MUST NOT silently fall back to ephemeral mode on DB commit failure."""
    from app.core.errors import ServiceUnavailableError
    from app.modules.verification.orchestrator import VerificationOrchestrator
    from app.schemas.verification import VerificationCreateRequest

    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=SecretStr("super-secure-production-jwt-secret-key-32chars"),
        DATABASE_URL=SecretStr("postgresql+asyncpg://prod:pass@localhost:5432/verifai"),
    )
    orchestrator = VerificationOrchestrator(settings=prod_settings)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result
    mock_session.commit.side_effect = RuntimeError(
        "PostgreSQL connection terminated abruptly"
    )

    req = VerificationCreateRequest(text="Water boils at 100 degrees Celsius.")

    with pytest.raises(ServiceUnavailableError) as exc_info:
        await orchestrator.verify(request=req, db_session=mock_session)

    assert exc_info.value.status_code == 503
    assert "Database persistence failed" in exc_info.value.message
    mock_session.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_production_missing_db_session_raises_503() -> None:
    """Regression test: Production MUST NOT execute without a database session."""
    from app.core.errors import ServiceUnavailableError
    from app.modules.verification.orchestrator import VerificationOrchestrator
    from app.schemas.verification import VerificationCreateRequest

    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=SecretStr("super-secure-production-jwt-secret-key-32chars"),
        DATABASE_URL=SecretStr("postgresql+asyncpg://prod:pass@localhost:5432/verifai"),
    )
    orchestrator = VerificationOrchestrator(settings=prod_settings)
    req = VerificationCreateRequest(text="Water boils at 100 degrees Celsius.")

    with pytest.raises(ServiceUnavailableError) as exc_info:
        await orchestrator.verify(request=req, db_session=None)

    assert exc_info.value.status_code == 503
    assert "ephemeral execution is prohibited" in exc_info.value.message


@pytest.mark.anyio
async def test_dev_missing_db_session_allows_in_memory_unit_tests() -> None:
    """Development and test environments permit hermetic execution without DB session."""
    from app.modules.verification.orchestrator import VerificationOrchestrator
    from app.schemas.verification import VerificationCreateRequest

    dev_settings = Settings(
        ENVIRONMENT="test",
        JWT_SECRET=SecretStr("dev-jwt-secret-for-testing-only-32chars"),
    )
    orchestrator = VerificationOrchestrator(settings=dev_settings)
    req = VerificationCreateRequest(text="Water boils at 100 degrees Celsius.")

    response = await orchestrator.verify(request=req, db_session=None)
    assert response.status == "COMPLETED"
