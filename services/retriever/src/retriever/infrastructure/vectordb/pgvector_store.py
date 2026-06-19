# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""pgvector-backed VectorStore implementation."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import DateTime, Float, Index, Text, delete, literal, select, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from retriever.infrastructure.vectordb.protocol import ChunkInput, SearchResult
from retriever.models.base import Base
from retriever.models.user import DEFAULT_TENANT_ID

_EMBEDDING_DIM = 1536


class DocumentChunk(Base):
    """Embedding + metadata for a single document chunk."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_document_chunks_tenant_doc", "tenant_id", "document_id"),
        Index(
            "ix_document_chunks_content_tsv",
            text("to_tsvector('english', content)"),
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(_EMBEDDING_DIM), nullable=False
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, default="")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=lambda: DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgVectorStore:
    """VectorStore backed by pgvector (cosine similarity)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def search(
        self,
        embedding: list[float],
        tenant_id: uuid.UUID,
        *,
        limit: int = 5,
        min_score: float = 0.7,
    ) -> list[SearchResult]:
        """Return up to `limit` chunks whose cosine similarity >= min_score."""
        max_distance = 1.0 - min_score
        vec = literal(embedding, type_=Vector(_EMBEDDING_DIM))
        async with self._factory() as session:
            rows = await session.execute(
                select(
                    DocumentChunk.id,
                    DocumentChunk.content,
                    DocumentChunk.source,
                    DocumentChunk.title,
                    (
                        1.0 - DocumentChunk.embedding.op("<=>", return_type=Float)(vec)
                    ).label("score"),
                )
                .where(DocumentChunk.tenant_id == tenant_id)
                .where(
                    DocumentChunk.embedding.op("<=>", return_type=Float)(vec)
                    <= max_distance
                )
                .order_by(DocumentChunk.embedding.op("<=>", return_type=Float)(vec))
                .limit(limit)
            )
            return [
                SearchResult(
                    chunk_id=row.id,
                    content=row.content,
                    source=row.source,
                    title=row.title,
                    score=float(row.score),
                )
                for row in rows
            ]

    async def upsert(
        self,
        chunks: list[ChunkInput],
        tenant_id: uuid.UUID,
    ) -> None:
        """Insert document chunks (existing chunks for the document are deleted first)."""
        if not chunks:
            return
        doc_ids = {c["document_id"] for c in chunks}
        if len(doc_ids) > 1:
            raise ValueError("upsert requires all chunks to share the same document_id")
        async with self._factory() as session, session.begin():
            doc_id = chunks[0]["document_id"]
            await session.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == doc_id,
                    DocumentChunk.tenant_id == tenant_id,
                )
            )
            session.add_all(
                [
                    DocumentChunk(
                        document_id=c["document_id"],
                        content=c["content"],
                        embedding=c["embedding"],
                        source=c["source"],
                        title=c["title"],
                        tenant_id=tenant_id,
                    )
                    for c in chunks
                ]
            )

    async def delete_by_document(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        """Remove all chunks for a document."""
        async with self._factory() as session, session.begin():
            await session.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.tenant_id == tenant_id,
                )
            )
