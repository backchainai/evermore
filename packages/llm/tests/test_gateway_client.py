"""Tests for the shared LLM gateway client builder (pure, no service Settings).

These tests exercise :func:`build_gateway_client` against a minimal
``GatewaySettings``-conforming stub, never a real service ``Settings`` class
(that would import a service into this package, violating ADR 0001). The
scoped-token tests that need real ``retriever.config.Settings`` stay in
``services/retriever/tests/test_gateway_client.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import SecretStr

from evermore_llm import GatewayScope, build_gateway_client


@dataclass
class _StubGatewaySettings:
    """Minimal object structurally satisfying ``GatewaySettings``."""

    llm_gateway_token: SecretStr
    base_url: str
    llm_gateway_auth_header: str = "cf-aig-authorization"

    @property
    def llm_gateway_base_url(self) -> str:
        return self.base_url

    def gateway_token_for(self, scope: GatewayScope | None) -> SecretStr:  # noqa: ARG002
        return self.llm_gateway_token


def _make_settings(
    *, base_url: str, token: str, auth_header: str = "cf-aig-authorization"
) -> _StubGatewaySettings:
    """Build a stub settings object exposing the gateway fields the helper reads."""
    return _StubGatewaySettings(
        llm_gateway_token=SecretStr(token),
        base_url=base_url,
        llm_gateway_auth_header=auth_header,
    )


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
