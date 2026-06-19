"""Cookie-based authentication for Adalo API."""

from __future__ import annotations

import re

from petdata.config import get_settings
from petdata.modules.api.exceptions import APIAuthenticationError


class CookieAuth:
    """Cookie-based authentication for Adalo API.

    Validates cookie presence and format, provides headers for HTTP requests.
    Cookies must be in format: "key1=value1; key2=value2"

    Example:
        >>> auth = CookieAuth()
        >>> headers = auth.get_headers()
        >>> headers["Cookie"]
        'session_id=abc123; user_token=xyz789'
    """

    # Regex pattern for cookie format validation
    # Matches: word chars/hyphens=word chars/hyphens, optionally repeated with '; '
    _COOKIE_PATTERN = re.compile(r"^[\w\-]+=[\w\-]+(?:; [\w\-]+=[\w\-]+)*$")

    def __init__(self, cookies: str | None = None) -> None:
        """Initialize authentication with cookies.

        Args:
            cookies: Cookie string in format "key=value; key=value".
                If None, reads from PETDATA_COOKIES environment variable.

        Raises:
            APIAuthenticationError: If cookies are missing, empty, or invalid.
        """
        settings = get_settings()
        self._cookies = cookies if cookies is not None else settings.cookies
        self._validate_format()

    def _validate_format(self) -> None:
        """Validate cookie format and reject header injection attempts.

        Raises:
            APIAuthenticationError: If cookies are missing, empty, contain
                header injection characters, or don't match expected format.
        """
        if not self._cookies:
            msg = (
                "PETDATA_COOKIES environment variable is required. "
                "Set it to your Adalo session cookies "
                "(format: 'key1=value1; key2=value2')"
            )
            raise APIAuthenticationError(msg)

        # Reject header injection attempts
        if any(char in self._cookies for char in ["\n", "\r", "\x00"]):
            msg = (
                "Invalid characters in cookies (newline, carriage return, or null byte)"
            )
            raise APIAuthenticationError(msg)

        # Validate basic format
        if not self._COOKIE_PATTERN.match(self._cookies):
            msg = (
                "Invalid cookie format. Expected 'key1=value1; key2=value2' "
                "with alphanumeric keys and values (hyphens allowed)"
            )
            raise APIAuthenticationError(msg)

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers with cookie authentication.

        Returns:
            Dictionary with Cookie and Accept headers.

        Example:
            >>> auth = CookieAuth(cookies="session=abc123")
            >>> headers = auth.get_headers()
            >>> headers["Cookie"]
            'session=abc123'
        """
        return {
            "Cookie": self._cookies,
            "Accept": "application/json",
        }

    @property
    def is_valid(self) -> bool:
        """Check if authentication credentials are present and formatted.

        Returns:
            True if cookies are non-empty and passed format validation.

        Note:
            This does NOT verify if cookies are expired or work with the API.
            It only checks format validity.
        """
        return bool(self._cookies and self._cookies.strip())
