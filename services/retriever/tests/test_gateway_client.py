"""Tests for the shared LLM gateway client builder."""

from __future__ import annotations

from unittest.mock import MagicMock

from openai import AsyncOpenAI

from retriever.infrastructure.llm.gateway_client import build_gateway_client


def _make_settings(
    *, base_url: str, token: str, auth_header: str = "cf-aig-authorization"
) -> MagicMock:
    """Build mock settings exposing the gateway fields the helper reads."""
    settings = MagicMock()
    settings.llm_gateway_base_url = base_url
    settings.llm_gateway_token.get_secret_value.return_value = token
    settings.llm_gateway_auth_header = auth_header
    return settings


def test_build_gateway_client_sets_base_url() -> None:
    """Client uses the gateway base URL from settings."""
    settings = _make_settings(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        token="",
    )

    client = build_gateway_client(settings)

    assert isinstance(client, AsyncOpenAI)
    assert str(client.base_url).rstrip("/").endswith("/compat")


def test_build_gateway_client_adds_auth_header_when_token_present() -> None:
    """A non-empty gateway token sets the configured auth header."""
    settings = _make_settings(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        token="cf-token-123",
    )

    client = build_gateway_client(settings)

    assert client.default_headers["cf-aig-authorization"] == "Bearer cf-token-123"


def test_build_gateway_client_uses_configured_header_name() -> None:
    """The auth header name comes from settings, not a hardcoded literal."""
    settings = _make_settings(
        base_url="https://my-gateway.example.com/v1",
        token="tok-456",
        auth_header="authorization",
    )

    client = build_gateway_client(settings)

    assert client.default_headers["authorization"] == "Bearer tok-456"


def test_build_gateway_client_omits_auth_header_when_token_absent() -> None:
    """An empty gateway token leaves the cf-aig-authorization header unset."""
    settings = _make_settings(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        token="",
    )

    client = build_gateway_client(settings)

    assert "cf-aig-authorization" not in client.default_headers


def test_build_gateway_client_uses_placeholder_api_key_when_token_empty() -> None:
    """The SDK requires a non-empty api_key; an empty token yields a placeholder."""
    settings = _make_settings(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        token="",
    )

    client = build_gateway_client(settings)

    assert client.api_key == "unused"


def test_build_gateway_client_uses_token_as_api_key_when_present() -> None:
    """When a gateway token is set, it doubles as the SDK api_key value."""
    settings = _make_settings(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        token="cf-token-123",
    )

    client = build_gateway_client(settings)

    assert client.api_key == "cf-token-123"
