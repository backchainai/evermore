# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared LLM gateway transport for Evermore: one AsyncOpenAI client builder.

This package is the single canonical source for :func:`build_gateway_client`,
which builds one ``AsyncOpenAI`` client pointed at the OpenAI-compatible LLM
gateway (see ADR 0028), plus the :class:`GatewaySettings` structural
:class:`~typing.Protocol` it reads and the :data:`GatewayScope` traffic-class
literal.
"""

from evermore_llm.gateway_client import (
    GatewayScope,
    GatewaySettings,
    build_gateway_client,
)

__all__ = [
    "GatewayScope",
    "GatewaySettings",
    "build_gateway_client",
]
