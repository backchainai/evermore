# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Schemas for content safety."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class SafetyViolationType(StrEnum):
    """Types of safety violations detected."""

    NONE = "none"
    MODERATION_FLAGGED = "moderation_flagged"
    PROMPT_INJECTION = "prompt_injection"
    HALLUCINATION = "hallucination"


class ModerationResult(BaseModel):
    """Result from content moderation API.

    Attributes:
        flagged: Whether the content was flagged as unsafe.
        categories: Dictionary of category names to boolean flags.
        category_scores: Dictionary of category names to confidence scores.
    """

    model_config = ConfigDict(frozen=True)

    flagged: bool
    categories: dict[str, bool]
    category_scores: dict[str, float]

    @classmethod
    def safe(cls) -> ModerationResult:
        """Create a safe (not flagged) result."""
        return cls(flagged=False, categories={}, category_scores={})


class SafetyCheckResult(BaseModel):
    """Combined result from all safety checks.

    Attributes:
        is_safe: Whether the content passed all safety checks.
        violation_type: Type of violation detected, if any.
        message: Human-readable message describing the result.
        details: Additional details about the check.
    """

    model_config = ConfigDict(frozen=True)

    is_safe: bool
    violation_type: SafetyViolationType
    message: str
    details: dict[str, object] | None = None

    @classmethod
    def passed(cls) -> SafetyCheckResult:
        """Create a passed safety check result."""
        return cls(
            is_safe=True,
            violation_type=SafetyViolationType.NONE,
            message="Content passed safety checks.",
        )

    @classmethod
    def failed_moderation(
        cls, categories: dict[str, bool] | None = None
    ) -> SafetyCheckResult:
        """Create a failed result due to moderation flags."""
        return cls(
            is_safe=False,
            violation_type=SafetyViolationType.MODERATION_FLAGGED,
            message="I can only answer questions about volunteer policies and procedures.",
            details={"flagged_categories": categories} if categories else None,
        )

    @classmethod
    def failed_injection(cls, pattern: str | None = None) -> SafetyCheckResult:
        """Create a failed result due to prompt injection detection."""
        return cls(
            is_safe=False,
            violation_type=SafetyViolationType.PROMPT_INJECTION,
            message="I can only answer questions about volunteer policies and procedures.",
            details={"matched_pattern": pattern} if pattern else None,
        )

    @classmethod
    def failed_hallucination(
        cls, support_ratio: float | None = None
    ) -> SafetyCheckResult:
        """Create a failed result due to hallucination detection."""
        return cls(
            is_safe=False,
            violation_type=SafetyViolationType.HALLUCINATION,
            message="I don't have enough information to answer that confidently.",
            details={"support_ratio": support_ratio}
            if support_ratio is not None
            else None,
        )


class ClaimVerification(BaseModel):
    """Result of verifying a single claim.

    Attributes:
        claim: The extracted claim text.
        supported: Whether the claim is supported by the sources.
        supporting_source: The source that supports the claim, if any.
    """

    model_config = ConfigDict(frozen=True)

    claim: str
    supported: bool
    supporting_source: str | None = None


class HallucinationCheckResult(BaseModel):
    """Result of hallucination detection.

    Attributes:
        is_grounded: Whether the answer is grounded in the sources.
        support_ratio: Ratio of supported claims (0.0 to 1.0).
        claims: List of individual claim verifications.
        total_claims: Total number of claims extracted.
        supported_claims: Number of claims that are supported.
    """

    model_config = ConfigDict(frozen=True)

    is_grounded: bool
    support_ratio: float
    claims: list[ClaimVerification]
    total_claims: int
    supported_claims: int


class ConfidenceLevel(StrEnum):
    """Confidence level categories."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceScore(BaseModel):
    """Confidence score for a RAG response.

    Attributes:
        level: Categorical confidence level (high/medium/low).
        score: Numeric score between 0.0 and 1.0.
        factors: Dict of factors contributing to the score.
        needs_review: Whether this response should be flagged for human review.
    """

    model_config = ConfigDict(frozen=True)

    level: ConfidenceLevel
    score: float
    factors: dict[str, float]
    needs_review: bool
