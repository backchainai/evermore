"""FastAPI dependencies for the Pet Data web module."""

from __future__ import annotations

from fastapi import Depends

# Resolved at runtime by FastAPI for dependency injection.
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from petdata.infrastructure.database.session import get_session
from petdata.modules.db import Database


async def get_repository(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Database:
    """Provide a repository bound to the request-scoped session.

    Args:
        session: Async session yielded by ``get_session``.

    Returns:
        Database repository for this request.
    """
    return Database(session)
