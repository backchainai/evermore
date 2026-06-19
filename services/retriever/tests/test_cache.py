"""Integration tests for PgSemanticCache."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.infrastructure.cache.pg_cache import PgSemanticCache

_DIM = 1536


def _embedding(value: float = 0.1) -> list[float]:
    return [value] * _DIM


@pytest.mark.integration
async def test_cache_miss_returns_none(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid.uuid4()
    cache = PgSemanticCache(session_factory)
    result = await cache.get(_embedding(0.42), tenant_id, threshold=0.99)
    assert result is None


@pytest.mark.integration
async def test_set_and_get(session_factory: async_sessionmaker[AsyncSession]) -> None:
    tenant_id = uuid.uuid4()
    cache = PgSemanticCache(session_factory)
    emb = _embedding(0.2)
    await cache.set(
        query="When does the shelter open?",
        query_embedding=emb,
        answer="The shelter opens at 9am.",
        sources=[{"file": "policy.pdf"}],
        tenant_id=tenant_id,
    )

    hit = await cache.get(emb, tenant_id, threshold=0.99)
    assert hit is not None
    assert hit["answer"] == "The shelter opens at 9am."
    assert hit["sources"] == [{"file": "policy.pdf"}]


@pytest.mark.integration
async def test_invalidate_clears_entries(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid.uuid4()
    cache = PgSemanticCache(session_factory)
    emb = _embedding(0.3)
    await cache.set(
        query="Test question",
        query_embedding=emb,
        answer="Test answer",
        sources=[],
        tenant_id=tenant_id,
    )

    await cache.invalidate(tenant_id)
    hit = await cache.get(emb, tenant_id, threshold=0.99)
    assert hit is None
