# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Confidence scoring for RAG responses."""

from __future__ import annotations

import structlog

from retriever.infrastructure.safety.schemas import ConfidenceLevel, ConfidenceScore

logger = structlog.get_logger()


class ConfidenceScorer:
    """Scores confidence in RAG responses.

    Factors considered:
    - Retrieval quality (top chunk similarity score)
    - Chunk coverage (number of relevant chunks found)
    - Grounding ratio (from hallucination check)
    """

    def __init__(
        self,
        *,
        high_threshold: float = 0.8,
        low_threshold: float = 0.5,
        min_chunks_for_high: int = 2,
    ) -> None:
        """Initialize the scorer.

        Args:
            high_threshold: Score threshold for high confidence.
            low_threshold: Score threshold below which confidence is low.
            min_chunks_for_high: Minimum chunks needed for high confidence.
        """
        self._high_threshold = high_threshold
        self._low_threshold = low_threshold
        self._min_chunks_for_high = min_chunks_for_high

    def score(
        self,
        *,
        chunk_scores: list[float],
        grounding_ratio: float | None = None,
    ) -> ConfidenceScore:
        """Calculate confidence score for a response.

        Args:
            chunk_scores: Similarity scores of retrieved chunks (0-1).
            grounding_ratio: Ratio of claims supported by chunks (0-1).
                If None, grounding is not considered.

        Returns:
            ConfidenceScore with level, score, and factors.
        """
        factors: dict[str, float] = {}

        # Factor 1: Top retrieval score (most important)
        if chunk_scores:
            top_score = max(chunk_scores)
            factors["retrieval_quality"] = top_score
        else:
            factors["retrieval_quality"] = 0.0

        # Factor 2: Chunk coverage (having multiple relevant chunks is better)
        if chunk_scores:
            # Score based on how many chunks have decent scores
            good_chunks = sum(1 for s in chunk_scores if s > 0.5)
            factors["chunk_coverage"] = min(
                good_chunks / self._min_chunks_for_high, 1.0
            )
        else:
            factors["chunk_coverage"] = 0.0

        # Factor 3: Grounding ratio (if hallucination check was run)
        if grounding_ratio is not None:
            factors["grounding"] = grounding_ratio

        # Calculate weighted score
        # Retrieval quality is most important, then grounding, then coverage
        if grounding_ratio is not None:
            computed_score = (
                factors["retrieval_quality"] * 0.4
                + factors["grounding"] * 0.4
                + factors["chunk_coverage"] * 0.2
            )
        else:
            computed_score = (
                factors["retrieval_quality"] * 0.6 + factors["chunk_coverage"] * 0.4
            )

        # Determine confidence level
        if (
            computed_score >= self._high_threshold
            and len(chunk_scores) >= self._min_chunks_for_high
        ):
            level = ConfidenceLevel.HIGH
            needs_review = False
        elif computed_score >= self._low_threshold:
            level = ConfidenceLevel.MEDIUM
            needs_review = False
        else:
            level = ConfidenceLevel.LOW
            needs_review = True

        result = ConfidenceScore(
            level=level,
            score=round(computed_score, 3),
            factors=factors,
            needs_review=needs_review,
        )

        logger.debug(
            "confidence_scored",
            level=level.value,
            score=result.score,
            factors=factors,
            needs_review=needs_review,
        )

        return result
