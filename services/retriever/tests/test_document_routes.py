"""Unit tests for document routes (no live DB or auth required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from retriever.modules.auth import AuthUser
from retriever.modules.auth.dependencies import require_admin, require_auth
from retriever.modules.documents.exceptions import (
    DocumentAlreadyExistsError,
    DocumentIndexingError,
    DocumentValidationError,
)
from retriever.modules.documents.routes import (
    get_document_service_dependency,
    router,
)
from retriever.modules.documents.schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from retriever.modules.documents.services import DocumentService

TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_USER = AuthUser(sub=TEST_USER_ID, email="test@example.com", is_admin=False)
TEST_ADMIN = AuthUser(sub=TEST_USER_ID, email="admin@example.com", is_admin=True)
DOC_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


def _build_app(
    mock_service: DocumentService,
    *,
    authenticated: bool = True,
    as_admin: bool = False,
) -> FastAPI:
    """Create a test FastAPI app with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_document_service_dependency] = lambda: mock_service

    if authenticated:
        user = TEST_ADMIN if as_admin else TEST_USER
        app.dependency_overrides[require_auth] = lambda: user
        if as_admin:
            app.dependency_overrides[require_admin] = lambda: user

    return app


# ── POST /api/v1/documents/upload ─────────────────────────────────────────


def test_upload_document_success() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.upload_document.return_value = DocumentUploadResponse(
        id=DOC_ID,
        filename="test.md",
        title="Test",
        chunks_created=5,
        message="Uploaded",
    )

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.md", BytesIO(b"# Test\ncontent"), "text/markdown")},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.md"
    assert data["chunks_created"] == 5


def test_upload_document_requires_admin() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    app = _build_app(mock_service, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.md", BytesIO(b"content"), "text/markdown")},
    )

    assert resp.status_code in (401, 403)


def test_upload_document_validation_error() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.upload_document.side_effect = DocumentValidationError("Bad file")

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("bad.png", BytesIO(b"data"), "image/png")},
    )

    assert resp.status_code == 400
    assert "Bad file" in resp.json()["detail"]


def test_upload_document_duplicate_error() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.upload_document.side_effect = DocumentAlreadyExistsError(
        "Already exists"
    )

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.md", BytesIO(b"content"), "text/markdown")},
    )

    assert resp.status_code == 409


def test_upload_document_indexing_error() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.upload_document.side_effect = DocumentIndexingError("Indexing failed")

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.md", BytesIO(b"content"), "text/markdown")},
    )

    assert resp.status_code == 500


# ── GET /api/v1/documents ────────────────────────────────────────────────────


def test_list_documents_success() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.list_documents.return_value = DocumentListResponse(
        documents=[
            DocumentResponse(
                id=DOC_ID,
                filename="test.md",
                title="Test",
                file_type="text/markdown",
                file_size_bytes=100,
                is_indexed=True,
                created_at=datetime.now(UTC),
                description=None,
            ),
        ],
        count=1,
    )

    app = _build_app(mock_service)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.get("/api/v1/documents")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["documents"]) == 1


def test_list_documents_requires_auth() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    app = _build_app(mock_service, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/v1/documents")

    assert resp.status_code in (401, 403)


# ── GET /api/v1/documents/{document_id} ─────────────────────────────────────


def test_get_document_success() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.get_document.return_value = DocumentResponse(
        id=DOC_ID,
        filename="test.md",
        title="Test",
        file_type="text/markdown",
        file_size_bytes=100,
        is_indexed=True,
        created_at=datetime.now(UTC),
        description=None,
    )

    app = _build_app(mock_service)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.get(f"/api/v1/documents/{DOC_ID}")

    assert resp.status_code == 200
    assert resp.json()["filename"] == "test.md"


def test_get_document_not_found() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.get_document.side_effect = DocumentValidationError("not found")

    app = _build_app(mock_service)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get(f"/api/v1/documents/{uuid.uuid4()}")

    assert resp.status_code == 404


# ── DELETE /api/v1/documents/{document_id} ──────────────────────────────────


def test_delete_document_success() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.delete_document.return_value = DocumentDeleteResponse(
        message="Deleted",
    )

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.delete(f"/api/v1/documents/{DOC_ID}")

    assert resp.status_code == 200
    assert "Deleted" in resp.json()["message"]


def test_delete_document_requires_admin() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    app = _build_app(mock_service, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.delete(f"/api/v1/documents/{DOC_ID}")

    assert resp.status_code in (401, 403)


def test_delete_document_not_found() -> None:
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.delete_document.side_effect = DocumentValidationError("not found")

    app = _build_app(mock_service, as_admin=True)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.delete(f"/api/v1/documents/{uuid.uuid4()}")

    assert resp.status_code == 404
