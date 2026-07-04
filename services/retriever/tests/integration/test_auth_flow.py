"""Authentication flow tests: unauthenticated → 401, authenticated → 200, admin → 403.

Maps to pre-PR testing script sections 2.4, 2.6, 2.10.
"""

from __future__ import annotations

import uuid

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
    """GET /documents count tracks a real upload/delete delta, not just >= 0."""
    baseline_resp = await admin_client.get("/api/v1/documents")
    assert baseline_resp.status_code == 200
    baseline_data = baseline_resp.json()
    assert isinstance(baseline_data["documents"], list)
    baseline_count = baseline_data["count"]

    unique_name = f"auth-flow-{uuid.uuid4().hex[:8]}.md"
    upload_resp = await admin_client.post(
        "/api/v1/documents/upload",
        files={"file": (unique_name, b"# Auth flow probe doc\n", "text/markdown")},
    )
    assert upload_resp.status_code == 201
    uploaded_id = upload_resp.json()["id"]

    after_upload_resp = await admin_client.get("/api/v1/documents")
    assert after_upload_resp.status_code == 200
    after_upload_data = after_upload_resp.json()
    assert isinstance(after_upload_data["documents"], list)
    assert after_upload_data["count"] == baseline_count + 1
    assert uploaded_id in [d["id"] for d in after_upload_data["documents"]]

    delete_resp = await admin_client.delete(f"/api/v1/documents/{uploaded_id}")
    assert delete_resp.status_code == 200

    after_delete_resp = await admin_client.get("/api/v1/documents")
    assert after_delete_resp.status_code == 200
    assert after_delete_resp.json()["count"] == baseline_count
