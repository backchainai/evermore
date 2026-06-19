"""Unit tests for RAG dependency providers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retriever.modules.rag.dependencies import (
    _reset_dependencies,
    get_confidence_scorer,
    get_document_processor,
    get_hybrid_retriever,
    get_message_repository,
    get_rag_service,
    get_semantic_cache,
    get_session_factory,
    get_vector_store,
)


def _make_mock_settings(
    *,
    cache_enabled: bool = True,
    hybrid_retrieval_enabled: bool = True,
    moderation_enabled: bool = True,
) -> MagicMock:
    """Create mock settings for dependency tests."""
    settings = MagicMock()
    settings.database_url.get_secret_value.return_value = (
        "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    settings.database_require_ssl = False
    settings.openai_api_key.get_secret_value.return_value = "test-openai-key"
    settings.openrouter_api_key.get_secret_value.return_value = "test-openrouter-key"
    settings.ai_gateway_base_url = "https://openrouter.ai/api/v1"
    settings.default_embedding_model = "openai/text-embedding-3-small"
    settings.default_llm_model = "anthropic/claude-sonnet-4"
    settings.llm_timeout_seconds = 30.0
    settings.cache_enabled = cache_enabled
    settings.hybrid_retrieval_enabled = hybrid_retrieval_enabled
    settings.hybrid_semantic_weight = 0.5
    settings.hybrid_keyword_weight = 0.5
    settings.hybrid_rrf_k = 60
    settings.moderation_enabled = moderation_enabled
    settings.rag_top_k = 5
    settings.docling_ocr_enabled = True
    settings.docling_table_extraction = True
    settings.docling_picture_description = False
    settings.docling_max_pages = 100
    settings.docling_chunk_max_tokens = 512
    settings.docling_merge_peers = True
    return settings


# ── get_session_factory ────────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_session_factory_delegates_to_shared_factory(
    mock_factory: MagicMock,
) -> None:
    factory = get_session_factory()
    mock_factory.assert_called_once()
    assert factory is mock_factory.return_value


# ── get_rag_service singleton ──────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_rag_service_creates_singleton(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    _reset_dependencies()
    mock_get_settings.return_value = _make_mock_settings()

    service1 = get_rag_service()
    service2 = get_rag_service()

    assert service1 is service2
    _reset_dependencies()


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_reset_dependencies_clears_singleton(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    _reset_dependencies()
    mock_get_settings.return_value = _make_mock_settings()

    service1 = get_rag_service()
    _reset_dependencies()
    service2 = get_rag_service()

    assert service1 is not service2
    _reset_dependencies()


# ── get_semantic_cache ─────────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_semantic_cache_returns_none_when_disabled(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_get_settings.return_value = _make_mock_settings(cache_enabled=False)

    result = get_semantic_cache()

    assert result is None


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_semantic_cache_returns_cache_when_enabled(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_get_settings.return_value = _make_mock_settings(cache_enabled=True)

    result = get_semantic_cache()

    assert result is not None


# ── get_hybrid_retriever ───────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_hybrid_retriever_returns_none_when_disabled(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_get_settings.return_value = _make_mock_settings(
        hybrid_retrieval_enabled=False,
    )

    result = get_hybrid_retriever()

    assert result is None


@patch("retriever.modules.rag.dependencies.get_settings")
@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_hybrid_retriever_returns_retriever_when_enabled(
    mock_factory: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_get_settings.return_value = _make_mock_settings(
        hybrid_retrieval_enabled=True,
    )

    result = get_hybrid_retriever()

    assert result is not None


# ── get_vector_store ───────────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_vector_store_creates_store(mock_factory: MagicMock) -> None:
    store = get_vector_store()

    assert store is not None


# ── get_confidence_scorer ──────────────────────────────────────────────────


def test_get_confidence_scorer_creates_scorer() -> None:
    scorer = get_confidence_scorer()

    assert scorer is not None


# ── get_message_repository ─────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies._get_factory")
def test_get_message_repository_creates_repo(mock_factory: MagicMock) -> None:
    repo = get_message_repository()

    assert repo is not None


# ── get_document_processor ────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_document_processor_returns_format_aware(
    mock_get_settings: MagicMock,
) -> None:
    from retriever.modules.rag.docling_processor import FormatAwareProcessor

    mock_get_settings.return_value = _make_mock_settings()

    processor = get_document_processor()

    assert isinstance(processor, FormatAwareProcessor)
