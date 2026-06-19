"""Integration tests for PgVectorStore."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.infrastructure.vectordb.pgvector_store import PgVectorStore

_DIM = 1536


def _embedding(value: float = 0.1) -> list[float]:
    return [value] * _DIM


@pytest.mark.integration
async def test_upsert_and_search(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    store = PgVectorStore(session_factory)
    chunks = [
        {
            "document_id": doc_id,
            "content": "The shelter opens at 9am.",
            "embedding": _embedding(0.1),
            "source": "policy.pdf",
            "title": "Hours",
        }
    ]
    await store.upsert(chunks, tenant_id)  # type: ignore[arg-type]

    results = await store.search(_embedding(0.1), tenant_id, min_score=0.5)
    assert len(results) >= 1
    assert results[0]["content"] == "The shelter opens at 9am."
    assert results[0]["score"] > 0.5


@pytest.mark.integration
async def test_search_returns_empty_below_threshold(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid.uuid4()
    store = PgVectorStore(session_factory)
    results = await store.search(_embedding(0.9), tenant_id, min_score=0.99)
    assert isinstance(results, list)


@pytest.mark.integration
async def test_delete_by_document(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    store = PgVectorStore(session_factory)
    chunks = [
        {
            "document_id": doc_id,
            "content": "To be deleted.",
            "embedding": _embedding(0.5),
            "source": "temp.pdf",
            "title": "Temp",
        }
    ]
    await store.upsert(chunks, tenant_id)  # type: ignore[arg-type]
    await store.delete_by_document(doc_id, tenant_id)

    results = await store.search(_embedding(0.5), tenant_id, min_score=0.99)
    contents = [r["content"] for r in results]
    assert "To be deleted." not in contents
