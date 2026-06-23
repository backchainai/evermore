# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Content moderation using OpenAI Moderation API."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog
from openai import AsyncOpenAI

from retriever.infrastructure.safety.schemas import ModerationResult

logger = structlog.get_logger()


@runtime_checkable
class ModerationProvider(Protocol):
    """Protocol for content moderation providers."""

    async def check(self, text: str) -> ModerationResult:
        """Check if text contains unsafe content.

        Args:
            text: The text to check.

        Returns:
            ModerationResult with flagged status and category details.
        """
        ...


class OpenAIModerator:
    """Content moderator using OpenAI's Moderation API.

    The Moderation API provides fast (<100ms) content classification for
    harmful content categories. Calls route through the shared LLM gateway
    (consolidated transport, single BYOK token) like chat and embeddings.
    """

    def __init__(self, *, client: AsyncOpenAI) -> None:
        """Initialize the moderator.

        Args:
            client: Pre-built AsyncOpenAI client pointed at the LLM gateway.
                The injected client owns the base URL, timeout, and auth
                header, so moderation routes through the gateway like chat and
                embeddings.
        """
        self._client = client

    async def check(self, text: str) -> ModerationResult:
        """Check if text contains unsafe content.

        Args:
            text: The text to check.

        Returns:
            ModerationResult with flagged status and category details.

        Note:
            On API errors, returns a safe result to avoid blocking
            legitimate requests. Errors are logged for monitoring.
        """
        try:
            # The compat endpoint addresses every provider uniformly, so the
            # model carries its provider prefix like chat and embeddings.
            response = await self._client.moderations.create(
                input=text,
                model="openai/omni-moderation-latest",
            )

            result = response.results[0]

            # Convert category objects to dicts
            categories: dict[str, bool] = {}
            category_scores: dict[str, float] = {}
            for field_name, value in result.categories:
                categories[field_name] = bool(value)
            for field_name, value in result.category_scores:
                category_scores[field_name] = float(value)

            moderation_result = ModerationResult(
                flagged=result.flagged,
                categories=categories,
                category_scores=category_scores,
            )

            if moderation_result.flagged:
                flagged_cats = [cat for cat, flagged in categories.items() if flagged]
                logger.warning(
                    "moderation_content_flagged",
                    flagged_categories=flagged_cats,
                    text_preview=text[:100],
                )

            return moderation_result

        except TimeoutError:
            logger.error("moderation_timeout", text_length=len(text))
            # Fail open - don't block on timeout
            return ModerationResult.safe()

        except Exception as e:
            logger.error(
                "moderation_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Fail open
            return ModerationResult.safe()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.close()


class NoOpModerator:
    """No-op moderator that always returns safe.

    Use this when moderation is disabled or API key is not configured.
    """

    async def check(self, text: str) -> ModerationResult:  # noqa: ARG002
        """Always returns a safe result.

        Args:
            text: The text to check (ignored).

        Returns:
            ModerationResult marked as safe.
        """
        return ModerationResult.safe()

    async def close(self) -> None:
        """No-op close."""
