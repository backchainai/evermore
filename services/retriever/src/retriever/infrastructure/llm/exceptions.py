# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Custom exceptions for LLM provider operations."""


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, message: str, *, provider: str = "unknown") -> None:
        self.provider = provider
        super().__init__(message)


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM request times out."""


class LLMRateLimitError(LLMProviderError):
    """Raised when rate limited by the LLM provider."""


class LLMConfigurationError(LLMProviderError):
    """Raised when there's a configuration issue (e.g., missing API key)."""
