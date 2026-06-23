# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""LLM provider abstraction layer."""

from retriever.infrastructure.llm.exceptions import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from retriever.infrastructure.llm.fallback import FallbackLLMProvider
from retriever.infrastructure.llm.openai_compat import OpenAICompatProvider
from retriever.infrastructure.llm.protocol import LLMProvider

__all__ = [
    "FallbackLLMProvider",
    "LLMConfigurationError",
    "LLMProvider",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "OpenAICompatProvider",
]
