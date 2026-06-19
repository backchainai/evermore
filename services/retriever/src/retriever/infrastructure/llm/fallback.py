# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Fallback LLM provider with model degradation."""

import structlog

from retriever.infrastructure.llm.exceptions import LLMProviderError
from retriever.infrastructure.llm.protocol import LLMProvider

logger = structlog.get_logger()


class FallbackLLMProvider:
    """LLM provider that falls back to a secondary model on failure.

    This provides graceful degradation when the primary model is unavailable
    or overloaded. The fallback model is typically smaller/faster/cheaper.
    """

    def __init__(
        self,
        primary_provider: LLMProvider,
        *,
        fallback_model: str,
    ) -> None:
        """Initialize the fallback provider.

        Args:
            primary_provider: The primary LLM provider to use.
            fallback_model: Model identifier to use when primary fails.
        """
        self._provider = primary_provider
        self._fallback_model = fallback_model

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str | None = None,
    ) -> str:
        """Generate a completion with automatic fallback.

        Tries the primary model first. On failure, automatically retries
        with the fallback model.

        Args:
            system_prompt: The system message setting context/behavior.
            user_message: The user's message to respond to.
            model: Optional model override for primary attempt.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If both primary and fallback fail.
        """
        try:
            return await self._provider.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                model=model,
            )
        except LLMProviderError as primary_error:
            logger.warning(
                "llm_primary_failed_trying_fallback",
                primary_error=str(primary_error),
                fallback_model=self._fallback_model,
            )

            try:
                result = await self._provider.complete(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=self._fallback_model,
                )
                logger.info(
                    "llm_fallback_success",
                    fallback_model=self._fallback_model,
                )
                return result

            except LLMProviderError as fallback_error:
                logger.error(
                    "llm_fallback_also_failed",
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                    fallback_model=self._fallback_model,
                )
                raise primary_error from None

    async def complete_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        """Generate a completion with conversation history and automatic fallback.

        Args:
            system_prompt: The system message setting context/behavior.
            messages: Conversation history.
            model: Optional model override for primary attempt.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If both primary and fallback fail.
        """
        try:
            return await self._provider.complete_with_history(
                system_prompt=system_prompt,
                messages=messages,
                model=model,
            )
        except LLMProviderError as primary_error:
            logger.warning(
                "llm_primary_failed_trying_fallback",
                primary_error=str(primary_error),
                fallback_model=self._fallback_model,
            )

            try:
                result = await self._provider.complete_with_history(
                    system_prompt=system_prompt,
                    messages=messages,
                    model=self._fallback_model,
                )
                logger.info(
                    "llm_fallback_success",
                    fallback_model=self._fallback_model,
                )
                return result

            except LLMProviderError as fallback_error:
                logger.error(
                    "llm_fallback_also_failed",
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                    fallback_model=self._fallback_model,
                )
                raise primary_error from None
