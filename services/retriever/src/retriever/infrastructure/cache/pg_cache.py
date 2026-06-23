# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Semantic cache backed by pgvector cosine similarity."""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import DateTime, Float, Index, Text, delete, literal, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from retriever.infrastructure.cache.protocol import CachedAnswer
from retriever.models.base import Base
from retriever.models.user import DEFAULT_TENANT_ID

_EMBEDDING_DIM = 1536


class SemanticCacheEntry(Base):
    """Cached query/answer pair with embedding for similarity lookup."""

    __tablename__ = "semantic_cache"
    __table_args__ = (
        Index(
            "ix_semantic_cache_embedding_hnsw",
            "query_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"query_embedding": "vector_cosine_ops"},
        ),
        Index("ix_semantic_cache_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding: Mapped[list[float]] = mapped_column(
        Vector(_EMBEDDING_DIM), nullable=False
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=lambda: DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgSemanticCache:
    """SemanticCache using pgvector cosine similarity for lookup."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def get(
        self,
        query_embedding: list[float],
        tenant_id: uuid.UUID,
        *,
        threshold: float = 0.95,
    ) -> CachedAnswer | None:
        """Return a cached answer if a near-identical query exists."""
        max_distance = 1.0 - threshold
        vec = literal(query_embedding, type_=Vector(_EMBEDDING_DIM))
        async with self._factory() as session:
            row = await session.scalar(
                select(SemanticCacheEntry)
                .where(SemanticCacheEntry.tenant_id == tenant_id)
                .where(
                    SemanticCacheEntry.query_embedding.op("<=>", return_type=Float)(vec)
                    <= max_distance
                )
                .order_by(
                    SemanticCacheEntry.query_embedding.op("<=>", return_type=Float)(vec)
                )
                .limit(1)
            )
            if row is None:
                return None
            return CachedAnswer(answer=row.answer, sources=list(row.sources))

    async def set(
        self,
        query: str,
        query_embedding: list[float],
        answer: str,
        sources: list[dict[str, Any]],
        tenant_id: uuid.UUID,
    ) -> None:
        """Store a new cache entry."""
        async with self._factory() as session, session.begin():
            session.add(
                SemanticCacheEntry(
                    query=query,
                    query_embedding=query_embedding,
                    answer=answer,
                    sources=sources,
                    tenant_id=tenant_id,
                )
            )

    async def invalidate(self, tenant_id: uuid.UUID) -> None:
        """Delete all cache entries for a tenant."""
        async with self._factory() as session, session.begin():
            await session.execute(
                delete(SemanticCacheEntry).where(
                    SemanticCacheEntry.tenant_id == tenant_id
                )
            )
