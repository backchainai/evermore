# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Document conversion error types for the RAG pipeline."""

from __future__ import annotations


class DocumentConversionError(Exception):
    """Raised when document conversion fails.

    Args:
        message: Human-readable error description.
        source: Source filename or identifier.
        retryable: Whether the operation may succeed on retry.
    """

    def __init__(self, message: str, source: str, *, retryable: bool = False) -> None:
        self.source = source
        self.retryable = retryable
        super().__init__(message)


class UnsupportedFormatError(DocumentConversionError):
    """Raised when a document's format is not supported by any converter."""


class ConversionTimeoutError(DocumentConversionError):
    """Raised when document conversion exceeds the allowed time."""
