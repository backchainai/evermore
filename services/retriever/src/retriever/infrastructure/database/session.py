# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI database session dependency."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.config import get_settings
from retriever.models.base import create_engine, create_session_factory


@lru_cache
def _get_factory() -> async_sessionmaker[AsyncSession]:
    """Build (once) and cache the session factory from app settings."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url.get_secret_value(),
        require_ssl=settings.database_require_ssl,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=settings.db_pool_pre_ping,
    )
    return create_session_factory(engine)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session; commit on success, rollback on error.

    Usage::

        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with _get_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
