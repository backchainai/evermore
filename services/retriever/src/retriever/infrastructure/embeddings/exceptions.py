# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Exceptions for embedding providers."""


class EmbeddingProviderError(Exception):
    """Base exception for embedding provider errors."""

    def __init__(self, message: str, *, provider: str = "unknown") -> None:
        self.provider = provider
        super().__init__(message)


class EmbeddingTimeoutError(EmbeddingProviderError):
    """Raised when an embedding request times out."""


class EmbeddingRateLimitError(EmbeddingProviderError):
    """Raised when rate limited by the embedding provider."""


class EmbeddingConfigurationError(EmbeddingProviderError):
    """Raised when there's a configuration issue (e.g., missing API key)."""
