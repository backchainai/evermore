# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""SQLAlchemy 2.0 async engine, session factory, and declarative base."""

import re

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all petdata SQLAlchemy models."""


def _async_url(database_url: str) -> str:
    """Convert a postgres:// URL to postgresql+asyncpg://, stripping sslmode."""
    url = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql+asyncpg://", database_url)
    # asyncpg handles SSL via connect_args; strip the query param to avoid conflicts
    # Handle ?sslmode=...& (sslmode is first param, others follow)
    url = re.sub(r"\?sslmode=\w+&", "?", url)
    # Handle &sslmode=... or ?sslmode=... with no following params
    url = re.sub(r"[?&]sslmode=\w+", "", url)
    return url.rstrip("?")


def create_engine(
    database_url: str,
    *,
    require_ssl: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_recycle: int = -1,
    pool_pre_ping: bool = True,
) -> AsyncEngine:
    """Create an async SQLAlchemy engine.

    Args:
        database_url: Postgres connection URL (postgres:// or postgresql://).
        require_ssl: Enforce SSL (set True for Supabase / Cloud Run).
        pool_size: Number of persistent connections in the pool.
        max_overflow: Additional connections allowed above pool_size.
        pool_timeout: Seconds to wait for a connection before raising.
        pool_recycle: Recycle connections older than this many seconds
            (-1 disables recycling).
        pool_pre_ping: Test connections for liveness before use.

    Returns:
        Configured AsyncEngine instance.
    """
    connect_args: dict[str, object] = {"prepared_statement_cache_size": 0}
    if require_ssl:
        connect_args["ssl"] = "require"

    return create_async_engine(
        _async_url(database_url),
        pool_pre_ping=pool_pre_ping,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        connect_args=connect_args,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to the given engine.

    Sessions are configured with expire_on_commit=False (required for async).
    """
    return async_sessionmaker(engine, expire_on_commit=False)
