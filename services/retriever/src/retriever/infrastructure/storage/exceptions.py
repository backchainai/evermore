# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Custom exceptions for object storage operations."""


class StorageError(Exception):
    """Base exception for object storage errors."""


class ObjectNotFoundError(StorageError):
    """Raised when a requested object does not exist in the backend."""


class StorageConfigError(StorageError):
    """Raised when the storage backend is misconfigured (missing deps or settings)."""
