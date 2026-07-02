# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""HTTP middleware for request tracing and CORS-safe error handling."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger(__name__)


class ExceptionHandlingMiddleware:
    """Convert unhandled exceptions into a 500 JSON response inside the stack.

    Starlette routes a base ``Exception`` handler to ``ServerErrorMiddleware``,
    the outermost layer, above ``CORSMiddleware``. A 500 built there never
    passes back through CORS, so browsers block it as a CORS failure and the
    frontend shows a generic "Load failed" instead of the real status.

    Registered inside the CORS layer, this middleware catches the exception
    and returns the response from within the stack, so CORS headers are added
    on the way out. The body is intentionally generic — no internal detail
    leaks to the client; the exception is logged with a traceback instead.

    Implemented as a pure ASGI middleware (not ``BaseHTTPMiddleware``) so it
    also covers responses whose body streams the exception mid-flight.
    ``BaseHTTPMiddleware`` buffers the downstream response via an internal
    task and can't catch an exception raised after the first chunk of a
    ``StreamingResponse`` has already been handed to the client. This
    middleware instead watches the raw ASGI ``send`` stream: if the
    exception happens before ``http.response.start`` goes out, it builds a
    clean 500 as before. If the response has already started streaming, the
    exception is logged and re-raised instead, since headers (and possibly
    body bytes) are already on the wire and the status can't be rewritten.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass non-HTTP scopes through untouched; guard HTTP scopes."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            logger.error("unhandled_exception", exc_info=exc)
            if response_started:
                # Headers (and possibly body bytes) have already been sent
                # to the client, so the status code can't be rewritten to
                # 500 and a well-formed JSON error can't be emitted without
                # corrupting the response. Re-raise so the server aborts
                # the connection; the exception is already logged above.
                raise
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
            await response(scope, receive, send)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to every incoming request.

    Checks for an existing ``X-Request-ID`` header and generates a UUID4 if
    missing.  Binds the ID to structlog context vars so every log line within
    the request includes it, and echoes it back as a response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with request ID tracking."""
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
