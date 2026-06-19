"""Shared pytest fixtures.

Integration tests require a running test Postgres:

    docker compose -f docker-compose.test.yml up -d

Set TEST_DATABASE_URL to override the default connection string.
Tests marked @pytest.mark.integration are skipped when the DB is unreachable.
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from retriever.models.base import Base

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/retriever_test",
)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: marks tests that require a live Postgres instance"
    )


@pytest_asyncio.fixture
async def db_engine() -> AsyncEngine:  # type: ignore[return]
    """Create all tables for one test; drop them after the test completes."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001 — any connection failure skips the suite
        pytest.skip(f"Integration DB unavailable: {exc}")
        return

    try:
        yield engine  # type: ignore[misc]
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine: AsyncEngine) -> AsyncSession:  # type: ignore[return]
    """Yield a session that is rolled back after each test (no persistent state)."""
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        db_engine, expire_on_commit=False
    )
    async with factory() as sess:
        yield sess  # type: ignore[misc]
        await sess.rollback()


@pytest_asyncio.fixture
async def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return the session factory (used by store/cache implementations)."""
    return async_sessionmaker(db_engine, expire_on_commit=False)
