# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI database session dependency."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from petdata.config import get_settings
from petdata.models.base import create_engine, create_session_factory

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@lru_cache
def _get_factory() -> async_sessionmaker[AsyncSession]:
    """Build (once) and cache the session factory from app settings."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url.get_secret_value(),
        require_ssl=settings.database_require_ssl,
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
