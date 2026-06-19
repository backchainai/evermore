# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Schemas for the RAG module.

Pydantic models and Protocol definitions for document processing
and retrieval-augmented generation.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from retriever.infrastructure.vectordb.protocol import SearchResult


class ParsedDocument(BaseModel, frozen=True):
    """A parsed document with extracted metadata."""

    content: str
    source: str
    title: str
    document_type: str


class Chunk(BaseModel, frozen=True):
    """A chunk of text from a document.

    Represents a segment of a document that can be embedded and stored
    in the vector database for retrieval.
    """

    content: str
    source: str
    section: str
    position: int
    title: str = ""
    metadata: dict[str, str] = {}

    def model_post_init(self, __context: Any) -> None:
        """Populate metadata from fields if not provided."""
        if not self.metadata:
            # Use object.__setattr__ since the model is frozen
            object.__setattr__(
                self,
                "metadata",
                {
                    "source": self.source,
                    "section": self.section,
                    "position": str(self.position),
                    "title": self.title,
                },
            )


class ProcessingResult(BaseModel, frozen=True):
    """Result of processing a document through parse + chunk pipeline."""

    document: ParsedDocument
    chunks: list[Chunk]


@runtime_checkable
class DocumentProcessor(Protocol):
    """Protocol for combined document parsing and chunking.

    Implementations accept raw bytes and return structured chunks
    ready for embedding. This replaces the separate DocumentParser
    and DocumentChunker protocols to avoid stateful caching of
    intermediate representations.
    """

    def process(self, content: bytes, source: str) -> ProcessingResult:
        """Parse and chunk a document in one step.

        Args:
            content: Raw file bytes.
            source: Source filename or identifier.

        Returns:
            Processing result with parsed document and chunks.

        Raises:
            DocumentConversionError: If conversion fails.
            UnsupportedFormatError: If the format is not supported.
        """
        ...


class ChunkWithScore(BaseModel, frozen=True):
    """A retrieved chunk with its similarity score."""

    content: str
    source: str
    section: str
    score: float
    title: str = ""

    @classmethod
    def from_search_result(cls, result: SearchResult) -> ChunkWithScore:
        """Create from a vectordb SearchResult.

        Args:
            result: Search result from the vector store.

        Returns:
            ChunkWithScore with fields extracted from the result.
        """
        return cls(
            content=result["content"],
            source=result["source"],
            section="",
            score=result["score"],
            title=result.get("title", ""),
        )


class IndexingResult(BaseModel, frozen=True):
    """Result of indexing a document."""

    source: str
    chunks_created: int
    success: bool
    error_message: str | None = None
    parsed_title: str | None = None


class RAGResponse(BaseModel, frozen=True):
    """Response from the RAG pipeline."""

    answer: str
    chunks_used: list[ChunkWithScore]
    question: str
    confidence_level: str = "medium"
    confidence_score: float = 0.5
    blocked: bool = False
    blocked_reason: str | None = None
