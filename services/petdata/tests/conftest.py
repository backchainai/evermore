"""Pytest configuration and shared fixtures.

Integration tests run against a live Postgres. Start one with::

    docker compose -f docker-compose.test.yml up -d

Set ``TEST_DATABASE_URL`` to override the default connection string. Tests that
depend on the ``db_engine`` / ``session`` fixtures skip automatically when no
Postgres is reachable, so the unit suite still runs on a bare checkout.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from petdata.main import create_app
from petdata.models.base import Base

if TYPE_CHECKING:
    from collections.abc import Iterator

# Import the ORM models so Base.metadata is populated before create_all.
from petdata.models import tables as _tables  # noqa: F401

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/petdata_test",
)


@pytest.fixture
def client() -> Iterator[object]:
    """Provide a TestClient for endpoints that do not touch the database.

    Schema is owned by Alembic and the engine is built lazily on first request,
    so importing and constructing the app needs no live database. Database-backed
    routes are exercised by the integration suite via the ``session`` fixture.
    """
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def db_engine() -> AsyncEngine:  # type: ignore[return]
    """Create all tables for one test; drop them after the test completes."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        await engine.dispose()
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
