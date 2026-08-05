# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared AsyncOpenAI client builder for the OpenAI-compatible LLM gateway.

One base URL and one client serve chat, embeddings, and moderation through the
gateway's OpenAI-compatible endpoint. Provider keys live in the gateway (BYOK);
the app authenticates with a single token sent via a configurable auth header,
so this builder carries no gateway-specific identifiers. An optional ``scope``
narrows the token used to one traffic class (chat, embeddings, moderation),
shrinking the blast radius of a single leaked token; see
``GatewaySettings.gateway_token_for``.

This module imports nothing from any Evermore service. ``GatewaySettings`` is a
structural :class:`typing.Protocol`: any settings object exposing its four
members (``llm_gateway_token``, ``llm_gateway_auth_header``,
``llm_gateway_base_url``, ``gateway_token_for``) satisfies it without
inheriting from anything defined here.
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


class GatewaySettings(Protocol):
    """Structural interface :func:`build_gateway_client` reads from settings.

    A service's own settings type (for example ``retriever.config.Settings``)
    implements this Protocol simply by exposing these members; no explicit
    inheritance, registration, or import of this package's types is required
    on the settings side.
    """

    llm_gateway_token: SecretStr
    llm_gateway_auth_header: str

    @property
    def llm_gateway_base_url(self) -> str: ...

    def gateway_token_for(self, scope: GatewayScope | None) -> SecretStr: ...


def build_gateway_client(
    settings: GatewaySettings,
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
        settings: Application settings supplying the gateway base URL, token,
            and auth header name.
        scope: Optional traffic-class scope ("chat", "embeddings",
            "moderation"). When given, the token is resolved via
            ``settings.gateway_token_for(scope)``, which prefers the matching
            scoped token and falls back to the shared ``llm_gateway_token``
            when the scoped token is unset. When omitted (None), the shared
            ``llm_gateway_token`` is used directly.
        timeout_seconds: Request timeout in seconds.

    Returns:
        An AsyncOpenAI client whose base URL is settings.llm_gateway_base_url
        and which sends the configured auth header when a gateway token is set.

    Raises:
        ValueError: If no LLM gateway is configured (propagated from
            settings.llm_gateway_base_url).
    """
    if scope is None:
        token = settings.llm_gateway_token.get_secret_value()
    else:
        token = settings.gateway_token_for(scope).get_secret_value()
    default_headers = (
        {settings.llm_gateway_auth_header: f"Bearer {token}"} if token else None
    )
    return AsyncOpenAI(
        api_key=token or "unused",
        base_url=settings.llm_gateway_base_url,
        timeout=timeout_seconds,
        default_headers=default_headers,
    )
