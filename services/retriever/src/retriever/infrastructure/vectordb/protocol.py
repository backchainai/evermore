# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""VectorStore protocol — defines the interface for vector similarity search."""

import uuid
from typing import Protocol, TypedDict


class SearchResult(TypedDict):
    """A single chunk returned from a vector similarity search."""

    chunk_id: uuid.UUID
    content: str
    source: str
    title: str
    score: float  # cosine similarity [0, 1], higher is more similar


class ChunkInput(TypedDict):
    """Input for upserting a document chunk."""

    document_id: uuid.UUID
    content: str
    embedding: list[float]
    source: str
    title: str


class VectorStore(Protocol):
    """Interface for vector similarity search over document chunks."""

    async def search(
        self,
        embedding: list[float],
        tenant_id: uuid.UUID,
        *,
        limit: int = 5,
        min_score: float = 0.7,
    ) -> list[SearchResult]:
        """Return the top-k chunks most similar to the query embedding."""
        ...

    async def upsert(
        self,
        chunks: list[ChunkInput],
        tenant_id: uuid.UUID,
    ) -> None:
        """Insert or update document chunks with their embeddings."""
        ...

    async def delete_by_document(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        """Delete all chunks belonging to a document."""
        ...
