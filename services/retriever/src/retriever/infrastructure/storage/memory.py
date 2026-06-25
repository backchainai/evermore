# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""In-memory storage backend for tests and local development."""

from __future__ import annotations

from retriever.infrastructure.storage.exceptions import ObjectNotFoundError


class InMemoryStorage:
    """A dict-backed StorageBackend fake.

    Holds objects in process memory; ``url`` returns a deterministic fake
    ``memory://<key>`` URL rather than a real presigned URL.
    """

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def put(
        self, key: str, data: bytes, *, content_type: str | None = None
    ) -> None:
        """Store ``data`` under ``key`` (content type is ignored)."""
        self._objects[key] = data

    async def get(self, key: str) -> bytes:
        """Return the bytes stored under ``key``.

        Raises:
            ObjectNotFoundError: If no object exists for ``key``.
        """
        try:
            return self._objects[key]
        except KeyError as exc:
            raise ObjectNotFoundError(key) from exc

    async def delete(self, key: str) -> None:
        """Delete the object stored under ``key``.

        Idempotent: deleting a missing key is a no-op, matching S3/R2 semantics.
        """
        self._objects.pop(key, None)

    async def url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a deterministic fake URL for ``key``."""
        return f"memory://{key}"
