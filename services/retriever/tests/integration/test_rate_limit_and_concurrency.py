"""Concurrent-request handling and burst behavior for the retriever API.

``POST /api/v1/ask`` now carries the ADR-0012 per-user rate limit (slowapi,
in-memory, keyed on the authenticated user's Supabase id). The burst test
below targets ``GET /api/v1/documents``, which is unaffected by that limit,
so it asserts service stability under load (no 5xx) rather than a specific
429 response; its allowed-status set already includes 429, so it keeps
passing unmodified if a limiter is ever extended to this endpoint too.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

pytestmark = pytest.mark.integration

_CONCURRENCY = 8
_BURST_SIZE = 20


async def test_concurrent_document_list_requests(
    admin_client: httpx.AsyncClient,
) -> None:
    """Several concurrent GET /documents all succeed with a well-formed body."""
    responses = await asyncio.gather(
        *(admin_client.get("/api/v1/documents") for _ in range(_CONCURRENCY))
    )
    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert isinstance(data["documents"], list)


async def test_burst_document_list_requests_stay_stable(
    admin_client: httpx.AsyncClient,
) -> None:
    """A rapid burst of GET /documents never 5xxs.

    Every response is either 200 (current behavior, no limiter) or 429
    (expected behavior once a rate limiter is introduced).
    """
    responses = await asyncio.gather(
        *(admin_client.get("/api/v1/documents") for _ in range(_BURST_SIZE))
    )
    for resp in responses:
        assert resp.status_code in (200, 429)
