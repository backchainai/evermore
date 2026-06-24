# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""OpenAI-compatible LLM provider implementation."""

from datetime import timedelta

import structlog
from aiobreaker import CircuitBreaker, CircuitBreakerError
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from retriever.infrastructure.llm.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from retriever.infrastructure.observability.langfuse import observe

logger = structlog.get_logger()


class OpenAICompatProvider:
    """LLM provider speaking the OpenAI chat-completions API.

    Calls go through an OpenAI-compatible LLM gateway. Includes resilience
    patterns:
    - Retries with exponential backoff for transient failures
    - Circuit breaker to fail fast after repeated failures
    - Configurable timeouts
    """

    PROVIDER_NAME = "openai-compat"

    def __init__(
        self,
        *,
        client: AsyncOpenAI,
        default_model: str = "anthropic/claude-sonnet-4-6",
        timeout_seconds: float = 30.0,
        circuit_breaker_fail_max: int = 5,
        circuit_breaker_timeout: float = 60.0,
    ) -> None:
        """Initialize the provider.

        Args:
            client: Pre-built AsyncOpenAI client pointed at the LLM gateway.
                The injected client owns the base URL, timeout, and auth
                header, so chat carries the gateway auth header like embeddings
                and moderation.
            default_model: Default model to use for completions.
            timeout_seconds: Request timeout in seconds, used only for the
                timeout messages reported on APITimeoutError; the injected
                client owns the transport-level timeout.
            circuit_breaker_fail_max: Open circuit after this many failures.
            circuit_breaker_timeout: Time in seconds before attempting recovery.
        """
        self._client = client
        self._default_model = default_model
        self._timeout = timeout_seconds

        self._breaker = CircuitBreaker(
            fail_max=circuit_breaker_fail_max,
            timeout_duration=timedelta(seconds=circuit_breaker_timeout),
        )

    @observe(as_type="generation")  # type: ignore[untyped-decorator]
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str | None = None,
    ) -> str:
        """Generate a completion via the LLM gateway.

        Args:
            system_prompt: The system message setting context/behavior.
            user_message: The user's message to respond to.
            model: Optional model override.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If the completion fails.
            LLMTimeoutError: If the request times out.
            LLMRateLimitError: If rate limited.
        """
        model_to_use = model or self._default_model

        try:
            result: str = await self._complete_with_resilience(
                system_prompt=system_prompt,
                user_message=user_message,
                model=model_to_use,
            )
            return result

        except CircuitBreakerError as e:
            logger.warning(
                "circuit_breaker_open",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
            )
            raise LLMProviderError(
                "Service temporarily unavailable. Please try again in a moment.",
                provider=self.PROVIDER_NAME,
            ) from e

        except APITimeoutError as e:
            logger.warning(
                "llm_timeout",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
                timeout_seconds=self._timeout,
            )
            raise LLMTimeoutError(
                f"Request timed out after {self._timeout}s",
                provider=self.PROVIDER_NAME,
            ) from e

        except APIConnectionError as e:
            logger.error(
                "llm_connection_error",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
                error=str(e),
            )
            raise LLMProviderError(
                "Unable to connect to LLM service",
                provider=self.PROVIDER_NAME,
            ) from e

    @retry(
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, max=5),
        reraise=True,
    )
    async def _complete_with_resilience(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
    ) -> str:
        """Internal method with retry and circuit breaker logic."""
        return await self._breaker.call_async(  # type: ignore[no-any-return]
            self._do_complete, system_prompt, user_message, model
        )

    async def _do_complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
    ) -> str:
        """Execute the actual API call."""
        logger.debug(
            "llm_request_start",
            provider=self.PROVIDER_NAME,
            model=model,
            message_length=len(user_message),
        )

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            content = response.choices[0].message.content or ""

            logger.debug(
                "llm_request_success",
                provider=self.PROVIDER_NAME,
                model=model,
                response_length=len(content),
            )

            return content

        except RateLimitError as e:
            logger.warning(
                "llm_rate_limited",
                provider=self.PROVIDER_NAME,
                model=model,
            )
            raise LLMRateLimitError(
                "Rate limited by the LLM gateway. Please try again shortly.",
                provider=self.PROVIDER_NAME,
            ) from e

        except (APIConnectionError, APITimeoutError):
            raise

        except Exception as e:
            logger.error(
                "llm_unexpected_error",
                provider=self.PROVIDER_NAME,
                model=model,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise LLMProviderError(
                "An unexpected error occurred",
                provider=self.PROVIDER_NAME,
            ) from e

    @observe(as_type="generation")  # type: ignore[untyped-decorator]
    async def complete_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        """Generate a completion with conversation history.

        Args:
            system_prompt: The system message setting context/behavior.
            messages: Conversation history as list of {"role": "user"|"assistant", "content": "..."}.
            model: Optional model override.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If the completion fails.
            LLMTimeoutError: If the request times out.
            LLMRateLimitError: If rate limited.
        """
        model_to_use = model or self._default_model

        try:
            result: str = await self._complete_history_with_resilience(
                system_prompt=system_prompt,
                messages=messages,
                model=model_to_use,
            )
            return result

        except CircuitBreakerError as e:
            logger.warning(
                "circuit_breaker_open",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
            )
            raise LLMProviderError(
                "Service temporarily unavailable. Please try again in a moment.",
                provider=self.PROVIDER_NAME,
            ) from e

        except APITimeoutError as e:
            logger.warning(
                "llm_timeout",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
                timeout_seconds=self._timeout,
            )
            raise LLMTimeoutError(
                f"Request timed out after {self._timeout}s",
                provider=self.PROVIDER_NAME,
            ) from e

        except APIConnectionError as e:
            logger.error(
                "llm_connection_error",
                provider=self.PROVIDER_NAME,
                model=model_to_use,
                error=str(e),
            )
            raise LLMProviderError(
                "Unable to connect to LLM service",
                provider=self.PROVIDER_NAME,
            ) from e

    @retry(
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, max=5),
        reraise=True,
    )
    async def _complete_history_with_resilience(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str,
    ) -> str:
        """Internal method with retry and circuit breaker logic for history completion."""
        return await self._breaker.call_async(  # type: ignore[no-any-return]
            self._do_complete_with_history, system_prompt, messages, model
        )

    async def _do_complete_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str,
    ) -> str:
        """Execute the actual API call with conversation history."""
        total_content_length = sum(len(m.get("content", "")) for m in messages)

        logger.debug(
            "llm_history_request_start",
            provider=self.PROVIDER_NAME,
            model=model,
            message_count=len(messages),
            total_content_length=total_content_length,
        )

        try:
            all_messages: list[dict[str, str]] = [
                {"role": "system", "content": system_prompt}
            ]
            all_messages.extend(messages)

            response = await self._client.chat.completions.create(
                model=model,
                messages=all_messages,  # type: ignore[arg-type]
            )

            content = response.choices[0].message.content or ""

            logger.debug(
                "llm_history_request_success",
                provider=self.PROVIDER_NAME,
                model=model,
                message_count=len(messages),
                response_length=len(content),
            )

            return content

        except RateLimitError as e:
            logger.warning(
                "llm_rate_limited",
                provider=self.PROVIDER_NAME,
                model=model,
            )
            raise LLMRateLimitError(
                "Rate limited by the LLM gateway. Please try again shortly.",
                provider=self.PROVIDER_NAME,
            ) from e

        except (APIConnectionError, APITimeoutError):
            raise

        except Exception as e:
            error_str = str(e).lower()
            if "context" in error_str and (
                "length" in error_str or "limit" in error_str
            ):
                logger.warning(
                    "llm_context_overflow",
                    provider=self.PROVIDER_NAME,
                    model=model,
                    message_count=len(messages),
                )
                raise LLMProviderError(
                    "Conversation is too long. Please start a new chat.",
                    provider=self.PROVIDER_NAME,
                ) from e

            logger.error(
                "llm_unexpected_error",
                provider=self.PROVIDER_NAME,
                model=model,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise LLMProviderError(
                "An unexpected error occurred",
                provider=self.PROVIDER_NAME,
            ) from e
