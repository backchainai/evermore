# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Protocol definition for LLM providers."""

from typing import Protocol


class LLMProvider(Protocol):
    """Protocol for LLM provider implementations.

    This allows swapping between different LLM backends (an OpenAI-compatible
    gateway, direct Anthropic, local models) without changing business logic.
    """

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str | None = None,
    ) -> str:
        """Generate a completion for the given prompts.

        Args:
            system_prompt: The system message setting context/behavior.
            user_message: The user's message to respond to.
            model: Optional model override. Uses provider default if not specified.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If the completion fails.
            LLMTimeoutError: If the request times out.
            LLMRateLimitError: If rate limited by the provider.
        """
        ...

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
            model: Optional model override. Uses provider default if not specified.

        Returns:
            The generated completion text.

        Raises:
            LLMProviderError: If the completion fails.
            LLMTimeoutError: If the request times out.
            LLMRateLimitError: If rate limited by the provider.
        """
        ...
