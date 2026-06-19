"""Input validation tests: 422 for empty/missing/oversized questions.

Maps to pre-PR testing script section 2.11.
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_ask_empty_question(authed_client: httpx.AsyncClient) -> None:
    resp = await authed_client.post("/api/v1/ask", json={"question": ""})
    assert resp.status_code == 422


async def test_ask_missing_question_field(
    authed_client: httpx.AsyncClient,
) -> None:
    resp = await authed_client.post("/api/v1/ask", json={})
    assert resp.status_code == 422


async def test_ask_question_too_long(authed_client: httpx.AsyncClient) -> None:
    resp = await authed_client.post("/api/v1/ask", json={"question": "x" * 2001})
    assert resp.status_code == 422
