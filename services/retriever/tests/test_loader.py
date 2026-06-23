"""Tests for the document loader and file validation."""

from __future__ import annotations

import pytest

from retriever.modules.rag.loader import (
    BINARY_EXTENSIONS,
    MAX_FILE_SIZE_BINARY,
    MAX_FILE_SIZE_TEXT,
    SUPPORTED_EXTENSIONS,
    TEXT_EXTENSIONS,
    FileValidationError,
    validate_file,
)


class TestValidateFile:
    """Tests for validate_file."""

    def test_valid_markdown_file(self) -> None:
        """Valid markdown file passes validation."""
        validate_file("document.md", 1000)

    def test_valid_text_file(self) -> None:
        """Valid text file passes validation."""
        validate_file("notes.txt", 500)

    def test_valid_pdf_file(self) -> None:
        """Valid PDF file passes validation."""
        validate_file("report.pdf", 1_000_000)

    def test_valid_docx_file(self) -> None:
        """Valid DOCX file passes validation."""
        validate_file("document.docx", 5_000_000)

    def test_valid_pptx_file(self) -> None:
        """Valid PPTX file passes validation."""
        validate_file("slides.pptx", 10_000_000)

    def test_valid_xlsx_file(self) -> None:
        """Valid XLSX file passes validation."""
        validate_file("data.xlsx", 2_000_000)

    def test_valid_html_file(self) -> None:
        """Valid HTML file passes validation."""
        validate_file("page.html", 500_000)

    def test_valid_htm_file(self) -> None:
        """Valid HTM file passes validation."""
        validate_file("page.htm", 500_000)

    def test_valid_image_files(self) -> None:
        """Image files pass validation."""
        for ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
            validate_file(f"image{ext}", 5_000_000)

    def test_invalid_extension_raises(self) -> None:
        """Unsupported extension raises FileValidationError."""
        with pytest.raises(FileValidationError, match="Unsupported file format"):
            validate_file("archive.zip", 1000)

    def test_no_extension_raises(self) -> None:
        """File without extension raises FileValidationError."""
        with pytest.raises(FileValidationError, match="no extension"):
            validate_file("noext", 1000)

    def test_text_file_too_large_raises(self) -> None:
        """Text file exceeding 1 MB raises FileValidationError."""
        with pytest.raises(FileValidationError, match="too large"):
            validate_file("big.md", MAX_FILE_SIZE_TEXT + 1)

    def test_binary_file_too_large_raises(self) -> None:
        """Binary file exceeding 20 MB raises FileValidationError."""
        with pytest.raises(FileValidationError, match="too large"):
            validate_file("big.pdf", MAX_FILE_SIZE_BINARY + 1)

    def test_binary_file_within_limit_passes(self) -> None:
        """Binary file at 5 MB passes (under 20 MB limit)."""
        validate_file("report.pdf", 5_000_000)

    def test_hidden_file_raises(self) -> None:
        """Hidden files (starting with .) raise FileValidationError."""
        with pytest.raises(FileValidationError, match="Hidden files"):
            validate_file(".hidden.md", 100)

    def test_empty_file_raises(self) -> None:
        """Empty file raises FileValidationError."""
        with pytest.raises(FileValidationError, match="empty"):
            validate_file("empty.md", 0)

    def test_exactly_max_text_size_passes(self) -> None:
        """Text file at exactly max size passes validation."""
        validate_file("exact.md", MAX_FILE_SIZE_TEXT)

    def test_exactly_max_binary_size_passes(self) -> None:
        """Binary file at exactly max size passes validation."""
        validate_file("exact.pdf", MAX_FILE_SIZE_BINARY)


class TestExtensionConstants:
    """Tests for extension set constants."""

    def test_text_extensions(self) -> None:
        """TEXT_EXTENSIONS contains expected types."""
        assert ".md" in TEXT_EXTENSIONS
        assert ".txt" in TEXT_EXTENSIONS
        assert ".pdf" not in TEXT_EXTENSIONS

    def test_binary_extensions(self) -> None:
        """BINARY_EXTENSIONS contains expected types."""
        assert ".pdf" in BINARY_EXTENSIONS
        assert ".docx" in BINARY_EXTENSIONS
        assert ".pptx" in BINARY_EXTENSIONS
        assert ".xlsx" in BINARY_EXTENSIONS
        assert ".html" in BINARY_EXTENSIONS
        assert ".png" in BINARY_EXTENSIONS
        assert ".md" not in BINARY_EXTENSIONS

    def test_supported_is_union(self) -> None:
        """SUPPORTED_EXTENSIONS is the union of text and binary."""
        assert SUPPORTED_EXTENSIONS == TEXT_EXTENSIONS | BINARY_EXTENSIONS
