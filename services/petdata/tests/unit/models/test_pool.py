"""Unit tests for env-driven connection-pool sizing (no live DB required)."""

from __future__ import annotations

from petdata.config import Settings
from petdata.models.base import create_engine


def test_create_engine_accepts_pool_params() -> None:
    engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/test",
        pool_size=3,
        max_overflow=7,
        pool_timeout=15.0,
        pool_recycle=900,
        pool_pre_ping=False,
    )
    # Engines are lazy — creation succeeds without a live DB.
    assert engine is not None


def test_settings_db_pool_defaults() -> None:
    settings = Settings()
    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 10
    assert settings.db_pool_timeout == 30.0
    assert settings.db_pool_recycle == -1
    assert settings.db_pool_pre_ping is True
