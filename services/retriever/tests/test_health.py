"""Tests for the health endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.main import app


def _make_session_factory(
    *,
    db_ok: bool = True,
    pgvector_ok: bool = True,
) -> async_sessionmaker[AsyncSession]:
    """Build a mock session factory that simulates DB and pgvector checks.

    Args:
        db_ok: Whether ``SELECT 1`` succeeds.
        pgvector_ok: Whether the pgvector extension row is found.
    """

    def _scalar_for(sql_text: Any) -> int | None:
        sql_str = str(sql_text)
        if "SELECT 1" in sql_str and "pg_extension" not in sql_str:
            return 1 if db_ok else None
        if "pg_extension" in sql_str:
            return 1 if pgvector_ok else None
        return None

    mock_result = MagicMock()
    mock_result.scalar.side_effect = lambda: _scalar_for(
        mock_result._last_statement  # noqa: SLF001
    )

    mock_session = AsyncMock(spec=AsyncSession)

    async def _execute_side_effect(stmt: Any) -> MagicMock:
        mock_result._last_statement = str(stmt)  # noqa: SLF001
        return mock_result

    mock_session.execute = AsyncMock(side_effect=_execute_side_effect)

    # Make the session work as an async context manager
    mock_factory = MagicMock(spec=async_sessionmaker)

    class _FakeCtx:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            pass

    mock_factory.return_value = _FakeCtx()
    return mock_factory  # type: ignore[return-value]


def _raising_factory() -> async_sessionmaker[AsyncSession]:
    """Return a factory whose __call__ raises (simulating unreachable DB)."""
    mock_factory = MagicMock(spec=async_sessionmaker)

    class _RaisingCtx:
        async def __aenter__(self) -> None:
            raise ConnectionRefusedError("DB unreachable")

        async def __aexit__(self, *args: object) -> None:
            pass

    mock_factory.return_value = _RaisingCtx()
    return mock_factory  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_health_returns_response() -> None:
    """Health endpoint always returns 200, even when DB is unavailable."""
    with patch(
        "retriever.main._get_factory",
        side_effect=ConnectionRefusedError("no db"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_expected_fields() -> None:
    """Health response includes status, version, database, and pgvector."""
    factory = _make_session_factory(db_ok=True, pgvector_ok=True)
    with patch("retriever.main._get_factory", return_value=factory):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    data = response.json()
    assert set(data.keys()) == {"status", "version", "database", "pgvector"}
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["database"] == "connected"
    assert data["pgvector"] == "available"


@pytest.mark.asyncio
async def test_health_with_db_unavailable_returns_degraded() -> None:
    """When the database is unreachable, status is degraded."""
    factory = _raising_factory()
    with patch("retriever.main._get_factory", return_value=factory):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unavailable"
    assert data["pgvector"] == "unavailable"


@pytest.mark.asyncio
async def test_health_db_connected_but_no_pgvector() -> None:
    """When DB is reachable but pgvector is not installed, status is degraded."""
    factory = _make_session_factory(db_ok=True, pgvector_ok=False)
    with patch("retriever.main._get_factory", return_value=factory):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "connected"
    assert data["pgvector"] == "unavailable"
