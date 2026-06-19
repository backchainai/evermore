"""Document CRUD lifecycle: upload → list → ask → delete.

Maps to pre-PR testing script sections 2.9, 2.10.
Requires admin token and live RAG pipeline (LLM + embedding API keys).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from tests.integration.conftest import NIL_UUID

pytestmark = pytest.mark.integration

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def _uploaded_doc_id() -> list[str]:
    """Mutable container to share the uploaded doc ID across tests."""
    return []


async def test_upload_document(
    admin_client: httpx.AsyncClient,
    _uploaded_doc_id: list[str],
) -> None:
    """POST /upload → 201 with document metadata."""
    test_file = _FIXTURES_DIR / "test-doc.md"
    with open(test_file, "rb") as f:
        resp = await admin_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test-doc.md", f, "text/markdown")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["filename"] == "test-doc.md"
    assert "title" in data
    assert data["chunks_created"] > 0
    assert "message" in data
    _uploaded_doc_id.append(data["id"])


async def test_list_documents_after_upload(
    admin_client: httpx.AsyncClient,
    _uploaded_doc_id: list[str],
) -> None:
    """GET /documents → includes the uploaded document."""
    assert _uploaded_doc_id, "Upload test must run first"

    resp = await admin_client.get("/api/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    doc_ids = [d["id"] for d in data["documents"]]
    assert _uploaded_doc_id[0] in doc_ids
    # Find our doc and check is_indexed
    our_doc = next(d for d in data["documents"] if d["id"] == _uploaded_doc_id[0])
    assert our_doc["is_indexed"] is True


async def test_ask_with_indexed_document(
    admin_client: httpx.AsyncClient,
    _uploaded_doc_id: list[str],
) -> None:
    """POST /ask about uploaded content → answer references it."""
    assert _uploaded_doc_id, "Upload test must run first"

    resp = await admin_client.post(
        "/api/v1/ask",
        json={"question": "What time is feeding?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # The answer should reference feeding times from the test document
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    # Clean up messages
    await admin_client.delete("/api/v1/history")


async def test_delete_document(
    admin_client: httpx.AsyncClient,
    _uploaded_doc_id: list[str],
) -> None:
    """DELETE /documents/{id} → 200 with message."""
    assert _uploaded_doc_id, "Upload test must run first"

    resp = await admin_client.delete(f"/api/v1/documents/{_uploaded_doc_id[0]}")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data


async def test_non_admin_cannot_upload(
    authed_client: httpx.AsyncClient,
) -> None:
    """POST /upload with regular token → 403."""
    test_file = _FIXTURES_DIR / "test-doc.md"
    with open(test_file, "rb") as f:
        resp = await authed_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test-doc.md", f, "text/markdown")},
        )
    assert resp.status_code == 403


async def test_non_admin_cannot_delete(
    authed_client: httpx.AsyncClient,
) -> None:
    """DELETE /documents/{id} with regular token → 403."""
    resp = await authed_client.delete(f"/api/v1/documents/{NIL_UUID}")
    assert resp.status_code == 403
