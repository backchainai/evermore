"""Unit tests for evermore_llm.gateway_client (no live gateway required).

Uses a concrete fake ``GatewayConfig`` (a dataclass, not a ``MagicMock``) so
mypy checks the fake against the real structural contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from openai import AsyncOpenAI
from pydantic import SecretStr

from evermore_llm import GatewayScope, build_gateway_client


@dataclass
class FakeGatewayConfig:
    """A concrete ``GatewayConfig`` fake conforming structurally, not a mock."""

    base_url: str
    llm_gateway_auth_header: str = "cf-aig-authorization"
    llm_gateway_token: SecretStr = field(default_factory=lambda: SecretStr(""))
    scoped_tokens: dict[GatewayScope, SecretStr] = field(default_factory=dict)
    raise_on_base_url: bool = False

    @property
    def llm_gateway_base_url(self) -> str:
        if self.raise_on_base_url:
            raise ValueError(
                "No LLM gateway configured. Set LLM_GATEWAY_URL, or "
                "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_GATEWAY_ID."
            )
        return self.base_url

    def gateway_token_for(self, scope: GatewayScope | None) -> SecretStr:
        """Resolve a scoped token, raising if asked to resolve ``None``.

        ``build_gateway_client`` reads ``llm_gateway_token`` directly on the
        ``scope is None`` path and only calls this method with a real scope.
        Raising here pins that branch: collapsing it into an unconditional
        ``gateway_token_for(scope)`` call fails these tests instead of passing
        silently because both paths happen to return the same token.
        """
        if scope is None:
            raise AssertionError(
                "gateway_token_for must not be called with scope=None; "
                "build_gateway_client reads llm_gateway_token directly."
            )
        scoped = self.scoped_tokens.get(scope)
        if scoped is not None and scoped.get_secret_value():
            return scoped
        return self.llm_gateway_token


def test_build_gateway_client_sets_base_url() -> None:
    """Client uses the gateway base URL from the config."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat"
    )
    client = build_gateway_client(config)

    assert isinstance(client, AsyncOpenAI)
    assert str(client.base_url).rstrip("/").endswith("/compat")


def test_build_gateway_client_adds_auth_header_when_token_present() -> None:
    """A non-empty gateway token sets the configured auth header."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        llm_gateway_token=SecretStr("cf-token-123"),
    )

    client = build_gateway_client(config)

    assert client.default_headers["cf-aig-authorization"] == "Bearer cf-token-123"


def test_build_gateway_client_uses_configured_header_name() -> None:
    """The auth header name comes from the config, not a hardcoded literal."""
    config = FakeGatewayConfig(
        base_url="https://my-gateway.example.com/v1",
        llm_gateway_auth_header="authorization",
        llm_gateway_token=SecretStr("tok-456"),
    )

    client = build_gateway_client(config)

    assert client.default_headers["authorization"] == "Bearer tok-456"


def test_build_gateway_client_omits_auth_header_when_token_absent() -> None:
    """An empty gateway token leaves the auth header unset."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat"
    )

    client = build_gateway_client(config)

    assert "cf-aig-authorization" not in client.default_headers


def test_build_gateway_client_uses_placeholder_api_key_when_token_empty() -> None:
    """The SDK requires a non-empty api_key; an empty token yields a placeholder."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat"
    )

    client = build_gateway_client(config)

    assert client.api_key == "unused"


def test_build_gateway_client_uses_token_as_api_key_when_present() -> None:
    """When a gateway token is set, it doubles as the SDK api_key value."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        llm_gateway_token=SecretStr("cf-token-123"),
    )

    client = build_gateway_client(config)

    assert client.api_key == "cf-token-123"


def test_build_gateway_client_uses_scoped_chat_token() -> None:
    """scope='chat' puts the chat-scoped token on the header, not the shared one."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        llm_gateway_token=SecretStr("shared-token"),
        scoped_tokens={"chat": SecretStr("chat-token")},
    )

    client = build_gateway_client(config, scope="chat")

    assert client.default_headers["cf-aig-authorization"] == "Bearer chat-token"
    assert client.api_key == "chat-token"


def test_build_gateway_client_scope_falls_back_to_shared_token() -> None:
    """A scope whose field is empty falls back to the shared token on the header."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        llm_gateway_token=SecretStr("shared-token"),
    )

    client = build_gateway_client(config, scope="embeddings")

    assert client.default_headers["cf-aig-authorization"] == "Bearer shared-token"
    assert client.api_key == "shared-token"


def test_build_gateway_client_scope_none_uses_shared_token_directly() -> None:
    """scope=None (default) uses the shared token even when scoped fields are set."""
    config = FakeGatewayConfig(
        base_url="https://gateway.ai.cloudflare.com/v1/a/b/compat",
        llm_gateway_token=SecretStr("shared-token"),
        scoped_tokens={"chat": SecretStr("chat-token")},
    )

    client = build_gateway_client(config)

    assert client.default_headers["cf-aig-authorization"] == "Bearer shared-token"


def test_build_gateway_client_propagates_base_url_error() -> None:
    """A config whose llm_gateway_base_url raises propagates that raise unchanged."""
    config = FakeGatewayConfig(base_url="unused", raise_on_base_url=True)

    with pytest.raises(ValueError, match="No LLM gateway configured"):
        build_gateway_client(config)
