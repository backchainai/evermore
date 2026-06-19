"""Custom exceptions for Adalo API operations."""

from __future__ import annotations


class APIError(Exception):
    """Base exception for API operations."""


class APIAuthenticationError(APIError):
    """Authentication failed (invalid/missing cookies)."""


class APIValidationError(APIError):
    """Response format or validation errors."""


class APIRateLimitError(APIError):
    """Rate limit exceeded (429) after all retries."""


class APIServerError(APIError):
    """Server error (5xx) after all retries.

    Attributes:
        status_code: HTTP status code if available.
        response_body: Response body text if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        """Initialize server error with optional debugging info.

        Args:
            message: Error description.
            status_code: HTTP status code (e.g., 500, 502).
            response_body: Response body text for debugging.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class APINetworkError(APIError):
    """Network error (connection/timeout) after all retries."""


class APIResponseParseError(APIError):
    """Failed to parse response JSON."""
