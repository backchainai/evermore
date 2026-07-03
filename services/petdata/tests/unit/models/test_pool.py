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
    """Default Settings pool fields actually reach the SQLAlchemy pool.

    Restating the Settings literals directly (``settings.db_pool_size == 5``)
    never exercises ``create_engine``'s parameter threading, so a mutant that
    breaks the plumbing (wrong kwarg, swapped values, dropped argument) would
    slip through undetected. Instead, thread a default ``Settings()``
    instance's pool fields into ``create_engine`` and assert the resulting
    engine's pool reflects the expected defaults via SQLAlchemy's pool
    introspection API. The async engine's pool implementation
    (``AsyncAdaptedQueuePool``) only exposes ``size()``/``timeout()`` as public
    methods; ``max_overflow``/``recycle``/``pre_ping`` have no public
    accessors, so the underlying ``_max_overflow``/``_recycle``/``_pre_ping``
    attributes are read directly (confirmed against the installed SQLAlchemy
    version before writing this test).
    """
    settings = Settings()
    engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/test",
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=settings.db_pool_pre_ping,
    )
    pool = engine.pool

    assert pool.size() == 5
    assert pool.timeout() == 30.0
    assert pool._max_overflow == 10
    assert pool._recycle == -1
    assert pool._pre_ping is True
