"""Unit tests for application settings."""

from __future__ import annotations

from petdata.config import Settings


class TestCookiesSecrecy:
    """Tests that the SMS session cookie never surfaces in plaintext."""

    def test_repr_does_not_expose_cookie_plaintext(self):
        """repr(settings) masks the cookie value instead of leaking it."""
        settings = Settings(cookies="session=abc123")
        assert "abc123" not in repr(settings)
        assert "**********" in repr(settings)

    def test_str_does_not_expose_cookie_plaintext(self):
        """str(settings) masks the cookie value instead of leaking it."""
        settings = Settings(cookies="session=abc123")
        assert "abc123" not in str(settings)
        assert "**********" in str(settings)

    def test_get_secret_value_round_trips_raw_cookie(self):
        """get_secret_value() still returns the original cookie string."""
        settings = Settings(cookies="session=abc123")
        assert settings.cookies.get_secret_value() == "session=abc123"
