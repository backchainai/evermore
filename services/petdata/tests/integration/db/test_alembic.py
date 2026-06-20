"""Alembic upgrade/downgrade smoke test against a live Postgres.

This is a synchronous test on purpose: Alembic's ``env.py`` drives migrations
with ``asyncio.run``, which cannot be nested inside the event loop that
``pytest-asyncio`` runs async tests under. It connects with its own short-lived
async engine via ``asyncio.run`` for the connectivity probe and assertions.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration

# Mirrors the default in tests/conftest.py; ``tests`` is not an importable
# package (only ``src`` is on the path), so the value is read directly here.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/petdata_test",
)

_PETDATA_ROOT = Path(__file__).resolve().parents[3]


async def _regclass(table: str) -> str | None:
    """Return the table's regclass name, or None when it does not exist."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"SELECT to_regclass('public.{table}')"))
            return result.scalar()
    finally:
        await engine.dispose()


def _skip_if_db_unavailable() -> None:
    try:
        asyncio.run(_regclass("petdata_animals"))
    except Exception as exc:
        pytest.skip(f"Integration DB unavailable: {exc}")


def _alembic_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("PETDATA_DATABASE_URL", TEST_DATABASE_URL)
    cfg = Config(str(_PETDATA_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_PETDATA_ROOT / "alembic"))
    return cfg


def test_alembic_upgrade_then_downgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_if_db_unavailable()
    cfg = _alembic_config(monkeypatch)

    try:
        command.upgrade(cfg, "head")
        assert asyncio.run(_regclass("petdata_animals")) == "petdata_animals"
        assert asyncio.run(_regclass("petdata_volunteer_notes")) is not None
    finally:
        command.downgrade(cfg, "base")

    assert asyncio.run(_regclass("petdata_animals")) is None
