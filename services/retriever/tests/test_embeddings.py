"""Tests for embedding provider infrastructure."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APIConnectionError, APITimeoutError, RateLimitError

from retriever.infrastructure.embeddings import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
    OpenAIEmbeddingProvider,
)


class TestOpenAIEmbeddingProviderInit:
    """Tests for OpenAIEmbeddingProvider initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Provider should initialize with valid API key."""
        provider = OpenAIEmbeddingProvider(api_key="test-key")

        assert provider._model == "openai/text-embedding-3-small"
        assert provider._timeout == 30.0

    def test_init_with_custom_model(self) -> None:
        """Provider should accept custom model."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="openai/text-embedding-3-large",
        )

        assert provider._model == "openai/text-embedding-3-large"

    def test_init_with_empty_api_key_raises(self) -> None:
        """Provider should raise error with empty API key."""
        with pytest.raises(EmbeddingConfigurationError) as exc_info:
            OpenAIEmbeddingProvider(api_key="")

        assert "API key is required" in str(exc_info.value)
        assert exc_info.value.provider == "openai"

    def test_dimensions_returns_correct_value_for_small(self) -> None:
        """Should return correct dimensions for text-embedding-3-small."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="openai/text-embedding-3-small",
        )

        assert provider.dimensions == 1536

    def test_dimensions_returns_correct_value_for_large(self) -> None:
        """Should return correct dimensions for text-embedding-3-large."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="openai/text-embedding-3-large",
        )

        assert provider.dimensions == 3072


class TestOpenAIEmbeddingProviderEmbed:
    """Tests for OpenAIEmbeddingProvider.embed() method."""

    @pytest.fixture
    def provider(self) -> OpenAIEmbeddingProvider:
        """Create a provider with a mocked client."""
        return OpenAIEmbeddingProvider(api_key="test-key")

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        """Create a mock API response."""
        response = MagicMock()
        embedding_item = MagicMock()
        embedding_item.embedding = [0.1] * 1536
        embedding_item.index = 0
        response.data = [embedding_item]
        return response

    async def test_embed_returns_vector(
        self, provider: OpenAIEmbeddingProvider, mock_response: MagicMock
    ) -> None:
        """Embed should return the embedding vector."""
        provider._client.embeddings.create = AsyncMock(return_value=mock_response)

        result = await provider.embed("Hello, world!")

        assert len(result) == 1536
        assert result[0] == 0.1

    async def test_embed_calls_api_with_correct_params(
        self, provider: OpenAIEmbeddingProvider, mock_response: MagicMock
    ) -> None:
        """Embed should call API with correct parameters."""
        provider._client.embeddings.create = AsyncMock(return_value=mock_response)

        await provider.embed("Hello, world!")

        provider._client.embeddings.create.assert_called_once()
        call_kwargs = provider._client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "openai/text-embedding-3-small"
        assert call_kwargs["input"] == ["Hello, world!"]

    async def test_embed_with_timeout_raises_timeout_error(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed should raise EmbeddingTimeoutError on timeout."""
        provider._client.embeddings.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with pytest.raises(EmbeddingTimeoutError) as exc_info:
            await provider.embed("Hello")

        assert "timed out" in str(exc_info.value)
        assert exc_info.value.provider == "openai"

    async def test_embed_with_rate_limit_raises_rate_limit_error(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed should raise EmbeddingRateLimitError on rate limit."""
        provider._client.embeddings.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=MagicMock(),
                body=None,
            )
        )

        with pytest.raises(EmbeddingRateLimitError) as exc_info:
            await provider.embed("Hello")

        assert "Rate limited" in str(exc_info.value)

    async def test_embed_with_connection_error_raises_provider_error(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed should raise EmbeddingProviderError on connection error."""
        provider._client.embeddings.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        with pytest.raises(EmbeddingProviderError) as exc_info:
            await provider.embed("Hello")

        assert "Unable to connect" in str(exc_info.value)


class TestOpenAIEmbeddingProviderCircuitBreaker:
    """Tests for circuit breaker behavior in embedding provider."""

    async def test_circuit_breaker_opens_after_failures(self) -> None:
        """Circuit breaker should open after repeated failures."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            circuit_breaker_fail_max=3,
            circuit_breaker_timeout=60.0,
        )

        provider._client.embeddings.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=MagicMock(),
                body=None,
            )
        )

        for _ in range(2):
            with pytest.raises(EmbeddingRateLimitError):
                await provider.embed("Hello")

        with pytest.raises(EmbeddingProviderError) as exc_info:
            await provider.embed("Hello")

        assert "temporarily unavailable" in str(exc_info.value)
        assert not isinstance(exc_info.value, EmbeddingRateLimitError)


class TestOpenAIEmbeddingProviderEmbedBatch:
    """Tests for OpenAIEmbeddingProvider.embed_batch() method."""

    @pytest.fixture
    def provider(self) -> OpenAIEmbeddingProvider:
        """Create a provider with a mocked client."""
        return OpenAIEmbeddingProvider(api_key="test-key")

    @pytest.fixture
    def mock_batch_response(self) -> MagicMock:
        """Create a mock batch API response."""
        response = MagicMock()
        items = []
        for i in range(3):
            item = MagicMock()
            item.embedding = [0.1 * (i + 1)] * 1536
            item.index = i
            items.append(item)
        response.data = items
        return response

    async def test_embed_batch_returns_multiple_vectors(
        self, provider: OpenAIEmbeddingProvider, mock_batch_response: MagicMock
    ) -> None:
        """Embed batch should return multiple vectors."""
        provider._client.embeddings.create = AsyncMock(return_value=mock_batch_response)

        result = await provider.embed_batch(["Hello", "World", "Test"])

        assert len(result) == 3
        assert len(result[0]) == 1536

    async def test_embed_batch_with_empty_list_returns_empty(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed batch with empty list should return empty list."""
        result = await provider.embed_batch([])

        assert result == []

    async def test_embed_batch_timeout_raises_timeout_error(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed batch should raise EmbeddingTimeoutError on timeout."""
        provider._client.embeddings.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with pytest.raises(EmbeddingTimeoutError):
            await provider.embed_batch(["Hello", "World"])

    async def test_embed_batch_connection_error_raises(
        self, provider: OpenAIEmbeddingProvider
    ) -> None:
        """Embed batch should raise EmbeddingProviderError on connection error."""
        provider._client.embeddings.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        with pytest.raises(EmbeddingProviderError) as exc_info:
            await provider.embed_batch(["Hello", "World"])

        assert "Unable to connect" in str(exc_info.value)

    async def test_embed_batch_preserves_order(
        self, provider: OpenAIEmbeddingProvider, mock_batch_response: MagicMock
    ) -> None:
        """Embed batch should preserve order of inputs."""
        provider._client.embeddings.create = AsyncMock(return_value=mock_batch_response)

        result = await provider.embed_batch(["First", "Second", "Third"])

        assert result[0][0] == 0.1
        assert result[1][0] == 0.2
        assert result[2][0] == pytest.approx(0.3, rel=1e-5)
