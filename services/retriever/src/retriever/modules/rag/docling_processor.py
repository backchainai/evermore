# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Docling-based document processing for the RAG pipeline.

All Docling imports are deferred to method bodies to avoid loading
PyTorch (~800 MB) at module import time. ML models only load when
the first binary document (PDF, DOCX, etc.) is uploaded.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Any

import structlog

from retriever.modules.rag.exceptions import DocumentConversionError
from retriever.modules.rag.loader import (
    TEXT_EXTENSIONS,
    get_extension,
    title_from_filename,
)
from retriever.modules.rag.schemas import (
    Chunk,
    ParsedDocument,
    ProcessingResult,
)

if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker

logger = structlog.get_logger()

# Regex to match markdown H1 heading: # Title (at start of line)
_MARKDOWN_H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)

# Tokenizer model — must match the embedding model used by the app
_TOKENIZER_MODEL = "text-embedding-3-small"

# Extension → document type mapping
_DOC_TYPES: dict[str, str] = {
    ".md": "markdown",
    ".txt": "text",
    ".pdf": "pdf",
    ".docx": "word",
    ".doc": "word",
    ".pptx": "powerpoint",
    ".xlsx": "excel",
    ".html": "html",
    ".htm": "html",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tiff": "image",
    ".bmp": "image",
}


@dataclass(frozen=True)
class DoclingConfig:
    """Configuration for the Docling document processor."""

    ocr_enabled: bool = True
    table_extraction: bool = True
    picture_description: bool = False
    max_pages: int = 100
    chunk_max_tokens: int = 512
    merge_peers: bool = True


def _infer_type(source: str) -> str:
    """Infer document type from filename extension."""
    ext = get_extension(source)
    return _DOC_TYPES.get(ext, "unknown") if ext else "unknown"


def _create_chunker(config: DoclingConfig) -> HybridChunker:
    """Create a HybridChunker with OpenAI tokenizer from config.

    Factored out to avoid duplication between DoclingProcessor
    and FormatAwareProcessor.
    """
    import tiktoken
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

    encoding = tiktoken.encoding_for_model(_TOKENIZER_MODEL)
    tokenizer = OpenAITokenizer(
        tokenizer=encoding,
        max_tokens=config.chunk_max_tokens,
    )
    return HybridChunker(
        tokenizer=tokenizer,
        merge_peers=config.merge_peers,
    )


def _build_chunks(
    chunker: Any,
    dl_doc: Any,
    source: str,
    title: str,
) -> list[Chunk]:
    """Convert Docling chunks into our Chunk models.

    Args:
        chunker: Docling HybridChunker instance.
        dl_doc: Docling DoclingDocument.
        source: Source filename.
        title: Document title.

    Returns:
        List of Chunk objects with contextualized content.
    """
    return [
        Chunk(
            content=chunker.contextualize(dc),
            source=source,
            section=" > ".join(dc.meta.headings) if dc.meta.headings else "",
            position=i,
            title=title,
        )
        for i, dc in enumerate(chunker.chunk(dl_doc=dl_doc))
    ]


class DoclingProcessor:
    """Document processor using Docling's ML pipeline.

    Handles binary formats (PDF, DOCX, PPTX, XLSX, HTML, images)
    with full layout analysis, OCR, and table extraction.

    Thread safety: ``converter.convert()`` is guarded by a lock.
    Lazy initialization: Docling imports and model loading happen on
    first call to ``process()``, not at import time.
    """

    def __init__(self, config: DoclingConfig) -> None:
        self.config = config
        self._converter: DocumentConverter | None = None
        self._chunker: HybridChunker | None = None
        self._lock = threading.Lock()

    def _get_converter(self) -> DocumentConverter:
        """Lazily initialize the Docling DocumentConverter."""
        if self._converter is not None:
            return self._converter

        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            EasyOcrOptions,
            PdfPipelineOptions,
            TableFormerMode,
            TableStructureOptions,
        )
        from docling.document_converter import (
            DocumentConverter,
            PdfFormatOption,
            PowerpointFormatOption,
            WordFormatOption,
        )
        from docling.pipeline.simple_pipeline import SimplePipeline

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.config.ocr_enabled
        if self.config.ocr_enabled:
            pipeline_options.ocr_options = EasyOcrOptions(lang=["en"])

        if self.config.table_extraction:
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options = TableStructureOptions(
                mode=TableFormerMode.ACCURATE,
                do_cell_matching=True,
            )

        self._converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.PPTX,
                InputFormat.XLSX,
                InputFormat.HTML,
                InputFormat.IMAGE,
                InputFormat.MD,
            ],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                ),
                InputFormat.DOCX: WordFormatOption(
                    pipeline_cls=SimplePipeline,
                ),
                InputFormat.PPTX: PowerpointFormatOption(
                    pipeline_cls=SimplePipeline,
                ),
            },
        )

        logger.info(
            "docling_converter_initialized",
            ocr=self.config.ocr_enabled,
            tables=self.config.table_extraction,
        )
        return self._converter

    def _get_chunker(self) -> HybridChunker:
        """Lazily initialize the HybridChunker with OpenAI tokenizer."""
        if self._chunker is not None:
            return self._chunker
        self._chunker = _create_chunker(self.config)
        return self._chunker

    def process(self, content: bytes, source: str) -> ProcessingResult:
        """Convert and chunk a document using Docling's ML pipeline.

        Args:
            content: Raw file bytes.
            source: Source filename or identifier.

        Returns:
            Processing result with parsed document and chunks.

        Raises:
            DocumentConversionError: If conversion fails.
        """
        from docling.datamodel.base_models import ConversionStatus
        from docling_core.types.io import DocumentStream

        converter = self._get_converter()
        chunker = self._get_chunker()

        stream = DocumentStream(name=source, stream=BytesIO(content))

        with self._lock:
            result = converter.convert(stream)

        if result.status == ConversionStatus.FAILURE:
            errors = getattr(result, "errors", [])
            raise DocumentConversionError(
                f"Document conversion failed for {source}: {errors}",
                source=source,
            )

        if result.status == ConversionStatus.PARTIAL_SUCCESS:
            logger.warning("docling_partial_conversion", source=source)

        dl_doc = result.document
        title = dl_doc.name or title_from_filename(source)
        doc_type = _infer_type(source)

        chunks = _build_chunks(chunker, dl_doc, source, title)

        logger.info(
            "docling_document_processed",
            source=source,
            title=title,
            chunks_created=len(chunks),
            document_type=doc_type,
        )

        parsed = ParsedDocument(
            content=dl_doc.export_to_markdown(),
            source=source,
            title=title,
            document_type=doc_type,
        )
        return ProcessingResult(document=parsed, chunks=chunks)


class FormatAwareProcessor:
    """Routes documents to the appropriate processing pipeline.

    - ``.md`` and ``.txt`` files use Docling's lightweight
      ``SimplePipeline`` — no ML models loaded.
    - All other formats delegate to ``DoclingProcessor`` with full ML
      pipeline (lazy-initialized on first binary upload).

    Implements the ``DocumentProcessor`` protocol.
    """

    def __init__(self, docling: DoclingProcessor) -> None:
        self._docling = docling
        self._text_converter: DocumentConverter | None = None
        self._lock = threading.Lock()

    def _get_text_converter(self) -> DocumentConverter:
        """Lazily initialize a lightweight converter for text formats."""
        if self._text_converter is not None:
            return self._text_converter

        with self._lock:
            if self._text_converter is not None:
                return self._text_converter

            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import (
                DocumentConverter,
                MarkdownFormatOption,
            )
            from docling.pipeline.simple_pipeline import SimplePipeline

            self._text_converter = DocumentConverter(
                allowed_formats=[InputFormat.MD],
                format_options={
                    InputFormat.MD: MarkdownFormatOption(
                        pipeline_cls=SimplePipeline,
                    ),
                },
            )
        return self._text_converter

    def process(self, content: bytes, source: str) -> ProcessingResult:
        """Process a document, routing by format.

        Args:
            content: Raw file bytes.
            source: Source filename or identifier.

        Returns:
            Processing result with parsed document and chunks.
        """
        ext = get_extension(source)
        if ext is not None and ext in TEXT_EXTENSIONS:
            return self._process_text(content, source)
        return self._docling.process(content, source)

    def _process_text(self, content: bytes, source: str) -> ProcessingResult:
        """Process a text/markdown file via Docling's lightweight pipeline.

        Args:
            content: Raw file bytes (must be valid UTF-8).
            source: Source filename.

        Returns:
            Processing result.

        Raises:
            DocumentConversionError: If conversion fails or encoding invalid.
        """
        from docling.datamodel.base_models import ConversionStatus
        from docling_core.types.io import DocumentStream

        # Decode to verify UTF-8 (needed for title extraction + fallback chunk)
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentConversionError(
                f"Text file is not valid UTF-8: {source}",
                source=source,
            ) from exc

        converter = self._get_text_converter()
        chunker = self._docling._get_chunker()

        # Docling's format detection uses the filename extension.
        # .txt has no dedicated InputFormat, so we hint it as .md
        # (plain text is valid markdown).
        stream_name = source if source.lower().endswith(".md") else f"{source}.md"
        stream = DocumentStream(name=stream_name, stream=BytesIO(content))
        result = converter.convert(stream)

        if result.status == ConversionStatus.FAILURE:
            raise DocumentConversionError(
                f"Text conversion failed for {source}",
                source=source,
            )

        dl_doc = result.document

        # Title: prefer markdown H1, then Docling's name, then filename stem
        title: str | None = None
        if source.lower().endswith(".md"):
            match = _MARKDOWN_H1_PATTERN.search(text_content)
            if match:
                title = match.group(1).strip()
        if not title:
            title = dl_doc.name or title_from_filename(source)

        doc_type = _infer_type(source)
        chunks = _build_chunks(chunker, dl_doc, source, title)

        # Fallback: if Docling produces no chunks for non-empty text
        if not chunks and text_content.strip():
            chunks = [
                Chunk(
                    content=text_content.strip(),
                    source=source,
                    section="",
                    position=0,
                    title=title,
                )
            ]

        logger.info(
            "docling_text_processed",
            source=source,
            title=title,
            chunks_created=len(chunks),
        )

        parsed = ParsedDocument(
            content=dl_doc.export_to_markdown(),
            source=source,
            title=title,
            document_type=doc_type,
        )
        return ProcessingResult(document=parsed, chunks=chunks)
