"""Tests for application configuration."""

import pytest

from retriever.config import Settings, _parse_origins_str, get_settings


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings load with sensible defaults when no env vars present."""
    monkeypatch.delenv("DEBUG", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.debug is False
    assert settings.langfuse_host == "https://us.cloud.langfuse.com"
    assert "http://localhost:5173" in settings.allowed_origins_list


def test_ai_gateway_base_url_fallback() -> None:
    """ai_gateway_base_url falls back to OpenRouter when CF not configured."""
    settings = Settings(cloudflare_account_id="", cloudflare_gateway_id="")
    assert settings.ai_gateway_base_url == "https://openrouter.ai/api/v1"


def test_ai_gateway_base_url_with_cloudflare() -> None:
    """ai_gateway_base_url returns CF gateway URL when both IDs are set."""
    settings = Settings(
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
    )
    url = settings.ai_gateway_base_url
    assert "gateway.ai.cloudflare.com" in url
    assert "acct123" in url
    assert "gw456" in url


def test_get_settings_returns_cached_instance() -> None:
    """get_settings returns the same instance on repeated calls."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_wildcard_origin_rejected() -> None:
    """Settings rejects wildcard '*' in allowed_origins."""
    with pytest.raises(Exception, match="Wildcard"):
        Settings(allowed_origins="*")


def test_parse_origins_json_array() -> None:
    """Parses valid JSON array."""
    assert _parse_origins_str('["http://a","http://b"]') == ["http://a", "http://b"]


def test_parse_origins_comma_separated() -> None:
    """Parses comma-separated string."""
    assert _parse_origins_str("http://a,http://b") == ["http://a", "http://b"]


def test_parse_origins_single_value() -> None:
    """Parses single origin."""
    assert _parse_origins_str("http://localhost:5173") == ["http://localhost:5173"]


def test_parse_origins_shell_escaped() -> None:
    r"""Handles shell-mangled JSON like [\"http://a\"]."""
    result = _parse_origins_str('[\\"http://a\\"]')
    assert "http://a" in result[0]


def test_parse_origins_empty() -> None:
    """Empty string returns empty list."""
    assert _parse_origins_str("") == []
