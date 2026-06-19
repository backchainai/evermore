# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""SemanticCache protocol — defines the interface for query result caching."""

import uuid
from typing import Any, Protocol, TypedDict


class CachedAnswer(TypedDict):
    """A cached Q&A response."""

    answer: str
    sources: list[dict[str, Any]]


class SemanticCache(Protocol):
    """Interface for semantic similarity-based answer caching."""

    async def get(
        self,
        query_embedding: list[float],
        tenant_id: uuid.UUID,
        *,
        threshold: float = 0.95,
    ) -> CachedAnswer | None:
        """Return a cached answer if a sufficiently similar query exists."""
        ...

    async def set(
        self,
        query: str,
        query_embedding: list[float],
        answer: str,
        sources: list[dict[str, Any]],
        tenant_id: uuid.UUID,
    ) -> None:
        """Cache an answer for the given query embedding."""
        ...

    async def invalidate(self, tenant_id: uuid.UUID) -> None:
        """Remove all cached entries for a tenant."""
        ...
