"""Tests for RAG prompt building."""

from __future__ import annotations

from retriever.modules.rag.prompts import (
    FALLBACK_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    build_rag_prompt,
)


class TestBuildRagPrompt:
    """Tests for build_rag_prompt."""

    def test_formats_chunks_correctly(self) -> None:
        """Chunks are formatted as numbered source blocks."""
        chunks: list[tuple[str, str, float]] = [
            ("Content A", "doc_a.md", 0.95),
            ("Content B", "doc_b.md", 0.85),
        ]
        result = build_rag_prompt(chunks)

        assert "[Source 1: doc_a.md]" in result
        assert "Content A" in result
        assert "[Source 2: doc_b.md]" in result
        assert "Content B" in result
        # Sources separated by horizontal rule
        assert "---" in result

    def test_empty_chunks_returns_no_documents_message(self) -> None:
        """Empty chunk list produces a 'no documents' placeholder."""
        result = build_rag_prompt([])
        assert "[No relevant documents found]" in result

    def test_single_chunk(self) -> None:
        """Single chunk is formatted without separator."""
        chunks: list[tuple[str, str, float]] = [
            ("Only content", "only.md", 0.99),
        ]
        result = build_rag_prompt(chunks)

        assert "[Source 1: only.md]" in result
        assert "Only content" in result

    def test_score_not_included_in_output(self) -> None:
        """Score values are not leaked into the prompt text."""
        chunks: list[tuple[str, str, float]] = [
            ("Content", "doc.md", 0.12345),
        ]
        result = build_rag_prompt(chunks)

        assert "0.12345" not in result


class TestRagSystemPrompt:
    """Tests for the RAG system prompt template."""

    def test_contains_strict_rules(self) -> None:
        """RAG system prompt contains key constraint phrases."""
        assert "STRICT RULES" in RAG_SYSTEM_PROMPT
        assert "ONLY use information" in RAG_SYSTEM_PROMPT
        assert "NEVER" in RAG_SYSTEM_PROMPT

    def test_contains_context_placeholder(self) -> None:
        """RAG system prompt has the {context} placeholder."""
        assert "{context}" in RAG_SYSTEM_PROMPT

    def test_mentions_retriever(self) -> None:
        """Prompt identifies the assistant as Retriever."""
        assert "Retriever" in RAG_SYSTEM_PROMPT


class TestFallbackSystemPrompt:
    """Tests for the fallback system prompt."""

    def test_exists_and_non_empty(self) -> None:
        """Fallback prompt exists and has content."""
        assert FALLBACK_SYSTEM_PROMPT
        assert len(FALLBACK_SYSTEM_PROMPT) > 50

    def test_mentions_no_documents(self) -> None:
        """Fallback prompt mentions that no documents are indexed."""
        assert "No shelter documents have been indexed" in FALLBACK_SYSTEM_PROMPT

    def test_mentions_retriever(self) -> None:
        """Fallback prompt identifies the assistant as Retriever."""
        assert "Retriever" in FALLBACK_SYSTEM_PROMPT
