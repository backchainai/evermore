"""FastAPI dependencies for the Pet Data web module."""

from __future__ import annotations

from typing import TYPE_CHECKING

# FastAPI resolves this annotation at runtime for DI and OpenAPI generation.
from fastapi import Request  # noqa: TC002

if TYPE_CHECKING:
    from petdata.modules.db import Database


def get_db(request: Request) -> Database:
    """Get database instance from app state.

    Args:
        request: FastAPI request with app state.

    Returns:
        Database instance.
    """
    db: Database = request.app.state.db
    return db
