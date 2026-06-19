"""Unit tests for the HybridRetriever.

Tests cover RRF merging logic, deduplication, edge cases (empty results,
single-source results), and top_k limiting — all with mocked dependencies.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from retriever.infrastructure.vectordb.protocol import SearchResult
from retriever.modules.rag.retriever import HybridRetriever

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _result(
    chunk_id: uuid.UUID,
    content: str = "text",
    source: str = "doc.pdf",
    title: str = "Doc",
    score: float = 0.9,
) -> SearchResult:
    """Build a SearchResult TypedDict with sensible defaults."""
    return SearchResult(
        chunk_id=chunk_id,
        content=content,
        source=source,
        title=title,
        score=score,
    )


# Fixed UUIDs for deterministic tests
ID_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ID_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ID_C = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
ID_D = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_keyword_row(
    chunk_id: uuid.UUID,
    content: str,
    source: str,
    title: str,
    score: float,
) -> MagicMock:
    """Return a mock row object mimicking a SQLAlchemy result row."""
    row = MagicMock()
    row.id = chunk_id
    row.content = content
    row.source = source
    row.title = title
    row.score = score
    return row


def _build_retriever(
    vector_results: list[SearchResult],
    keyword_rows: list[MagicMock],
    *,
    semantic_weight: float = 0.5,
    keyword_weight: float = 0.5,
    rrf_k: int = 60,
) -> HybridRetriever:
    """Build a HybridRetriever with fully mocked dependencies.

    Args:
        vector_results: Results the mocked vector_store.search will return.
        keyword_rows: Row mocks the mocked session.execute will yield.
        semantic_weight: RRF weight for semantic results.
        keyword_weight: RRF weight for keyword results.
        rrf_k: RRF constant.

    Returns:
        Configured HybridRetriever instance.
    """
    # Mock vector store
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=vector_results)

    # Mock session factory: factory() returns an async context manager
    # that yields a session whose execute() returns rows.
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(keyword_rows))

    mock_session = AsyncMock(spec=["execute", "__aenter__", "__aexit__"])
    mock_session.execute = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def _session_ctx() -> AsyncGenerator[Any]:
        yield mock_session

    mock_factory = MagicMock()
    mock_factory.return_value = _session_ctx()
    # Each call to factory() needs a fresh context manager
    mock_factory.side_effect = lambda: _session_ctx()

    return HybridRetriever(
        session_factory=mock_factory,
        vector_store=vector_store,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
        rrf_k=rrf_k,
    )


# ---------------------------------------------------------------------------
# Tests — RRF merging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rrf_merges_overlapping_results() -> None:
    """Documents appearing in both lists get boosted by combined RRF scores."""
    # Semantic: A(rank 0), B(rank 1), C(rank 2)
    semantic = [
        _result(ID_A, content="A"),
        _result(ID_B, content="B"),
        _result(ID_C, content="C"),
    ]
    # Keyword: B(rank 0), D(rank 1), A(rank 2)
    keyword_rows = [
        _make_keyword_row(ID_B, "B", "doc.pdf", "Doc", 0.8),
        _make_keyword_row(ID_D, "D", "doc.pdf", "Doc", 0.6),
        _make_keyword_row(ID_A, "A", "doc.pdf", "Doc", 0.4),
    ]

    retriever = _build_retriever(semantic, keyword_rows)
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test query",
        tenant_id=TENANT,
        top_k=10,
    )

    ids = [r["chunk_id"] for r in results]

    # B appears at rank 1 in semantic and rank 0 in keyword → highest combined
    assert ids[0] == ID_B
    # A appears at rank 0 in semantic and rank 2 in keyword → second highest
    assert ids[1] == ID_A
    # All four unique chunks present
    assert set(ids) == {ID_A, ID_B, ID_C, ID_D}


@pytest.mark.asyncio
async def test_rrf_scores_are_correctly_computed() -> None:
    """Verify RRF score formula: weight / (k + rank + 1)."""
    rrf_k = 60
    semantic = [_result(ID_A)]
    keyword_rows = [_make_keyword_row(ID_A, "A", "doc.pdf", "Doc", 0.5)]

    retriever = _build_retriever(semantic, keyword_rows, rrf_k=rrf_k)
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    expected_score = 0.5 / (60 + 0 + 1) + 0.5 / (60 + 0 + 1)
    assert len(results) == 1
    assert abs(results[0]["score"] - expected_score) < 1e-9


# ---------------------------------------------------------------------------
# Tests — single-source results
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semantic_only_results() -> None:
    """When keyword search returns nothing, semantic results still come through."""
    semantic = [
        _result(ID_A, content="A"),
        _result(ID_B, content="B"),
    ]

    retriever = _build_retriever(semantic, keyword_rows=[])
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    assert len(results) == 2
    ids = [r["chunk_id"] for r in results]
    assert ids == [ID_A, ID_B]


@pytest.mark.asyncio
async def test_keyword_only_results() -> None:
    """When semantic search returns nothing, keyword results still come through."""
    keyword_rows = [
        _make_keyword_row(ID_C, "C", "doc.pdf", "Doc", 0.9),
        _make_keyword_row(ID_D, "D", "doc.pdf", "Doc", 0.7),
    ]

    retriever = _build_retriever(vector_results=[], keyword_rows=keyword_rows)
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    assert len(results) == 2
    ids = [r["chunk_id"] for r in results]
    assert ids == [ID_C, ID_D]


# ---------------------------------------------------------------------------
# Tests — empty results
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_results_from_both() -> None:
    """When both search methods return nothing, retrieve returns an empty list."""
    retriever = _build_retriever(vector_results=[], keyword_rows=[])
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=5,
    )

    assert results == []


# ---------------------------------------------------------------------------
# Tests — deduplication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deduplication_by_chunk_id() -> None:
    """Chunks appearing in both lists are not duplicated in output."""
    semantic = [_result(ID_A, content="A-semantic")]
    keyword_rows = [_make_keyword_row(ID_A, "A-keyword", "doc.pdf", "Doc", 0.5)]

    retriever = _build_retriever(semantic, keyword_rows)
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == ID_A
    # Semantic result is preferred when both exist
    assert results[0]["content"] == "A-semantic"


# ---------------------------------------------------------------------------
# Tests — top_k limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_top_k_limits_output() -> None:
    """Output is capped at top_k even when more results are available."""
    semantic = [
        _result(ID_A, content="A"),
        _result(ID_B, content="B"),
        _result(ID_C, content="C"),
    ]
    keyword_rows = [
        _make_keyword_row(ID_D, "D", "doc.pdf", "Doc", 0.9),
    ]

    retriever = _build_retriever(semantic, keyword_rows)
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=2,
    )

    assert len(results) == 2


# ---------------------------------------------------------------------------
# Tests — weight configuration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semantic_weight_bias() -> None:
    """Higher semantic weight should rank semantic-only results above keyword-only."""
    # Only in semantic, not keyword
    semantic = [_result(ID_A, content="A")]
    # Only in keyword, not semantic
    keyword_rows = [_make_keyword_row(ID_B, "B", "doc.pdf", "Doc", 0.9)]

    retriever = _build_retriever(
        semantic, keyword_rows, semantic_weight=0.9, keyword_weight=0.1
    )
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    # With 0.9 semantic weight vs 0.1 keyword weight, both at rank 0,
    # A (semantic only) should score higher than B (keyword only)
    assert results[0]["chunk_id"] == ID_A
    assert results[1]["chunk_id"] == ID_B


@pytest.mark.asyncio
async def test_keyword_weight_bias() -> None:
    """Higher keyword weight should rank keyword-only results above semantic-only."""
    semantic = [_result(ID_A, content="A")]
    keyword_rows = [_make_keyword_row(ID_B, "B", "doc.pdf", "Doc", 0.9)]

    retriever = _build_retriever(
        semantic, keyword_rows, semantic_weight=0.1, keyword_weight=0.9
    )
    results = await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=10,
    )

    assert results[0]["chunk_id"] == ID_B
    assert results[1]["chunk_id"] == ID_A


# ---------------------------------------------------------------------------
# Tests — vector store receives correct parameters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vector_store_called_with_correct_params() -> None:
    """Verify the vector store is called with over-retrieve limit and min_score."""
    retriever = _build_retriever(vector_results=[], keyword_rows=[])

    await retriever.retrieve(
        query_embedding=[0.1] * 1536,
        query_text="test",
        tenant_id=TENANT,
        top_k=5,
    )

    vector_store = retriever._vector_store  # noqa: SLF001
    vector_store.search.assert_awaited_once_with(
        [0.1] * 1536,
        TENANT,
        limit=10,  # top_k * 2
        min_score=0.3,
    )
