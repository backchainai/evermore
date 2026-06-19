# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Request ID middleware for tracing requests through the system."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


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
