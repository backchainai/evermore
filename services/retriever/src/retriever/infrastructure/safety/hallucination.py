# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Hallucination detection by verifying claims against source chunks."""

from __future__ import annotations

import re

import structlog

from retriever.infrastructure.safety.schemas import (
    ClaimVerification,
    HallucinationCheckResult,
)

logger = structlog.get_logger()

# Common English stop words to exclude from keyword matching
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "it",
        "its",
        "you",
        "your",
        "they",
        "their",
        "this",
        "that",
        "these",
        "those",
        "i",
        "we",
        "he",
        "she",
    }
)


class HallucinationDetector:
    """Detects hallucinations by verifying claims against source chunks.

    This detector extracts factual claims from the answer and checks
    whether each claim is supported by the retrieved source chunks.
    """

    def __init__(
        self,
        *,
        support_threshold: float = 0.8,
        min_claim_length: int = 10,
    ) -> None:
        """Initialize the detector.

        Args:
            support_threshold: Minimum ratio of supported claims to consider
                the answer grounded (0.0 to 1.0).
            min_claim_length: Minimum length of a sentence to be considered
                a claim (filters out short phrases).
        """
        self._threshold = support_threshold
        self._min_claim_length = min_claim_length

    def check(
        self,
        answer: str,
        chunks: list[str],
        sources: list[str] | None = None,
    ) -> HallucinationCheckResult:
        """Check if the answer is grounded in the source chunks.

        Args:
            answer: The generated answer text.
            chunks: List of source chunk texts.
            sources: Optional list of source identifiers corresponding to chunks.

        Returns:
            HallucinationCheckResult with grounding status and details.
        """
        claims = self._extract_claims(answer)

        if not claims:
            # No claims to verify - consider grounded
            return HallucinationCheckResult(
                is_grounded=True,
                support_ratio=1.0,
                claims=[],
                total_claims=0,
                supported_claims=0,
            )

        verifications: list[ClaimVerification] = []
        resolved_sources = sources or ["source"] * len(chunks)

        for claim in claims:
            supported, source = self._is_supported(claim, chunks, resolved_sources)
            verifications.append(
                ClaimVerification(
                    claim=claim,
                    supported=supported,
                    supporting_source=source,
                )
            )

        supported_count = sum(1 for v in verifications if v.supported)
        support_ratio = supported_count / len(claims)
        is_grounded = support_ratio >= self._threshold

        if not is_grounded:
            unsupported = [v.claim for v in verifications if not v.supported]
            logger.warning(
                "hallucination_detected",
                support_ratio=round(support_ratio, 2),
                total_claims=len(claims),
                supported_claims=supported_count,
                unsupported_claims=unsupported[:3],  # Log first 3 unsupported
            )

        return HallucinationCheckResult(
            is_grounded=is_grounded,
            support_ratio=support_ratio,
            claims=verifications,
            total_claims=len(claims),
            supported_claims=supported_count,
        )

    def _extract_claims(self, answer: str) -> list[str]:
        """Extract factual claims from an answer.

        This uses a simple heuristic: split into sentences and filter
        for declarative statements that are long enough to be claims.

        Args:
            answer: The answer text.

        Returns:
            List of extracted claim strings.
        """
        # Split on sentence boundaries
        sentences = re.split(r"[.!?]+", answer)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()

            # Skip short sentences
            if len(sentence) < self._min_claim_length:
                continue

            # Skip questions
            if sentence.endswith("?") or sentence.startswith(
                ("Can ", "Could ", "Would ", "Should ", "May ", "Might ")
            ):
                continue

            # Skip first-person statements that are meta-commentary
            if sentence.lower().startswith(
                ("i ", "i'm ", "i am ", "based on ", "according to ")
            ):
                continue

            # Skip hedged statements
            if any(
                hedge in sentence.lower()
                for hedge in [
                    "i'm not sure",
                    "i don't know",
                    "i cannot",
                    "i can't",
                ]
            ):
                continue

            claims.append(sentence)

        return claims

    def _is_supported(
        self,
        claim: str,
        chunks: list[str],
        sources: list[str],
    ) -> tuple[bool, str | None]:
        """Check if a claim is supported by any source chunk.

        Uses keyword overlap to determine support. This is a simple
        but effective heuristic for detecting obvious hallucinations.

        Args:
            claim: The claim to verify.
            chunks: List of source chunk texts.
            sources: List of source identifiers.

        Returns:
            Tuple of (is_supported, supporting_source or None).
        """
        claim_lower = claim.lower()
        claim_words = set(self._extract_keywords(claim_lower))

        # Need at least some meaningful keywords to check
        if len(claim_words) < 2:
            return True, None  # Can't verify, assume ok

        for chunk, source in zip(chunks, sources, strict=False):
            chunk_lower = chunk.lower()
            chunk_words = set(self._extract_keywords(chunk_lower))

            # Calculate keyword overlap
            overlap = claim_words & chunk_words
            overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0

            # If significant keyword overlap, consider supported
            if overlap_ratio >= 0.5:
                return True, source

            # Also check for substring matches of key phrases
            # This catches exact quotes or close paraphrases
            if len(claim) > 20 and claim_lower in chunk_lower:
                return True, source

        return False, None

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Extract meaningful keywords from text.

        Removes common stop words to focus on content words.

        Args:
            text: The text to extract keywords from.

        Returns:
            List of keyword strings.
        """
        # Extract words (alphanumeric sequences)
        words = re.findall(r"\b[a-z0-9]+\b", text)

        # Filter out stop words and very short words
        return [w for w in words if w not in _STOP_WORDS and len(w) > 2]
