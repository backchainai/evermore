# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Document module exceptions."""

from __future__ import annotations


class DocumentValidationError(Exception):
    """Raised when a document fails validation (bad type, size, encoding)."""


class DocumentAlreadyExistsError(Exception):
    """Raised when a duplicate filename is uploaded for the same tenant."""


class DocumentIndexingError(Exception):
    """Raised when document indexing into the vector store fails."""
