"""Unit tests for RAG dependency providers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retriever.modules.rag.dependencies import (
    _reset_dependencies,
    get_confidence_scorer,
    get_document_processor,
    get_embedding_provider,
    get_hybrid_retriever,
    get_llm_provider,
    get_message_repository,
    get_rag_service,
    get_safety_service,
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
    settings.cloudflare_account_id = ""
    settings.cloudflare_gateway_id = ""
    settings.llm_gateway_url = ""
    settings.llm_gateway_token.get_secret_value.return_value = ""
    settings.llm_gateway_auth_header = "cf-aig-authorization"
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    settings.default_embedding_model = "openai/text-embedding-3-small"
    settings.default_llm_model = "anthropic/claude-sonnet-4.6"
    settings.fallback_llm_model = "anthropic/claude-haiku-3"
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


# ── get_embedding_provider ─────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_embedding_provider_uses_gateway_base_url(
    mock_get_settings: MagicMock,
) -> None:
    """Embedding provider builds against the single gateway base URL."""
    settings = _make_mock_settings()
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    mock_get_settings.return_value = settings

    provider = get_embedding_provider()

    assert str(provider._client.base_url).rstrip("/").endswith("/compat")


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_embedding_provider_keeps_provider_prefix(
    mock_get_settings: MagicMock,
) -> None:
    """On the compat endpoint the embedding model keeps its {provider}/ prefix."""
    settings = _make_mock_settings()
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    mock_get_settings.return_value = settings

    provider = get_embedding_provider()

    assert provider._model == "openai/text-embedding-3-small"


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_embedding_provider_sends_gateway_token_header(
    mock_get_settings: MagicMock,
) -> None:
    """Embeddings route through the shared gateway client with the BYOK token."""
    settings = _make_mock_settings()
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    settings.llm_gateway_token.get_secret_value.return_value = "cf-token"
    mock_get_settings.return_value = settings

    provider = get_embedding_provider()

    headers = provider._client.default_headers
    assert headers.get("cf-aig-authorization") == "Bearer cf-token"


# ── get_llm_provider ───────────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_llm_provider_uses_settings_fallback_model(
    mock_get_settings: MagicMock,
) -> None:
    """Fallback model comes from settings, not a hardcoded literal."""
    settings = _make_mock_settings()
    settings.fallback_llm_model = "anthropic/claude-haiku-custom"
    mock_get_settings.return_value = settings

    provider = get_llm_provider()

    assert provider._fallback_model == "anthropic/claude-haiku-custom"


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_llm_provider_sends_gateway_token_header(
    mock_get_settings: MagicMock,
) -> None:
    """Chat routes through the shared gateway client with the BYOK token."""
    settings = _make_mock_settings()
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    settings.llm_gateway_token.get_secret_value.return_value = "cf-token"
    mock_get_settings.return_value = settings

    provider = get_llm_provider()

    headers = provider._provider._client.default_headers
    assert headers.get("cf-aig-authorization") == "Bearer cf-token"


# ── get_safety_service ─────────────────────────────────────────────────────


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_safety_service_routes_moderator_through_gateway(
    mock_get_settings: MagicMock,
) -> None:
    """Moderator is constructed against the gateway base URL, no direct OpenAI bypass."""
    settings = _make_mock_settings()
    settings.llm_gateway_base_url = "https://gateway.ai.cloudflare.com/v1/a/b/compat"
    settings.llm_gateway_token.get_secret_value.return_value = "cf-token"
    mock_get_settings.return_value = settings

    service = get_safety_service()

    assert service is not None
    moderator = service._moderator
    assert str(moderator._client.base_url).rstrip("/").endswith("/compat")


@patch("retriever.modules.rag.dependencies.get_settings")
def test_get_safety_service_returns_none_when_disabled(
    mock_get_settings: MagicMock,
) -> None:
    """No safety service when moderation is disabled."""
    mock_get_settings.return_value = _make_mock_settings(moderation_enabled=False)

    assert get_safety_service() is None


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
