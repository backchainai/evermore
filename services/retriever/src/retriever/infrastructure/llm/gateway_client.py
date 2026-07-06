# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared AsyncOpenAI client builder for the OpenAI-compatible LLM gateway.

One base URL and one client serve chat, embeddings, and moderation through the
gateway's OpenAI-compatible endpoint. Provider keys live in the gateway (BYOK);
the app authenticates with a single token sent via a configurable auth header,
so this builder carries no gateway-specific identifiers. An optional ``scope``
narrows the token used to one traffic class (chat, embeddings, moderation),
shrinking the blast radius of a single leaked token; see
``Settings.gateway_token_for``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from retriever.config import GatewayScope, Settings


def build_gateway_client(
    settings: Settings,
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
