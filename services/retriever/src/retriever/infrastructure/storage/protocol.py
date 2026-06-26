# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Protocol definitions for object storage backends."""

from __future__ import annotations

from typing import Any, Protocol


class StorageBackend(Protocol):
    """Protocol for object storage implementations.

    This allows swapping between an R2/S3 backend and an in-memory fake
    without changing business logic.
    """

    async def put(
        self, key: str, data: bytes, *, content_type: str | None = None
    ) -> None:
        """Store ``data`` under ``key``, overwriting any existing object.

        Args:
            key: The object key (path) within the backend.
            data: The raw bytes to store.
            content_type: Optional MIME type recorded with the object.

        Raises:
            StorageError: If the store operation fails.
        """
        ...

    async def get(self, key: str) -> bytes:
        """Return the bytes stored under ``key``.

        Args:
            key: The object key (path) within the backend.

        Returns:
            The raw bytes of the stored object.

        Raises:
            ObjectNotFoundError: If no object exists for ``key``.
            StorageError: If the fetch fails for any other reason.
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete the object stored under ``key``.

        Delete is idempotent: deleting a key that does not exist is a no-op
        and does not raise.

        Args:
            key: The object key (path) within the backend.

        Raises:
            StorageError: If the delete fails for any other reason.
        """
        ...

    async def url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a presigned GET URL for ``key``.

        Args:
            key: The object key (path) within the backend.
            expires_in: Lifetime of the presigned URL in seconds.

        Returns:
            A URL that grants temporary read access to the object.

        Raises:
            StorageError: If URL generation fails.
        """
        ...


class S3Client(Protocol):
    """Narrow structural protocol for the boto3 S3 client methods R2Storage uses.

    Declaring only the methods we call lets mypy --strict type the injected
    client without depending on boto3 type stubs. The boto3 client is dynamically
    generated, so signatures are kept permissive (``**kwargs``) to match it.
    """

    def put_object(self, **kwargs: Any) -> Any:
        """Upload an object to a bucket."""
        ...

    def get_object(self, **kwargs: Any) -> Any:
        """Retrieve an object from a bucket."""
        ...

    def delete_object(self, **kwargs: Any) -> Any:
        """Delete an object from a bucket."""
        ...

    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, Any], ExpiresIn: int
    ) -> str:
        """Generate a presigned URL for a client method."""
        ...
