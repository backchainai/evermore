# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Document repository — async persistence for RAG source documents."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.models.document import Document

logger = structlog.get_logger(__name__)


class DocumentRepository:
    """Async repository for document records.

    Handles creating, retrieving, listing, and deleting document
    metadata scoped to a tenant.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        filename: str,
        title: str,
        file_path: str,
        tenant_id: uuid.UUID,
        *,
        file_size_bytes: int = 0,
        file_type: str = "text/plain",
        uploaded_by: uuid.UUID | None = None,
        description: str | None = None,
        is_indexed: bool = False,
    ) -> Document:
        """Persist a new document record.

        Args:
            filename: Original upload filename.
            title: Extracted or derived document title.
            file_path: Storage path (ephemeral or reference).
            tenant_id: Tenant scope.
            file_size_bytes: Size of the file in bytes.
            file_type: MIME type of the file.
            uploaded_by: UUID of the uploading user.
            description: Optional description of the document.
            is_indexed: Whether the document has been indexed.

        Returns:
            The persisted Document instance.
        """
        document = Document(
            filename=filename,
            title=title,
            file_path=file_path,
            tenant_id=tenant_id,
            file_size_bytes=file_size_bytes,
            file_type=file_type,
            uploaded_by=uploaded_by,
            description=description,
            is_indexed=is_indexed,
        )

        async with self._session_factory() as session:
            session.add(document)
            await session.commit()
            await session.refresh(document)

        logger.debug(
            "document.created",
            document_id=str(document.id),
            filename=filename,
            tenant_id=str(tenant_id),
        )

        return document

    async def mark_indexed(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        *,
        title: str | None = None,
    ) -> None:
        """Mark a document as indexed, optionally updating its title.

        Combines the indexed flag and title update in a single DB round-trip.

        Args:
            document_id: The document's UUID.
            tenant_id: Tenant scope.
            title: New title (if the processor extracted a better one).
        """
        async with self._session_factory() as session:
            doc = await session.get(Document, document_id)
            if doc and doc.tenant_id == tenant_id:
                doc.is_indexed = True
                if title is not None:
                    doc.title = title
                await session.commit()

    async def get(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Document | None:
        """Retrieve a document by ID within a tenant.

        Args:
            document_id: The document's UUID.
            tenant_id: Tenant scope.

        Returns:
            The Document if found, otherwise None.
        """
        stmt = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_all(
        self,
        tenant_id: uuid.UUID,
    ) -> list[Document]:
        """List all documents for a tenant, newest first.

        Args:
            tenant_id: Tenant scope.

        Returns:
            Documents ordered by created_at DESC.
        """
        stmt = (
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            rows = list(result.scalars().all())

        logger.debug(
            "documents.listed",
            tenant_id=str(tenant_id),
            count=len(rows),
        )

        return rows

    async def delete(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Delete a document by ID within a tenant.

        Args:
            document_id: The document's UUID.
            tenant_id: Tenant scope.

        Returns:
            True if a document was found and deleted, False otherwise.
        """
        stmt = delete(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )

        async with self._session_factory() as session:
            cursor: CursorResult[tuple[()]] = await session.execute(stmt)  # type: ignore[assignment]
            await session.commit()
            deleted: int = cursor.rowcount

        if deleted > 0:
            logger.info(
                "document.deleted",
                document_id=str(document_id),
                tenant_id=str(tenant_id),
            )

        return deleted > 0

    async def get_count(
        self,
        tenant_id: uuid.UUID,
    ) -> int:
        """Return the number of documents for a tenant.

        Args:
            tenant_id: Tenant scope.

        Returns:
            Document count.
        """
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant_id)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            count: int = result.scalar_one()

        return count

    async def exists_by_filename(
        self,
        filename: str,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Check if a document with the given filename exists for a tenant.

        Args:
            filename: Filename to check.
            tenant_id: Tenant scope.

        Returns:
            True if a document with the filename exists.
        """
        stmt = select(
            select(Document)
            .where(
                Document.filename == filename,
                Document.tenant_id == tenant_id,
            )
            .exists()
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return bool(result.scalar())
