# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Hybrid retriever combining semantic and keyword search.

Replaces the old in-memory BM25 approach with SQL ts_rank via an
existing GIN index on ``document_chunks``, merged with pgvector
cosine similarity through Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import uuid
from collections import defaultdict

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.infrastructure.vectordb.protocol import SearchResult, VectorStore

logger = structlog.get_logger()


class HybridRetriever:
    """Retriever combining semantic search with Postgres full-text keyword search.

    Hybrid retrieval improves accuracy by 10-15% over semantic-only search
    by catching both semantic matches ("sign in" = "check in") and
    exact keyword matches ("COVID-19 protocol").

    The results are merged using Reciprocal Rank Fusion (RRF), which
    combines rankings from multiple sources into a single ordered list.

    The caller is responsible for embedding the query before calling
    ``retrieve()`` — this class does not perform embedding.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        vector_store: VectorStore,
        *,
        semantic_weight: float = 0.5,
        keyword_weight: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        """Initialize the hybrid retriever.

        Args:
            session_factory: Async SQLAlchemy session factory for keyword search.
            vector_store: Store for semantic (vector) search.
            semantic_weight: Weight for semantic search results in RRF (0-1).
            keyword_weight: Weight for keyword search results in RRF (0-1).
            rrf_k: Constant for Reciprocal Rank Fusion (default 60).
        """
        self._session_factory = session_factory
        self._vector_store = vector_store
        self._semantic_weight = semantic_weight
        self._keyword_weight = keyword_weight
        self._rrf_k = rrf_k

    async def retrieve(
        self,
        query_embedding: list[float],
        query_text: str,
        tenant_id: uuid.UUID,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Retrieve documents using hybrid semantic + keyword search.

        Args:
            query_embedding: Pre-computed embedding vector for the query.
            query_text: Raw query text for keyword search.
            tenant_id: Tenant to scope the search to.
            top_k: Number of results to return.

        Returns:
            List of search results ordered by combined RRF relevance.
        """
        over_retrieve = top_k * 2

        # 1. Semantic search via vector store (over-retrieve by 2x)
        semantic_results = await self._vector_store.search(
            query_embedding,
            tenant_id,
            limit=over_retrieve,
            min_score=0.3,
        )

        logger.debug(
            "hybrid_semantic_results",
            count=len(semantic_results),
            top_score=semantic_results[0]["score"] if semantic_results else 0,
        )

        # 2. Keyword search via SQL ts_rank (over-retrieve by 2x)
        keyword_results = await self._keyword_search(
            query_text, tenant_id, limit=over_retrieve
        )

        logger.debug(
            "hybrid_keyword_results",
            count=len(keyword_results),
            top_score=keyword_results[0]["score"] if keyword_results else 0,
        )

        # 3. Merge results using Reciprocal Rank Fusion
        merged = self._reciprocal_rank_fusion(semantic_results, keyword_results)

        # 4. Return top_k results
        final_results = merged[:top_k]

        logger.info(
            "hybrid_retrieval_complete",
            query_length=len(query_text),
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_results),
            merged_count=len(merged),
            returned_count=len(final_results),
        )

        return final_results

    async def _keyword_search(
        self,
        query_text: str,
        tenant_id: uuid.UUID,
        *,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search using Postgres full-text search with ts_rank.

        Uses the existing GIN index on ``document_chunks.content``.

        Args:
            query_text: The search query text.
            tenant_id: Tenant to scope the search to.
            limit: Maximum number of results to return.

        Returns:
            List of search results with ts_rank scores.
        """
        sql = text(
            """
            SELECT id, content, source, title,
                   ts_rank(
                       to_tsvector('english', content),
                       plainto_tsquery('english', :query)
                   ) AS score
            FROM document_chunks
            WHERE tenant_id = :tenant_id
              AND to_tsvector('english', content)
                  @@ plainto_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :limit
            """
        )

        async with self._session_factory() as session:
            rows = await session.execute(
                sql,
                {"query": query_text, "tenant_id": tenant_id, "limit": limit},
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

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Merge results using Reciprocal Rank Fusion.

        RRF score = sum(weight / (k + rank + 1)) for each ranking list.
        This gives higher weight to documents ranked highly in multiple lists.

        Args:
            semantic_results: Results from semantic (vector) search.
            keyword_results: Results from keyword (full-text) search.

        Returns:
            Merged results sorted by RRF score descending.
        """
        rrf_scores: dict[uuid.UUID, float] = defaultdict(float)
        doc_map: dict[uuid.UUID, SearchResult] = {}

        # Add semantic results
        for rank, result in enumerate(semantic_results):
            chunk_id = result["chunk_id"]
            rrf_scores[chunk_id] += self._semantic_weight / (self._rrf_k + rank + 1)
            doc_map[chunk_id] = result

        # Add keyword results
        for rank, result in enumerate(keyword_results):
            chunk_id = result["chunk_id"]
            rrf_scores[chunk_id] += self._keyword_weight / (self._rrf_k + rank + 1)
            # Prefer semantic result if we have both (has embedding-based score)
            if chunk_id not in doc_map:
                doc_map[chunk_id] = result

        # Sort by RRF score descending
        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True
        )

        # Build result list with RRF score as the final score
        merged: list[SearchResult] = []
        for chunk_id in sorted_ids:
            original = doc_map[chunk_id]
            merged.append(
                SearchResult(
                    chunk_id=original["chunk_id"],
                    content=original["content"],
                    source=original["source"],
                    title=original["title"],
                    score=rrf_scores[chunk_id],
                )
            )

        return merged
