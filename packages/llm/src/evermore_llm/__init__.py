# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared OpenAI-compatible LLM gateway client builder for Evermore.

This package is the single canonical source for the AsyncOpenAI client
builder (:func:`build_gateway_client`) that every service routes outbound
model calls (chat, embeddings, moderation) through, decoupled from any one
service's settings via the structural :class:`GatewayConfig` protocol.
"""

from evermore_llm.gateway_client import (
    GatewayConfig,
    GatewayScope,
    build_gateway_client,
)

__all__ = ["GatewayConfig", "GatewayScope", "build_gateway_client"]
