# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Safety service orchestrating all content safety checks."""

from __future__ import annotations

import structlog

from retriever.infrastructure.safety.detector import PromptInjectionDetector
from retriever.infrastructure.safety.hallucination import HallucinationDetector
from retriever.infrastructure.safety.moderation import (
    ModerationProvider,
    NoOpModerator,
)
from retriever.infrastructure.safety.schemas import (
    HallucinationCheckResult,
    SafetyCheckResult,
)

logger = structlog.get_logger()


class SafetyService:
    """Orchestrates all content safety checks.

    This service provides a unified interface for:
    - Input moderation (OpenAI Moderation API)
    - Prompt injection detection (pattern-based)
    - Output moderation
    - Hallucination detection (claim verification)
    """

    def __init__(
        self,
        moderator: ModerationProvider | None = None,
        *,
        injection_detector: PromptInjectionDetector | None = None,
        hallucination_detector: HallucinationDetector | None = None,
    ) -> None:
        """Initialize the safety service.

        Args:
            moderator: Content moderation provider. If None, uses NoOpModerator.
            injection_detector: Prompt injection detector. If None, creates default.
            hallucination_detector: Hallucination detector. If None, creates default.
        """
        self._moderator: ModerationProvider = moderator or NoOpModerator()
        self._injection_detector = injection_detector or PromptInjectionDetector()
        self._hallucination_detector = hallucination_detector or HallucinationDetector()

    async def check_input(self, text: str) -> SafetyCheckResult:
        """Check if input text is safe.

        Runs prompt injection detection and content moderation.

        Args:
            text: The user input text to check.

        Returns:
            SafetyCheckResult indicating whether input is safe.
        """
        # Check for prompt injection first (fast, no API call)
        matched_pattern = self._injection_detector.get_matched_pattern(text)
        if matched_pattern:
            logger.warning(
                "safety_input_blocked",
                reason="prompt_injection",
                pattern=matched_pattern,
                text_length=len(text),
            )
            return SafetyCheckResult.failed_injection(matched_pattern)

        # Check content moderation
        moderation_result = await self._moderator.check(text)
        if moderation_result.flagged:
            flagged_categories: dict[str, bool] = {
                cat: flagged
                for cat, flagged in moderation_result.categories.items()
                if flagged
            }
            logger.warning(
                "safety_input_blocked",
                reason="moderation",
                categories=list(flagged_categories.keys()),
                text_length=len(text),
            )
            return SafetyCheckResult.failed_moderation(flagged_categories)

        logger.debug("safety_input_passed", text_length=len(text))
        return SafetyCheckResult.passed()

    async def check_output(self, text: str) -> SafetyCheckResult:
        """Check if output text is safe.

        Runs content moderation on the generated response.

        Args:
            text: The generated response text to check.

        Returns:
            SafetyCheckResult indicating whether output is safe.
        """
        moderation_result = await self._moderator.check(text)
        if moderation_result.flagged:
            flagged_categories: dict[str, bool] = {
                cat: flagged
                for cat, flagged in moderation_result.categories.items()
                if flagged
            }
            logger.warning(
                "safety_output_blocked",
                reason="moderation",
                categories=list(flagged_categories.keys()),
                text_length=len(text),
            )
            return SafetyCheckResult.failed_moderation(flagged_categories)

        logger.debug("safety_output_passed", text_length=len(text))
        return SafetyCheckResult.passed()

    def check_hallucination(
        self,
        answer: str,
        chunks: list[str],
        sources: list[str] | None = None,
    ) -> SafetyCheckResult:
        """Check if answer is grounded in source chunks.

        Args:
            answer: The generated answer text.
            chunks: List of source chunk texts used for generation.
            sources: Optional list of source identifiers.

        Returns:
            SafetyCheckResult indicating whether answer is grounded.
        """
        result = self._hallucination_detector.check(answer, chunks, sources)

        if not result.is_grounded:
            logger.warning(
                "safety_hallucination_detected",
                support_ratio=result.support_ratio,
                total_claims=result.total_claims,
                supported_claims=result.supported_claims,
            )
            return SafetyCheckResult.failed_hallucination(result.support_ratio)

        logger.debug(
            "safety_grounded",
            support_ratio=result.support_ratio,
            total_claims=result.total_claims,
        )
        return SafetyCheckResult.passed()

    def get_hallucination_details(
        self,
        answer: str,
        chunks: list[str],
        sources: list[str] | None = None,
    ) -> HallucinationCheckResult:
        """Get detailed hallucination check results.

        Use this for debugging or when you need claim-level details.

        Args:
            answer: The generated answer text.
            chunks: List of source chunk texts.
            sources: Optional list of source identifiers.

        Returns:
            HallucinationCheckResult with full details.
        """
        return self._hallucination_detector.check(answer, chunks, sources)

    async def close(self) -> None:
        """Close any open connections."""
        if hasattr(self._moderator, "close"):
            await self._moderator.close()
