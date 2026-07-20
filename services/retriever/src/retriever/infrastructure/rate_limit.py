# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Per-user request rate limiting for the RAG ask endpoint (ADR-0012).

Guards ``POST /api/v1/ask`` against denial-of-wallet: a single authenticated,
subscribed token could otherwise drive unbounded paid LLM inference. The
limiter keys on the caller's Supabase user id (``AuthUser.sub``), stashed onto
``request.state.rate_limit_key`` by a route dependency, so the limit tracks
one bucket per user rather than one bucket per process or per remote address.

Per-tenant limiting is a documented forward extension only, not implemented
here: the JWT this service validates carries no tenant claim, so keying on
the constant ``DEFAULT_TENANT_ID`` would collapse every user in the system
into a single global bucket rather than isolating tenants from each other.

Storage is in-memory (``memory://``, slowapi's default) -- per ADR-0012 this
resets on restart and limits are per-instance, which is acceptable for a
single-instance deployment.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import cast

from fastapi import FastAPI, Request
from limits import parse_many
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from retriever.config import get_settings

# Fallback Retry-After (seconds) when slowapi hasn't recorded window state on
# the request (defensive; should not happen once configure_rate_limiting has
# wired the limiter onto the app).
_DEFAULT_RETRY_AFTER_SECONDS = 60

RATE_LIMIT_MESSAGE = (
    "Too many requests. Please wait a moment before asking another question."
)


def rate_limit_key(request: Request) -> str:
    """Resolve the slowapi bucket key for the current request.

    Prefers the per-user identity stashed by
    :func:`retriever.modules.rag.routes._stash_rate_limit_identity` (the
    authenticated user's ``sub``); falls back to the remote address for any
    request that reaches the limiter without that identity attached.
    """
    stashed = getattr(request.state, "rate_limit_key", None)
    if isinstance(stashed, str) and stashed:
        return stashed
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=rate_limit_key, headers_enabled=False)


def _ask_limit_value() -> str:
    """Return the current ``/ask`` limit string, re-read from settings."""
    return get_settings().rate_limit_ask


def _rate_limiting_disabled() -> bool:
    """Return True when rate limiting is disabled via settings."""
    return not get_settings().rate_limit_enabled


# slowapi re-evaluates both callables on every request, so toggling
# RATE_LIMIT_ENABLED or RATE_LIMIT_ASK at runtime (e.g. via env in tests)
# takes effect without re-registering the decorator.
_ask_limit_decorator = limiter.limit(
    _ask_limit_value, exempt_when=_rate_limiting_disabled
)


def ask_rate_limit[F: Callable[..., object]](func: F) -> F:
    """Typed shim around ``limiter.limit`` for the ``/ask`` endpoint.

    slowapi's ``Limiter.limit`` is untyped, which trips mypy --strict's
    ``disallow_untyped_decorators``. Casting the wrapped callable back to
    ``F`` keeps the decorated route's signature visible to type checkers.
    """
    return cast("F", _ask_limit_decorator(func))


def _retry_after_seconds(request: Request) -> int:
    """Compute a Retry-After value (seconds) from slowapi's window state."""
    current = getattr(request.state, "view_rate_limit", None)
    if current is None:
        return _DEFAULT_RETRY_AFTER_SECONDS
    window_stats = limiter.limiter.get_window_stats(current[0], *current[1])
    return max(1, int(1 + window_stats[0] - time.time()))


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render the ADR-0012 429 body for a :class:`RateLimitExceeded` error."""
    retry_after = _retry_after_seconds(request)
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": RATE_LIMIT_MESSAGE,
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


def configure_rate_limiting(app: FastAPI) -> None:
    """Wire the ADR-0012 limiter and its 429 handler onto ``app``.

    Parses the configured ``/ask`` limit up front so an invalid limit string
    fails fast at startup rather than on the first request.
    """
    parse_many(get_settings().rate_limit_ask)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
