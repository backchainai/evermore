# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI dependency providers for RAG pipeline components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from retriever.modules.rag.docling_processor import FormatAwareProcessor

from retriever.config import get_settings
from retriever.infrastructure.cache.pg_cache import PgSemanticCache
from retriever.infrastructure.database.session import _get_factory
from retriever.infrastructure.embeddings.openai import OpenAIEmbeddingProvider
from retriever.infrastructure.llm.fallback import FallbackLLMProvider
from retriever.infrastructure.llm.openrouter import OpenRouterProvider
from retriever.infrastructure.safety.confidence import ConfidenceScorer
from retriever.infrastructure.safety.detector import PromptInjectionDetector
from retriever.infrastructure.safety.moderation import OpenAIModerator
from retriever.infrastructure.safety.service import SafetyService
from retriever.infrastructure.vectordb.pgvector_store import PgVectorStore
from retriever.models.user import DEFAULT_TENANT_ID
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.rag.retriever import HybridRetriever
from retriever.modules.rag.service import RAGService

# Module-level singletons (initialized on first use)
_rag_service: RAGService | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the database session factory.

    Returns:
        Cached async session factory.
    """
    return _get_factory()


def get_embedding_provider() -> OpenAIEmbeddingProvider:
    """Create an embedding provider from settings.

    Uses AI Gateway URL when Cloudflare is configured, otherwise
    falls back to OpenAI directly (not OpenRouter, which doesn't
    support the embeddings endpoint with the same auth).

    Returns:
        Configured OpenAI embedding provider.
    """
    settings = get_settings()
    use_gateway = bool(
        settings.cloudflare_account_id and settings.cloudflare_gateway_id
    )
    base_url = (
        settings.ai_gateway_base_url if use_gateway else "https://api.openai.com/v1"
    )
    model = settings.default_embedding_model
    if not use_gateway and model.startswith("openai/"):
        model = model.removeprefix("openai/")
    return OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key.get_secret_value(),
        base_url=base_url,
        model=model,
    )


def get_llm_provider() -> FallbackLLMProvider:
    """Create an LLM provider with fallback from settings.

    Returns:
        Configured fallback LLM provider wrapping the primary provider.
    """
    settings = get_settings()
    primary = OpenRouterProvider(
        api_key=settings.openrouter_api_key.get_secret_value(),
        base_url=settings.ai_gateway_base_url,
        default_model=settings.default_llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    return FallbackLLMProvider(primary, fallback_model="anthropic/claude-haiku-3")


def get_vector_store() -> PgVectorStore:
    """Create a vector store from the shared session factory.

    Returns:
        Configured pgvector store.
    """
    return PgVectorStore(get_session_factory())


def get_semantic_cache() -> PgSemanticCache | None:
    """Create a semantic cache if enabled in settings.

    Returns:
        Configured semantic cache, or None if disabled.
    """
    settings = get_settings()
    if not settings.cache_enabled:
        return None
    return PgSemanticCache(get_session_factory())


def get_hybrid_retriever() -> HybridRetriever | None:
    """Create a hybrid retriever if enabled in settings.

    Returns:
        Configured hybrid retriever, or None if disabled.
    """
    settings = get_settings()
    if not settings.hybrid_retrieval_enabled:
        return None
    return HybridRetriever(
        session_factory=get_session_factory(),
        vector_store=get_vector_store(),
        semantic_weight=settings.hybrid_semantic_weight,
        keyword_weight=settings.hybrid_keyword_weight,
        rrf_k=settings.hybrid_rrf_k,
    )


def get_safety_service() -> SafetyService | None:
    """Create a safety service if moderation is enabled.

    Returns:
        Configured safety service, or None if disabled.
    """
    settings = get_settings()
    if not settings.moderation_enabled:
        return None
    moderator = OpenAIModerator(
        api_key=settings.openai_api_key.get_secret_value(),
    )
    detector = PromptInjectionDetector()
    return SafetyService(
        moderator=moderator,
        injection_detector=detector,
    )


def get_confidence_scorer() -> ConfidenceScorer:
    """Create a confidence scorer.

    Returns:
        Default confidence scorer instance.
    """
    return ConfidenceScorer()


def get_document_processor() -> FormatAwareProcessor:
    """Create a format-aware document processor from settings.

    Routes text files through a lightweight pipeline and binary
    formats through Docling's full ML pipeline (lazy-initialized).

    Returns:
        Configured FormatAwareProcessor.
    """
    from retriever.modules.rag.docling_processor import (
        DoclingConfig,
        DoclingProcessor,
        FormatAwareProcessor,
    )

    settings = get_settings()
    config = DoclingConfig(
        ocr_enabled=settings.docling_ocr_enabled,
        table_extraction=settings.docling_table_extraction,
        picture_description=settings.docling_picture_description,
        max_pages=settings.docling_max_pages,
        chunk_max_tokens=settings.docling_chunk_max_tokens,
        merge_peers=settings.docling_merge_peers,
    )
    return FormatAwareProcessor(docling=DoclingProcessor(config=config))


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton.

    Lazily initializes all RAG pipeline components from settings.

    Returns:
        Configured RAG service.
    """
    global _rag_service  # noqa: PLW0603
    if _rag_service is None:
        settings = get_settings()
        _rag_service = RAGService(
            session_factory=get_session_factory(),
            llm_provider=get_llm_provider(),
            embedding_provider=get_embedding_provider(),
            vector_store=get_vector_store(),
            document_processor=get_document_processor(),
            semantic_cache=get_semantic_cache(),
            hybrid_retriever=get_hybrid_retriever(),
            safety_service=get_safety_service(),
            confidence_scorer=get_confidence_scorer(),
            top_k=settings.rag_top_k,
            tenant_id=DEFAULT_TENANT_ID,
        )
    return _rag_service


def get_message_repository() -> MessageRepository:
    """Create a message repository from the shared session factory.

    Returns:
        Configured message repository.
    """
    return MessageRepository(get_session_factory())


def _reset_dependencies() -> None:
    """Reset module-level singletons (for testing)."""
    global _rag_service  # noqa: PLW0603
    _rag_service = None
