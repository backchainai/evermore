# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Document loading and validation for the RAG pipeline.

Validates file uploads by extension and size. Format-aware limits
allow larger binary documents (PDF, DOCX, etc.) while keeping text
uploads lightweight.
"""

from __future__ import annotations

# Supported extension sets — shared with FormatAwareProcessor for routing
TEXT_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt"})
BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".html",
        ".htm",
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".bmp",
    }
)
SUPPORTED_EXTENSIONS: frozenset[str] = TEXT_EXTENSIONS | BINARY_EXTENSIONS

# Size limits
MAX_FILE_SIZE_TEXT: int = 1_048_576  # 1 MB for text files
MAX_FILE_SIZE_BINARY: int = 20_971_520  # 20 MB for binary files


class FileValidationError(Exception):
    """Raised when a file fails upload validation."""


def get_extension(filename: str) -> str | None:
    """Extract lowercase extension from a filename.

    Args:
        filename: The filename to inspect.

    Returns:
        Extension including the dot (e.g. ".pdf"), or None if no extension.
    """
    dot_pos = filename.rfind(".")
    if dot_pos < 0:
        return None
    return filename[dot_pos:].lower()


def title_from_filename(source: str) -> str:
    """Extract a title from a filename by stripping the extension.

    Args:
        source: Filename or source identifier.

    Returns:
        Filename stem (without extension).
    """
    dot_pos = source.rfind(".")
    if dot_pos > 0:
        return source[:dot_pos]
    return source


def validate_file(filename: str, content_length: int) -> None:
    """Validate a file for upload.

    Checks filename extension, size, and hidden-file rules.
    Applies format-aware size limits: text files limited to 1 MB,
    binary files limited to 20 MB.

    Args:
        filename: The name of the file to validate.
        content_length: Size of the file content in bytes.

    Raises:
        FileValidationError: If validation fails.
    """
    # No hidden files (starting with .)
    if filename.startswith("."):
        raise FileValidationError(f"Hidden files are not allowed: {filename}")

    # Check extension
    extension = get_extension(filename)
    if extension is None:
        raise FileValidationError(
            f"File has no extension: {filename}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if extension not in SUPPORTED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file format: {extension}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Format-aware size limit
    max_size = (
        MAX_FILE_SIZE_TEXT if extension in TEXT_EXTENSIONS else MAX_FILE_SIZE_BINARY
    )
    if content_length > max_size:
        raise FileValidationError(
            f"File too large: {content_length} bytes (max {max_size} bytes)"
        )

    if content_length == 0:
        raise FileValidationError("File is empty")
