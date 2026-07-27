# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared AsyncOpenAI client builder for the OpenAI-compatible LLM gateway.

One base URL and one client serve chat, embeddings, and moderation through the
gateway's OpenAI-compatible endpoint. Provider keys live in the gateway (BYOK);
the app authenticates with a single token sent via a configurable auth header,
so this builder carries no gateway-specific identifiers. An optional ``scope``
narrows the token used to one traffic class (chat, embeddings, moderation),
shrinking the blast radius of a single leaked token; see
``GatewayConfig.gateway_token_for``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from pydantic import SecretStr

# Per-traffic-class gateway token scope. Narrows the blast radius of a
# leaked token to one model traffic class (chat, embeddings, moderation)
# instead of all gateway traffic authenticated by the shared token.
GatewayScope = Literal["chat", "embeddings", "moderation"]


class GatewayConfig(Protocol):
    """Structural config surface that ``build_gateway_client`` reads from."""

    llm_gateway_auth_header: str
    llm_gateway_token: SecretStr

    @property
    def llm_gateway_base_url(self) -> str: ...

    def gateway_token_for(self, scope: GatewayScope | None) -> SecretStr: ...


def build_gateway_client(
    config: GatewayConfig,
    *,
    scope: GatewayScope | None = None,
    timeout_seconds: float = 30.0,
) -> AsyncOpenAI:
    """Construct an AsyncOpenAI client pointed at the LLM gateway.

    Authentication is a single BYOK token: provider keys live in the gateway,
    and the app authenticates with the gateway via the configured auth header.
    The OpenAI SDK requires a non-empty ``api_key``, so when no token is set a
    harmless placeholder is used; for a BYOK gateway the Authorization bearer
    is ignored in favor of the gateway's stored keys plus the auth header.

    Args:
        config: Configuration supplying the gateway base URL, token, and auth
            header name.
        scope: Optional traffic-class scope ("chat", "embeddings",
            "moderation"). When given, the token is resolved via
            ``config.gateway_token_for(scope)``, which prefers the matching
            scoped token and falls back to the shared ``llm_gateway_token``
            when the scoped token is unset. When omitted (None), the shared
            ``llm_gateway_token`` is used directly.
        timeout_seconds: Request timeout in seconds.

    Returns:
        An AsyncOpenAI client whose base URL is config.llm_gateway_base_url
        and which sends the configured auth header when a gateway token is set.

    Raises:
        ValueError: If no LLM gateway is configured (propagated from
            config.llm_gateway_base_url).
    """
    if scope is None:
        token = config.llm_gateway_token.get_secret_value()
    else:
        token = config.gateway_token_for(scope).get_secret_value()
    default_headers = (
        {config.llm_gateway_auth_header: f"Bearer {token}"} if token else None
    )
    return AsyncOpenAI(
        api_key=token or "unused",
        base_url=config.llm_gateway_base_url,
        timeout=timeout_seconds,
        default_headers=default_headers,
    )
