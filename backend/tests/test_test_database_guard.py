"""Verify pytest cannot accidentally select the ordinary application database.

No database connection is opened: all values are synthetic URLs.
"""

import pytest
from backend.tests.conftest import _is_isolated_test_database


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+asyncpg://tester:password@127.0.0.1:5432/verifai",
        "postgresql+asyncpg://tester:password@127.0.0.1:5432/production",
        "postgresql+asyncpg://tester:password@127.0.0.1:5432/verifai_testing",
        "sqlite+aiosqlite:///app.sqlite",
        "sqlite+aiosqlite:///../../ordinary.sqlite",
        "not-a-url",
        "",
    ],
)
def test_non_test_databases_are_rejected(database_url: str) -> None:
    assert not _is_isolated_test_database(database_url)


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+asyncpg://tester:password@127.0.0.1:5432/verifai_test",
        "postgresql+asyncpg://tester:password@127.0.0.1:5432/test_verifai",
        "sqlite+aiosqlite:///:memory:",
        "sqlite+aiosqlite:///phase4_test.sqlite",
    ],
)
def test_explicitly_named_test_databases_are_accepted(database_url: str) -> None:
    assert _is_isolated_test_database(database_url)
