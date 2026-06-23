"""Unit tests for DocumentService with mocked dependencies."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from retriever.models.document import Document
from retriever.modules.documents.exceptions import (
    DocumentAlreadyExistsError,
    DocumentIndexingError,
    DocumentValidationError,
)
from retriever.modules.documents.repos import DocumentRepository
from retriever.modules.documents.services import DocumentService
from retriever.modules.rag.schemas import IndexingResult

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def _make_document(
    *,
    filename: str = "test.md",
    title: str = "test",
    doc_id: uuid.UUID | None = None,
) -> MagicMock:
    """Create a mock Document."""
    doc = MagicMock(spec=Document)
    doc.id = doc_id or uuid.uuid4()
    doc.filename = filename
    doc.title = title
    doc.file_path = f"ephemeral://{filename}"
    doc.tenant_id = TENANT_ID
    doc.is_indexed = True
    doc.file_size_bytes = 100
    doc.file_type = "text/markdown"
    doc.uploaded_by = USER_ID
    doc.description = None
    doc.created_at = datetime.now(UTC)
    doc.updated_at = datetime.now(UTC)
    return doc


def _build_service(
    *,
    repo: DocumentRepository | None = None,
    rag_service: AsyncMock | None = None,
    vector_store: AsyncMock | None = None,
    semantic_cache: AsyncMock | None = None,
    max_documents: int = 20,
) -> tuple[DocumentService, AsyncMock, AsyncMock, AsyncMock, AsyncMock | None]:
    """Build a DocumentService with mock dependencies."""
    mock_repo = repo or AsyncMock(spec=DocumentRepository)
    mock_rag = rag_service or AsyncMock()
    mock_store = vector_store or AsyncMock()
    mock_cache = semantic_cache

    service = DocumentService(
        document_repo=mock_repo,  # type: ignore[arg-type]
        rag_service=mock_rag,
        vector_store=mock_store,
        semantic_cache=mock_cache,
        max_documents=max_documents,
    )
    return service, mock_repo, mock_rag, mock_store, mock_cache


# ── upload_document ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_document_valid_file() -> None:
    service, mock_repo, mock_rag, _, _ = _build_service()

    mock_repo.get_count.return_value = 0
    mock_repo.exists_by_filename.return_value = False

    doc = _make_document()
    mock_repo.create.return_value = doc

    mock_rag.index_document.return_value = IndexingResult(
        source="test.md",
        chunks_created=5,
        success=True,
        parsed_title="Test Document",
    )

    result = await service.upload_document(
        file_content=b"# Test Document\n\nSome content here.",
        filename="test.md",
        tenant_id=TENANT_ID,
        uploaded_by=USER_ID,
    )

    assert result.filename == "test.md"
    assert result.chunks_created == 5
    assert result.title == "Test Document"
    assert result.id == doc.id
    mock_repo.create.assert_awaited_once()
    mock_rag.index_document.assert_awaited_once()
    # mark_indexed called with title= because parsed_title differs from fallback
    mock_repo.mark_indexed.assert_awaited_once()
    call_kwargs = mock_repo.mark_indexed.call_args.kwargs
    assert call_kwargs["title"] == "Test Document"


@pytest.mark.asyncio
async def test_upload_document_invalid_file_type() -> None:
    service, mock_repo, _, _, _ = _build_service()

    with pytest.raises(DocumentValidationError, match="Unsupported file format"):
        await service.upload_document(
            file_content=b"binary data",
            filename="archive.zip",
            tenant_id=TENANT_ID,
            uploaded_by=USER_ID,
        )


@pytest.mark.asyncio
async def test_upload_document_max_documents_exceeded() -> None:
    service, mock_repo, _, _, _ = _build_service(max_documents=5)
    mock_repo.get_count.return_value = 5

    with pytest.raises(DocumentValidationError, match="Maximum document limit"):
        await service.upload_document(
            file_content=b"content",
            filename="test.txt",
            tenant_id=TENANT_ID,
            uploaded_by=USER_ID,
        )


@pytest.mark.asyncio
async def test_upload_document_duplicate_filename() -> None:
    service, mock_repo, _, _, _ = _build_service()
    mock_repo.get_count.return_value = 1
    mock_repo.exists_by_filename.return_value = True

    with pytest.raises(DocumentAlreadyExistsError, match="already exists"):
        await service.upload_document(
            file_content=b"content",
            filename="test.txt",
            tenant_id=TENANT_ID,
            uploaded_by=USER_ID,
        )


@pytest.mark.asyncio
async def test_upload_document_indexing_failure_cleans_up() -> None:
    service, mock_repo, mock_rag, _, _ = _build_service()

    mock_repo.get_count.return_value = 0
    mock_repo.exists_by_filename.return_value = False

    doc = _make_document()
    mock_repo.create.return_value = doc

    mock_rag.index_document.return_value = IndexingResult(
        source="test.md",
        chunks_created=0,
        success=False,
        error_message="Embedding API failed",
    )

    with pytest.raises(DocumentIndexingError, match="Embedding API failed"):
        await service.upload_document(
            file_content=b"# Test\n\nContent",
            filename="test.md",
            tenant_id=TENANT_ID,
            uploaded_by=USER_ID,
        )

    # DB record should be cleaned up
    mock_repo.delete.assert_awaited_once_with(doc.id, TENANT_ID)


@pytest.mark.asyncio
async def test_upload_document_pdf_sets_correct_mime_type() -> None:
    """PDF upload uses application/pdf MIME type."""
    service, mock_repo, mock_rag, _, _ = _build_service()

    mock_repo.get_count.return_value = 0
    mock_repo.exists_by_filename.return_value = False

    doc = _make_document(filename="report.pdf")
    doc.file_type = "application/pdf"
    mock_repo.create.return_value = doc

    mock_rag.index_document.return_value = IndexingResult(
        source="report.pdf",
        chunks_created=10,
        success=True,
        parsed_title="Annual Report",
    )

    result = await service.upload_document(
        file_content=b"%PDF-1.4 fake pdf content",
        filename="report.pdf",
        tenant_id=TENANT_ID,
        uploaded_by=USER_ID,
    )

    assert result.chunks_created == 10
    # Verify the MIME type was passed to create
    create_call = mock_repo.create.call_args
    assert create_call.kwargs["file_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_document_empty_file() -> None:
    service, mock_repo, _, _, _ = _build_service()

    with pytest.raises(DocumentValidationError, match="empty"):
        await service.upload_document(
            file_content=b"",
            filename="test.txt",
            tenant_id=TENANT_ID,
            uploaded_by=USER_ID,
        )


# ── delete_document ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_document_success() -> None:
    mock_cache = AsyncMock()
    service, mock_repo, _, mock_store, _ = _build_service(
        semantic_cache=mock_cache,
    )

    doc = _make_document()
    mock_repo.get.return_value = doc
    mock_repo.delete.return_value = True

    result = await service.delete_document(doc.id, TENANT_ID)

    assert "deleted" in result.message.lower()
    mock_store.delete_by_document.assert_awaited_once_with(doc.id, TENANT_ID)
    mock_cache.invalidate.assert_awaited_once_with(TENANT_ID)
    mock_repo.delete.assert_awaited_once_with(doc.id, TENANT_ID)


@pytest.mark.asyncio
async def test_delete_document_not_found() -> None:
    service, mock_repo, _, _, _ = _build_service()
    mock_repo.get.return_value = None

    with pytest.raises(DocumentValidationError, match="not found"):
        await service.delete_document(uuid.uuid4(), TENANT_ID)


@pytest.mark.asyncio
async def test_delete_document_no_cache() -> None:
    """Delete succeeds even when no semantic cache is configured."""
    service, mock_repo, _, mock_store, _ = _build_service(semantic_cache=None)

    doc = _make_document()
    mock_repo.get.return_value = doc
    mock_repo.delete.return_value = True

    result = await service.delete_document(doc.id, TENANT_ID)

    assert "deleted" in result.message.lower()
    mock_store.delete_by_document.assert_awaited_once()


# ── list_documents ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_documents_returns_all() -> None:
    service, mock_repo, _, _, _ = _build_service()

    docs = [_make_document(filename="a.md"), _make_document(filename="b.txt")]
    mock_repo.list_all.return_value = docs

    result = await service.list_documents(TENANT_ID)

    assert result.count == 2
    assert len(result.documents) == 2
    assert result.documents[0].filename == "a.md"
    assert result.documents[1].filename == "b.txt"


@pytest.mark.asyncio
async def test_list_documents_empty() -> None:
    service, mock_repo, _, _, _ = _build_service()
    mock_repo.list_all.return_value = []

    result = await service.list_documents(TENANT_ID)

    assert result.count == 0
    assert result.documents == []


# ── get_document ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_document_found() -> None:
    service, mock_repo, _, _, _ = _build_service()

    doc = _make_document()
    mock_repo.get.return_value = doc

    result = await service.get_document(doc.id, TENANT_ID)

    assert result.id == doc.id
    assert result.filename == doc.filename


@pytest.mark.asyncio
async def test_get_document_not_found() -> None:
    service, mock_repo, _, _, _ = _build_service()
    mock_repo.get.return_value = None

    with pytest.raises(DocumentValidationError, match="not found"):
        await service.get_document(uuid.uuid4(), TENANT_ID)


# ── get_document_count ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_document_count() -> None:
    service, mock_repo, _, _, _ = _build_service()
    mock_repo.get_count.return_value = 7

    count = await service.get_document_count(TENANT_ID)

    assert count == 7
