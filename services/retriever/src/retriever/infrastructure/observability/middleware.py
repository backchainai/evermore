# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""HTTP middleware for request tracing and CORS-safe error handling."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger(__name__)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """Convert unhandled exceptions into a 500 JSON response inside the stack.

    Starlette routes a base ``Exception`` handler to ``ServerErrorMiddleware``,
    the outermost layer, above ``CORSMiddleware``. A 500 built there never
    passes back through CORS, so browsers block it as a CORS failure and the
    frontend shows a generic "Load failed" instead of the real status.

    Registered inside the CORS layer, this middleware catches the exception
    and returns the response from within the stack, so CORS headers are added
    on the way out. The body is intentionally generic — no internal detail
    leaks to the client; the exception is logged with a traceback instead.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Return the route response, or a generic 500 if it raises."""
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error("unhandled_exception", exc_info=exc)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


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
