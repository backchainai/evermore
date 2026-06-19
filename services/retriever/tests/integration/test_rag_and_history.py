"""RAG ask endpoint + conversation history flow.

Maps to pre-PR testing script sections 2.7, 2.8.
Tests run in declaration order within this module.
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_ask_returns_valid_response(
    authed_client: httpx.AsyncClient,
) -> None:
    """POST /ask → 200 with all expected fields."""
    # Clear history so count assertions below are reliable
    await authed_client.delete("/api/v1/history")

    resp = await authed_client.post(
        "/api/v1/ask",
        json={"question": "What are the shelter policies?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["answer"], str)
    assert isinstance(data["chunks_used"], list)
    assert data["confidence_level"] in ("high", "medium", "low")
    assert isinstance(data["confidence_score"], float)
    assert isinstance(data["blocked"], bool)
    assert "blocked_reason" in data


async def test_history_after_ask(authed_client: httpx.AsyncClient) -> None:
    """After asking a question, history should contain user + assistant."""
    resp = await authed_client.get("/api/v1/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    roles = [m["role"] for m in data["messages"]]
    assert "user" in roles
    assert "assistant" in roles


async def test_clear_history(authed_client: httpx.AsyncClient) -> None:
    """DELETE /history → deleted_count matches prior count."""
    resp = await authed_client.delete("/api/v1/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_count"] == 2
    assert "message" in data


async def test_history_after_clear(authed_client: httpx.AsyncClient) -> None:
    """After clearing, history is empty."""
    resp = await authed_client.get("/api/v1/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["messages"] == []


async def test_ask_no_crash_empty_vectorstore(
    authed_client: httpx.AsyncClient,
) -> None:
    """Asking with no indexed documents returns 200, not 500."""
    resp = await authed_client.post(
        "/api/v1/ask",
        json={"question": "Tell me something random"},
    )
    assert resp.status_code == 200
    # Clean up the messages we just created
    await authed_client.delete("/api/v1/history")
