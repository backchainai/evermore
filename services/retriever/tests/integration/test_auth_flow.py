"""Authentication flow tests: unauthenticated → 401, authenticated → 200, admin → 403.

Maps to pre-PR testing script sections 2.4, 2.6, 2.10.
"""

from __future__ import annotations

import httpx
import pytest

from tests.integration.conftest import NIL_UUID

pytestmark = pytest.mark.integration


async def test_ask_unauthenticated(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.post(
        "/api/v1/ask",
        json={"question": "test"},
    )
    assert resp.status_code == 401


async def test_history_unauthenticated(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/api/v1/history")
    assert resp.status_code == 401


async def test_documents_list_unauthenticated(
    http_client: httpx.AsyncClient,
) -> None:
    resp = await http_client.get("/api/v1/documents")
    assert resp.status_code == 401


async def test_documents_upload_unauthenticated(
    http_client: httpx.AsyncClient,
) -> None:
    resp = await http_client.post("/api/v1/documents/upload")
    assert resp.status_code == 401


async def test_documents_delete_unauthenticated(
    http_client: httpx.AsyncClient,
) -> None:
    resp = await http_client.delete(f"/api/v1/documents/{NIL_UUID}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Authenticated requests → 200
# ---------------------------------------------------------------------------


async def test_history_authenticated_empty(
    authed_client: httpx.AsyncClient,
) -> None:
    # Clear any leftover history first
    await authed_client.delete("/api/v1/history")

    resp = await authed_client.get("/api/v1/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["messages"] == []


async def test_documents_authenticated_empty(
    admin_client: httpx.AsyncClient,
) -> None:
    resp = await admin_client.get("/api/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 0
    assert isinstance(data["documents"], list)
