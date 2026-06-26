# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Object storage infrastructure."""

from retriever.infrastructure.storage.exceptions import (
    ObjectNotFoundError,
    StorageConfigError,
    StorageError,
)
from retriever.infrastructure.storage.memory import InMemoryStorage
from retriever.infrastructure.storage.protocol import S3Client, StorageBackend
from retriever.infrastructure.storage.r2 import R2Storage, build_r2_storage

__all__ = [
    "InMemoryStorage",
    "ObjectNotFoundError",
    "R2Storage",
    "S3Client",
    "StorageBackend",
    "StorageConfigError",
    "StorageError",
    "build_r2_storage",
]
