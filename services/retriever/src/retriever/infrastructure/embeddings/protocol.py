# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Protocol definition for embedding providers."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding provider implementations.

    This allows swapping between different embedding backends (OpenAI,
    local models, etc.) without changing business logic.
    """

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as a list of floats.

        Raises:
            EmbeddingProviderError: If embedding generation fails.
            EmbeddingTimeoutError: If the request times out.
            EmbeddingRateLimitError: If rate limited by the provider.
        """
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingProviderError: If embedding generation fails.
            EmbeddingTimeoutError: If the request times out.
            EmbeddingRateLimitError: If rate limited by the provider.
        """
        ...

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""
        ...
