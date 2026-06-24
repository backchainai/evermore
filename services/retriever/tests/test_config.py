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


def test_llm_gateway_base_url_raises_when_unconfigured() -> None:
    """llm_gateway_base_url raises when no gateway is configured (no fallback)."""
    settings = Settings(
        llm_gateway_url="",
        cloudflare_account_id="",
        cloudflare_gateway_id="",
    )
    with pytest.raises(ValueError, match="No LLM gateway configured"):
        _ = settings.llm_gateway_base_url


def test_llm_gateway_base_url_with_cloudflare() -> None:
    """llm_gateway_base_url returns the CF compat gateway URL when both IDs are set."""
    settings = Settings(
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
    )
    url = settings.llm_gateway_base_url
    assert "gateway.ai.cloudflare.com" in url
    assert "acct123" in url
    assert "gw456" in url
    # One base URL serves chat, embeddings, and moderation via the compat endpoint.
    assert url.endswith("/compat")
    assert "/openai" not in url


def test_llm_gateway_url_overrides_everything() -> None:
    """An explicit llm_gateway_url is returned verbatim, ignoring the CF IDs."""
    override = "https://my-gateway.example.com/v1"
    settings = Settings(
        llm_gateway_url=override,
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
    )
    assert settings.llm_gateway_base_url == override


def test_llm_gateway_auth_header_default() -> None:
    """llm_gateway_auth_header defaults to the Cloudflare AI Gateway header."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_gateway_auth_header == "cf-aig-authorization"


def test_llm_gateway_token_default() -> None:
    """llm_gateway_token is an empty SecretStr by default."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_gateway_token.get_secret_value() == ""


def test_fallback_llm_model_default() -> None:
    """fallback_llm_model defaults to the cheap Haiku slug."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.fallback_llm_model == "anthropic/claude-haiku-4-5"


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
