# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Langfuse LLM observability integration.

Provides @observe() decorator for tracing LLM calls with token tracking
and cost calculation.  When Langfuse is not configured (missing keys),
the decorator becomes a transparent pass-through — no runtime cost.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Re-export observe so callers import from one place.
# Langfuse's @observe() is a no-op when the client is not initialised.
try:
    from langfuse.decorators import observe as observe
except ImportError:  # pragma: no cover – langfuse is a required dep
    from functools import wraps

    def observe(**_kwargs: Any) -> Any:
        """Fallback no-op decorator when langfuse is not installed."""

        def _identity(fn: Any) -> Any:
            @wraps(fn)
            async def _wrapper(*args: Any, **kw: Any) -> Any:
                return await fn(*args, **kw)

            return _wrapper

        return _identity


__all__ = ["configure_langfuse", "flush_langfuse", "observe"]


def configure_langfuse(
    *,
    secret_key: str,
    public_key: str,
    host: str,
) -> None:
    """Initialise the Langfuse client if credentials are provided.

    Args:
        secret_key: Langfuse secret key.
        public_key: Langfuse public key.
        host: Langfuse host URL.
    """
    if not (secret_key and public_key and host):
        logger.info("langfuse.disabled", reason="missing credentials")
        return

    try:
        from langfuse import Langfuse

        Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host,
        )
        logger.info("langfuse.configured", host=host)
    except Exception:
        logger.warning("langfuse.init_failed", exc_info=True)


def flush_langfuse() -> None:
    """Flush pending Langfuse events.  Safe to call even if not configured."""
    try:
        from langfuse import Langfuse

        Langfuse().flush()
    except Exception:
        logger.debug("langfuse.flush_skipped")
