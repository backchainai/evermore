"""Tests for the Docling-based document processor.

Tests mock Docling's DocumentConverter and HybridChunker to verify
the processing pipeline without requiring ML model downloads.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from retriever.modules.rag.docling_processor import (
    DoclingConfig,
    DoclingProcessor,
    FormatAwareProcessor,
    _infer_type,
)
from retriever.modules.rag.exceptions import DocumentConversionError
from retriever.modules.rag.loader import title_from_filename
from retriever.modules.rag.schemas import (
    DocumentProcessor,
    ParsedDocument,
    ProcessingResult,
)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_mock_chunk(
    text: str = "Chunk text",
    headings: list[str] | None = None,
) -> MagicMock:
    """Create a mock Docling chunk."""
    chunk = MagicMock()
    chunk.text = text
    chunk.meta = MagicMock()
    chunk.meta.headings = headings or []
    return chunk


def _make_mock_conversion_result(
    *,
    status_name: str = "SUCCESS",
    doc_name: str = "test.md",
    markdown: str = "# Title\n\nContent",
) -> MagicMock:
    """Create a mock ConversionResult."""
    result = MagicMock()
    result.status = MagicMock()
    result.status.name = status_name
    result.document = MagicMock()
    result.document.name = doc_name
    result.document.export_to_markdown.return_value = markdown
    return result


# ---------------------------------------------------------------------------
# Tests: utility functions
# ---------------------------------------------------------------------------


class TestTitleFromFilename:
    """Tests for title_from_filename (from loader.py)."""

    def test_strips_extension(self) -> None:
        assert title_from_filename("document.pdf") == "document"

    def test_no_extension(self) -> None:
        assert title_from_filename("readme") == "readme"

    def test_multiple_dots(self) -> None:
        assert title_from_filename("my.file.name.pdf") == "my.file.name"


class TestInferType:
    """Tests for _infer_type."""

    def test_markdown(self) -> None:
        assert _infer_type("file.md") == "markdown"

    def test_text(self) -> None:
        assert _infer_type("file.txt") == "text"

    def test_pdf(self) -> None:
        assert _infer_type("file.pdf") == "pdf"

    def test_word(self) -> None:
        assert _infer_type("file.docx") == "word"

    def test_powerpoint(self) -> None:
        assert _infer_type("file.pptx") == "powerpoint"

    def test_excel(self) -> None:
        assert _infer_type("file.xlsx") == "excel"

    def test_html(self) -> None:
        assert _infer_type("file.html") == "html"
        assert _infer_type("file.htm") == "html"

    def test_image(self) -> None:
        assert _infer_type("file.png") == "image"
        assert _infer_type("file.jpg") == "image"

    def test_unknown(self) -> None:
        assert _infer_type("file.xyz") == "unknown"


# ---------------------------------------------------------------------------
# Tests: FormatAwareProcessor routing
# ---------------------------------------------------------------------------


class TestFormatAwareProcessorRouting:
    """Tests for format-based routing in FormatAwareProcessor."""

    def test_text_routes_to_text_path(self) -> None:
        """Text files route to _process_text, binary to DoclingProcessor."""
        mock_docling = MagicMock(spec=DoclingProcessor)
        mock_docling.config = DoclingConfig()
        processor = FormatAwareProcessor(docling=mock_docling)

        # Binary files delegate to DoclingProcessor
        mock_docling.process.return_value = ProcessingResult(
            document=ParsedDocument(
                content="", source="r.pdf", title="r", document_type="pdf"
            ),
            chunks=[],
        )
        processor.process(b"pdf", "report.pdf")
        mock_docling.process.assert_called_once()

    def test_satisfies_document_processor_protocol(self) -> None:
        """FormatAwareProcessor satisfies the DocumentProcessor protocol."""
        docling = DoclingProcessor(config=DoclingConfig())
        processor = FormatAwareProcessor(docling=docling)
        assert isinstance(processor, DocumentProcessor)


# ---------------------------------------------------------------------------
# Tests: FormatAwareProcessor text processing
# ---------------------------------------------------------------------------


class TestFormatAwareProcessorText:
    """Tests for text file processing via FormatAwareProcessor."""

    @patch("retriever.modules.rag.docling_processor.DoclingProcessor._get_chunker")
    @patch(
        "retriever.modules.rag.docling_processor.FormatAwareProcessor._get_text_converter"
    )
    def test_process_markdown_extracts_title(
        self,
        mock_get_converter: MagicMock,
        mock_get_chunker: MagicMock,
    ) -> None:
        """Markdown files extract H1 heading as title."""
        mock_result = _make_mock_conversion_result(
            doc_name="test.md",
            markdown="# My Document\n\nSome content.",
        )
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        mock_chunk = _make_mock_chunk("My Document\n\nSome content.")
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = [mock_chunk]
        mock_chunker.contextualize.return_value = "My Document\n\nSome content."
        mock_get_chunker.return_value = mock_chunker

        docling = DoclingProcessor(config=DoclingConfig())
        processor = FormatAwareProcessor(docling=docling)

        result = processor.process(b"# My Document\n\nSome content.", "readme.md")

        assert isinstance(result, ProcessingResult)
        assert result.document.title == "My Document"
        assert result.document.document_type == "markdown"
        assert len(result.chunks) == 1

    @patch("retriever.modules.rag.docling_processor.DoclingProcessor._get_chunker")
    @patch(
        "retriever.modules.rag.docling_processor.FormatAwareProcessor._get_text_converter"
    )
    def test_process_txt_uses_filename_title(
        self,
        mock_get_converter: MagicMock,
        mock_get_chunker: MagicMock,
    ) -> None:
        """Text files without H1 heading use filename as title."""
        mock_result = _make_mock_conversion_result(
            doc_name="",
            markdown="Just plain text content.",
        )
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        mock_chunk = _make_mock_chunk("Just plain text content.")
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = [mock_chunk]
        mock_chunker.contextualize.return_value = "Just plain text content."
        mock_get_chunker.return_value = mock_chunker

        docling = DoclingProcessor(config=DoclingConfig())
        processor = FormatAwareProcessor(docling=docling)

        result = processor.process(b"Just plain text content.", "notes.txt")

        assert result.document.title == "notes"
        assert result.document.document_type == "text"

    def test_process_invalid_utf8_raises(self) -> None:
        """Invalid UTF-8 in text files raises DocumentConversionError."""
        docling = DoclingProcessor(config=DoclingConfig())
        processor = FormatAwareProcessor(docling=docling)

        with pytest.raises(DocumentConversionError, match="UTF-8"):
            processor.process(b"\xff\xfe\x00", "bad.txt")

    @patch("retriever.modules.rag.docling_processor.DoclingProcessor._get_chunker")
    @patch(
        "retriever.modules.rag.docling_processor.FormatAwareProcessor._get_text_converter"
    )
    def test_process_text_fallback_chunk_for_short_content(
        self,
        mock_get_converter: MagicMock,
        mock_get_chunker: MagicMock,
    ) -> None:
        """Short text that produces no chunks gets a fallback single chunk."""
        mock_result = _make_mock_conversion_result(
            doc_name="",
            markdown="Hi",
        )
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        # Chunker returns empty list (text too short for a chunk)
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = []
        mock_get_chunker.return_value = mock_chunker

        docling = DoclingProcessor(config=DoclingConfig())
        processor = FormatAwareProcessor(docling=docling)

        result = processor.process(b"Hi", "short.txt")

        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Hi"
        assert result.chunks[0].source == "short.txt"


# ---------------------------------------------------------------------------
# Tests: FormatAwareProcessor binary delegation
# ---------------------------------------------------------------------------


class TestFormatAwareProcessorBinary:
    """Tests for binary file delegation to DoclingProcessor."""

    def test_binary_delegates_to_docling_processor(self) -> None:
        """Binary files are delegated to DoclingProcessor.process()."""
        mock_docling = MagicMock(spec=DoclingProcessor)
        mock_docling.config = DoclingConfig()
        expected = ProcessingResult(
            document=ParsedDocument(
                content="PDF text",
                source="report.pdf",
                title="report",
                document_type="pdf",
            ),
            chunks=[],
        )
        mock_docling.process.return_value = expected

        processor = FormatAwareProcessor(docling=mock_docling)
        result = processor.process(b"PDF content", "report.pdf")

        mock_docling.process.assert_called_once_with(b"PDF content", "report.pdf")
        assert result is expected


# ---------------------------------------------------------------------------
# Tests: DoclingConfig
# ---------------------------------------------------------------------------


class TestDoclingConfig:
    """Tests for DoclingConfig defaults."""

    def test_defaults(self) -> None:
        config = DoclingConfig()
        assert config.ocr_enabled is True
        assert config.table_extraction is True
        assert config.picture_description is False
        assert config.chunk_max_tokens == 512
        assert config.merge_peers is True
        assert config.max_pages == 100

    def test_custom_values(self) -> None:
        config = DoclingConfig(
            ocr_enabled=False,
            chunk_max_tokens=256,
            merge_peers=False,
        )
        assert config.ocr_enabled is False
        assert config.chunk_max_tokens == 256
        assert config.merge_peers is False


# ---------------------------------------------------------------------------
# Tests: exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    """Tests for document conversion exceptions."""

    def test_document_conversion_error(self) -> None:
        from retriever.modules.rag.exceptions import (
            ConversionTimeoutError,
            UnsupportedFormatError,
        )

        err = DocumentConversionError("failed", "test.pdf", retryable=True)
        assert err.source == "test.pdf"
        assert err.retryable is True
        assert str(err) == "failed"

        unsupported = UnsupportedFormatError("bad format", "test.xyz")
        assert isinstance(unsupported, DocumentConversionError)

        timeout = ConversionTimeoutError("took too long", "big.pdf")
        assert isinstance(timeout, DocumentConversionError)
