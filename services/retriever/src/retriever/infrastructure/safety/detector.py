# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Prompt injection detection using pattern matching."""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger()

# Patterns for common prompt injection attempts
# These patterns are case-insensitive and match common attack vectors
INJECTION_PATTERNS: list[tuple[str, str]] = [
    # Instruction override attempts
    (r"ignore .{0,30}(instructions|rules|guidelines)", "ignore_instructions"),
    (r"disregard .{0,30}(instructions|rules|guidelines)", "disregard_instructions"),
    (r"forget .{0,30}(instructions|rules|guidelines)", "forget_instructions"),
    (r"override .{0,30}(instructions|rules|guidelines)", "override_instructions"),
    # Role manipulation
    (r"you are now", "role_change"),
    (r"act as", "role_change"),
    (r"pretend (to be|you are|that you)", "role_change"),
    (r"roleplay as", "role_change"),
    (r"new (instructions|task|role|persona)", "new_role"),
    # System prompt extraction
    (
        r"(reveal|show|display|output|print) .{0,20}(system|original|initial) "
        r"(prompt|instructions)",
        "prompt_extraction",
    ),
    (
        r"what (are|is) your (system|original|initial) (prompt|instructions)",
        "prompt_extraction",
    ),
    (r"system prompt", "prompt_extraction"),
    (r"(initial|original) instructions", "prompt_extraction"),
    # Developer/debug mode attempts
    (r"(developer|debug|admin|maintenance) mode", "debug_mode"),
    (r"enable (developer|debug|admin) (mode|access)", "debug_mode"),
    # Jailbreak attempts
    (r"jailbreak", "jailbreak"),
    (r"dan mode", "jailbreak"),
    (r"do anything now", "jailbreak"),
]

# Compile patterns for efficiency
_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), name) for pattern, name in INJECTION_PATTERNS
]


class PromptInjectionDetector:
    """Detects prompt injection attempts using pattern matching.

    This provides a lightweight defense against common prompt injection
    attacks. It should be used as part of a layered security approach.
    """

    def __init__(
        self, *, additional_patterns: list[tuple[str, str]] | None = None
    ) -> None:
        """Initialize the detector.

        Args:
            additional_patterns: Optional list of (pattern, name) tuples to add
                to the default patterns.
        """
        self._patterns = list(_COMPILED_PATTERNS)

        if additional_patterns:
            for pattern, name in additional_patterns:
                self._patterns.append((re.compile(pattern, re.IGNORECASE), name))

    def is_injection(self, text: str) -> bool:
        """Check if text contains a prompt injection attempt.

        Args:
            text: The text to check.

        Returns:
            True if an injection pattern was detected, False otherwise.
        """
        matched_pattern = self.get_matched_pattern(text)
        return matched_pattern is not None

    def get_matched_pattern(self, text: str) -> str | None:
        """Get the name of the matched injection pattern, if any.

        Args:
            text: The text to check.

        Returns:
            The name of the matched pattern, or None if no pattern matched.
        """
        for pattern, name in self._patterns:
            if pattern.search(text):
                logger.warning(
                    "prompt_injection_detected",
                    pattern_name=name,
                    text_preview=text[:100],
                )
                return name

        return None
