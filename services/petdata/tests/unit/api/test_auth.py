"""Unit tests for cookie-based authentication."""

from __future__ import annotations

import pytest

from petbio.modules.api.auth import CookieAuth
from petbio.modules.api.exceptions import APIAuthenticationError


class TestCookieValidation:
    """Tests for cookie format validation."""

    def test_missing_cookies_raises_error(self):
        """CookieAuth raises error when PETBIO_COOKIES not set."""
        with pytest.raises(APIAuthenticationError, match=r"PETBIO_COOKIES.*required"):
            CookieAuth(cookies="")

    def test_empty_cookies_raises_error(self):
        """CookieAuth raises error for empty cookie string."""
        with pytest.raises(APIAuthenticationError, match=r"PETBIO_COOKIES.*required"):
            CookieAuth(cookies="")

    def test_whitespace_only_cookies_raises_error(self):
        """CookieAuth raises error for whitespace-only cookies."""
        with pytest.raises(APIAuthenticationError, match="Invalid cookie format"):
            CookieAuth(cookies="   ")

    def test_cookies_with_newline_raises_error(self):
        """CookieAuth rejects cookies containing newline characters."""
        with pytest.raises(APIAuthenticationError, match="Invalid characters"):
            CookieAuth(cookies="session=abc123\nmalicious=header")

    def test_cookies_with_carriage_return_raises_error(self):
        """CookieAuth rejects cookies containing carriage return."""
        with pytest.raises(APIAuthenticationError, match="Invalid characters"):
            CookieAuth(cookies="session=abc123\rmalicious=header")

    def test_cookies_with_null_byte_raises_error(self):
        """CookieAuth rejects cookies containing null byte."""
        with pytest.raises(APIAuthenticationError, match="Invalid characters"):
            CookieAuth(cookies="session=abc123\x00malicious=header")

    def test_invalid_format_no_equals_raises_error(self):
        """CookieAuth rejects cookies without equals sign."""
        with pytest.raises(APIAuthenticationError, match="Invalid cookie format"):
            CookieAuth(cookies="invalid_cookie_format")

    def test_invalid_format_missing_key_raises_error(self):
        """CookieAuth rejects cookies with missing key."""
        with pytest.raises(APIAuthenticationError, match="Invalid cookie format"):
            CookieAuth(cookies="=value")

    def test_invalid_format_missing_value_raises_error(self):
        """CookieAuth rejects cookies with missing value."""
        with pytest.raises(APIAuthenticationError, match="Invalid cookie format"):
            CookieAuth(cookies="key=")

    def test_valid_single_cookie_passes(self):
        """CookieAuth accepts valid single cookie."""
        auth = CookieAuth(cookies="session=abc123")
        assert auth.is_valid

    def test_valid_multiple_cookies_passes(self):
        """CookieAuth accepts valid multiple cookies."""
        auth = CookieAuth(cookies="session=abc123; user=xyz789")
        assert auth.is_valid

    def test_valid_cookies_with_hyphens_passes(self):
        """CookieAuth accepts cookies with hyphens in keys and values."""
        auth = CookieAuth(cookies="session-id=abc-123; user-token=xyz-789")
        assert auth.is_valid

    def test_valid_cookies_with_underscores_passes(self):
        """CookieAuth accepts cookies with underscores."""
        auth = CookieAuth(cookies="session_id=abc_123")
        assert auth.is_valid


class TestGetHeaders:
    """Tests for header generation."""

    def test_get_headers_includes_cookie(self):
        """get_headers returns Cookie header."""
        auth = CookieAuth(cookies="session=abc123")
        headers = auth.get_headers()
        assert "Cookie" in headers
        assert headers["Cookie"] == "session=abc123"

    def test_get_headers_includes_accept(self):
        """get_headers returns Accept header for JSON."""
        auth = CookieAuth(cookies="session=abc123")
        headers = auth.get_headers()
        assert "Accept" in headers
        assert headers["Accept"] == "application/json"

    def test_get_headers_preserves_cookie_value(self):
        """get_headers preserves exact cookie value."""
        cookies = "session=abc123; user=xyz789; token=def456"
        auth = CookieAuth(cookies=cookies)
        headers = auth.get_headers()
        assert headers["Cookie"] == cookies


class TestIsValid:
    """Tests for is_valid property."""

    def test_is_valid_true_for_non_empty_cookies(self):
        """is_valid returns True for non-empty cookies."""
        auth = CookieAuth(cookies="session=abc123")
        assert auth.is_valid is True

    def test_is_valid_only_checks_format(self):
        """is_valid only validates format, not actual authentication."""
        # This will pass format validation but may not work with API
        auth = CookieAuth(cookies="fake=cookie")
        assert auth.is_valid is True
