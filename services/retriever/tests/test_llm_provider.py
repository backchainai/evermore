"""Tests for LLM provider infrastructure."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APIConnectionError, APITimeoutError, RateLimitError

from retriever.infrastructure.llm import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    OpenRouterProvider,
)


class TestOpenRouterProviderInit:
    """Tests for OpenRouterProvider initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Provider should initialize with valid API key."""
        provider = OpenRouterProvider(api_key="test-key")

        assert provider._default_model == "anthropic/claude-sonnet-4"
        assert provider._timeout == 30.0

    def test_init_with_custom_model(self) -> None:
        """Provider should accept custom default model."""
        provider = OpenRouterProvider(
            api_key="test-key",
            default_model="anthropic/claude-haiku",
        )

        assert provider._default_model == "anthropic/claude-haiku"

    def test_init_with_empty_api_key_raises(self) -> None:
        """Provider should raise error with empty API key."""
        with pytest.raises(LLMConfigurationError) as exc_info:
            OpenRouterProvider(api_key="")

        assert "API key is required" in str(exc_info.value)
        assert exc_info.value.provider == "openrouter"

    def test_init_with_custom_circuit_breaker_settings(self) -> None:
        """Provider should accept custom circuit breaker settings."""
        provider = OpenRouterProvider(
            api_key="test-key",
            circuit_breaker_fail_max=3,
            circuit_breaker_timeout=30.0,
        )

        assert provider._breaker._fail_max == 3

    def test_init_with_custom_base_url(self) -> None:
        """Provider should accept custom base URL for AI Gateway."""
        provider = OpenRouterProvider(
            api_key="test-key",
            base_url="https://gateway.ai.cloudflare.com/v1/acct/gw/openai",
        )

        assert provider._client.base_url.host == "gateway.ai.cloudflare.com"


class TestOpenRouterProviderComplete:
    """Tests for OpenRouterProvider.complete() method."""

    @pytest.fixture
    def provider(self) -> OpenRouterProvider:
        """Create a provider with a mocked client."""
        return OpenRouterProvider(api_key="test-key")

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        """Create a mock API response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Test response"
        return response

    async def test_complete_returns_content(
        self, provider: OpenRouterProvider, mock_response: MagicMock
    ) -> None:
        """Complete should return the message content."""
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.complete(
            system_prompt="You are helpful.",
            user_message="Hello",
        )

        assert result == "Test response"

    async def test_complete_uses_default_model(
        self, provider: OpenRouterProvider, mock_response: MagicMock
    ) -> None:
        """Complete should use default model when not specified."""
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        await provider.complete(
            system_prompt="You are helpful.",
            user_message="Hello",
        )

        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "anthropic/claude-sonnet-4"

    async def test_complete_with_custom_model(
        self, provider: OpenRouterProvider, mock_response: MagicMock
    ) -> None:
        """Complete should use specified model."""
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        await provider.complete(
            system_prompt="You are helpful.",
            user_message="Hello",
            model="anthropic/claude-haiku",
        )

        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "anthropic/claude-haiku"

    async def test_complete_timeout_raises_llm_timeout_error(
        self, provider: OpenRouterProvider
    ) -> None:
        """Complete should raise LLMTimeoutError on timeout."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with pytest.raises(LLMTimeoutError) as exc_info:
            await provider.complete(
                system_prompt="You are helpful.",
                user_message="Hello",
            )

        assert "timed out" in str(exc_info.value)
        assert exc_info.value.provider == "openrouter"

    async def test_complete_rate_limit_raises_llm_rate_limit_error(
        self, provider: OpenRouterProvider
    ) -> None:
        """Complete should raise LLMRateLimitError when rate limited."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        with pytest.raises(LLMRateLimitError) as exc_info:
            await provider.complete(
                system_prompt="You are helpful.",
                user_message="Hello",
            )

        assert "Rate limited" in str(exc_info.value)

    async def test_complete_connection_error_raises_llm_provider_error(
        self, provider: OpenRouterProvider
    ) -> None:
        """Complete should raise LLMProviderError on connection error."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.complete(
                system_prompt="You are helpful.",
                user_message="Hello",
            )

        assert "Unable to connect" in str(exc_info.value)

    async def test_complete_handles_empty_response_content(
        self, provider: OpenRouterProvider
    ) -> None:
        """Complete should handle None content gracefully."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = None

        provider._client.chat.completions.create = AsyncMock(return_value=response)

        result = await provider.complete(
            system_prompt="You are helpful.",
            user_message="Hello",
        )

        assert result == ""


class TestOpenRouterProviderCompleteWithHistory:
    """Tests for OpenRouterProvider.complete_with_history() method."""

    @pytest.fixture
    def provider(self) -> OpenRouterProvider:
        """Create a provider with a mocked client."""
        return OpenRouterProvider(api_key="test-key")

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        """Create a mock API response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "History response"
        return response

    async def test_complete_with_history_returns_content(
        self, provider: OpenRouterProvider, mock_response: MagicMock
    ) -> None:
        """complete_with_history should return message content."""
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.complete_with_history(
            system_prompt="You are helpful.",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
                {"role": "user", "content": "What's the policy?"},
            ],
        )

        assert result == "History response"

    async def test_complete_with_history_includes_system_prompt(
        self, provider: OpenRouterProvider, mock_response: MagicMock
    ) -> None:
        """complete_with_history should include system prompt as first message."""
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        await provider.complete_with_history(
            system_prompt="You are helpful.",
            messages=[{"role": "user", "content": "Hello"}],
        )

        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert len(messages) == 2

    async def test_complete_with_history_timeout_raises(
        self, provider: OpenRouterProvider
    ) -> None:
        """complete_with_history should raise LLMTimeoutError on timeout."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with pytest.raises(LLMTimeoutError):
            await provider.complete_with_history(
                system_prompt="system",
                messages=[{"role": "user", "content": "hello"}],
            )

    async def test_complete_with_history_rate_limit_raises(
        self, provider: OpenRouterProvider
    ) -> None:
        """complete_with_history should raise LLMRateLimitError on rate limit."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        with pytest.raises(LLMRateLimitError):
            await provider.complete_with_history(
                system_prompt="system",
                messages=[{"role": "user", "content": "hello"}],
            )

    async def test_complete_with_history_connection_error_raises(
        self, provider: OpenRouterProvider
    ) -> None:
        """complete_with_history should raise LLMProviderError on connection error."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        with pytest.raises(LLMProviderError):
            await provider.complete_with_history(
                system_prompt="system",
                messages=[{"role": "user", "content": "hello"}],
            )

    async def test_complete_with_history_unexpected_error_raises(
        self, provider: OpenRouterProvider
    ) -> None:
        """complete_with_history should raise LLMProviderError on unexpected error."""
        provider._client.chat.completions.create = AsyncMock(
            side_effect=ValueError("Something went wrong")
        )

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.complete_with_history(
                system_prompt="system",
                messages=[{"role": "user", "content": "hello"}],
            )

        assert "unexpected error" in str(exc_info.value)


class TestOpenRouterProviderResilience:
    """Tests for retry and circuit breaker behavior."""

    async def test_retries_on_connection_error(self) -> None:
        """Provider should retry on connection errors."""
        provider = OpenRouterProvider(api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success after retry"

        provider._client.chat.completions.create = AsyncMock(
            side_effect=[
                APIConnectionError(request=MagicMock()),
                mock_response,
            ]
        )

        result = await provider.complete(
            system_prompt="You are helpful.",
            user_message="Hello",
        )

        assert result == "Success after retry"
        assert provider._client.chat.completions.create.call_count == 2

    async def test_circuit_breaker_opens_after_failures(self) -> None:
        """Circuit breaker should open after repeated failures."""
        provider = OpenRouterProvider(
            api_key="test-key",
            circuit_breaker_fail_max=3,
            circuit_breaker_timeout=60.0,
        )

        provider._client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        for _ in range(2):
            with pytest.raises(LLMRateLimitError):
                await provider.complete(
                    system_prompt="You are helpful.",
                    user_message="Hello",
                )

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.complete(
                system_prompt="You are helpful.",
                user_message="Hello",
            )

        assert "temporarily unavailable" in str(exc_info.value)
        assert not isinstance(exc_info.value, LLMRateLimitError)
