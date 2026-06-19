# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI routes for document management."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from retriever.infrastructure.database.session import _get_factory
from retriever.models.user import DEFAULT_TENANT_ID
from retriever.modules.auth import AuthUser, require_admin, require_auth
from retriever.modules.documents.exceptions import (
    DocumentAlreadyExistsError,
    DocumentIndexingError,
    DocumentValidationError,
)
from retriever.modules.documents.repos import DocumentRepository
from retriever.modules.documents.schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from retriever.modules.documents.services import DocumentService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _get_document_repository() -> DocumentRepository:
    """Build a DocumentRepository from the shared session factory."""
    return DocumentRepository(_get_factory())


def _get_document_service(
    repo: Annotated[DocumentRepository, Depends(_get_document_repository)],
) -> DocumentService:
    """Build a DocumentService with all dependencies.

    Note: In production this would use proper DI. For the MVP, we create
    a minimal service. The RAG service, vector store, and cache are
    injected from the application's configured providers. For now this
    raises a RuntimeError if the providers are not configured via
    ``configure_document_service``.
    """
    if _service_instance is not None:
        return _service_instance

    # Fallback: service not configured — only repo-based operations work
    raise RuntimeError(
        "DocumentService not configured. "
        "Call configure_document_service() during app startup."
    )


# Module-level service instance, set during app startup
_service_instance: DocumentService | None = None


def configure_document_service(service: DocumentService) -> None:
    """Set the module-level DocumentService instance.

    Called during application startup after all infrastructure
    providers are initialized.

    Args:
        service: Fully configured DocumentService.
    """
    global _service_instance  # noqa: PLW0603
    _service_instance = service


def get_document_service_dependency() -> DocumentService:
    """FastAPI dependency that returns the configured DocumentService."""
    if _service_instance is None:
        raise RuntimeError(
            "DocumentService not configured. "
            "Call configure_document_service() during app startup."
        )
    return _service_instance


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    admin: Annotated[AuthUser, Depends(require_admin)],
    service: Annotated[DocumentService, Depends(get_document_service_dependency)],
) -> DocumentUploadResponse:
    """Upload and index a document (admin only).

    Accepts a multipart file upload, validates the file, indexes it
    into the vector store, and creates a database record.
    """
    filename = file.filename or "unnamed"

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        ) from exc

    try:
        uploaded_by = uuid.UUID(admin.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token",
        ) from exc

    try:
        return await service.upload_document(
            file_content=content,
            filename=filename,
            tenant_id=DEFAULT_TENANT_ID,
            uploaded_by=uploaded_by,
        )
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DocumentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DocumentIndexingError as exc:
        logger.error(
            "document.upload_indexing_failed",
            filename=filename,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {exc}",
        ) from exc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user: Annotated[AuthUser, Depends(require_auth)],
    service: Annotated[DocumentService, Depends(get_document_service_dependency)],
) -> DocumentListResponse:
    """List all documents for the current tenant."""
    return await service.list_documents(DEFAULT_TENANT_ID)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: Annotated[AuthUser, Depends(require_auth)],
    service: Annotated[DocumentService, Depends(get_document_service_dependency)],
) -> DocumentResponse:
    """Get a single document by ID."""
    try:
        return await service.get_document(document_id, DEFAULT_TENANT_ID)
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: uuid.UUID,
    admin: Annotated[AuthUser, Depends(require_admin)],
    service: Annotated[DocumentService, Depends(get_document_service_dependency)],
) -> DocumentDeleteResponse:
    """Delete a document and its indexed chunks (admin only)."""
    try:
        return await service.delete_document(document_id, DEFAULT_TENANT_ID)
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
