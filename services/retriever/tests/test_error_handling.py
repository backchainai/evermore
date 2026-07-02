# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for CORS-safe error handling (issue #97).

An unhandled exception must yield a 500 response that still carries CORS
headers, so browsers surface the error instead of blocking it as a CORS
failure. The 500 must be built inside the CORS layer, not above it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from retriever.config import get_settings
from retriever.main import create_app

# A configured allowed origin (dev default includes http://localhost:5173).
ALLOWED_ORIGIN = get_settings().allowed_origins_list[0]


async def _boom() -> None:
    """Route that always raises, exercising the unhandled-exception path."""
    raise RuntimeError("boom")


async def _stream_then_boom() -> AsyncIterator[bytes]:
    """Yield one chunk, then raise, exercising the mid-stream failure path."""
    yield b"chunk-1"
    raise RuntimeError("boom-mid-stream")


async def _streaming_boom() -> StreamingResponse:
    """Route whose body streams and then raises after the first chunk."""
    return StreamingResponse(_stream_then_boom(), media_type="text/plain")


def _client() -> TestClient:
    """Build the real app wiring, then attach a route that raises.

    The client is not entered as a context manager, so lifespan startup
    (which wires the DB-backed document service) never runs — this test
    exercises middleware wiring only and never touches Postgres.
    """
    app = create_app()
    app.add_api_route("/api/v1/_boom", _boom, methods=["GET"])
    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_exception_returns_500_with_cors_header() -> None:
    """A route that raises returns a 500 that carries the CORS origin header."""
    client = _client()

    resp = client.get("/api/v1/_boom", headers={"Origin": ALLOWED_ORIGIN})

    assert resp.status_code == 500
    assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert resp.json() == {"detail": "Internal server error"}


def test_unhandled_exception_body_is_generic() -> None:
    """The 500 body must not leak internal exception detail."""
    client = _client()

    resp = client.get("/api/v1/_boom", headers={"Origin": ALLOWED_ORIGIN})

    body = resp.json()
    assert body == {"detail": "Internal server error"}
    assert "boom" not in resp.text
    assert "RuntimeError" not in resp.text


def test_streaming_exception_after_body_started_reraises() -> None:
    """A mid-stream exception can't be rewritten into a clean 500.

    Once the first chunk is sent, ``http.response.start`` has already gone
    out, so the middleware can't rewrite the status code without emitting a
    malformed response; it re-raises instead (the exception is already
    logged). This is the deterministic assertion for the streaming path:
    with the client's default ``raise_server_exceptions=True``, that
    re-raise surfaces here rather than as a truncated/hung response, which
    would be flaky to assert on directly.
    """
    app = create_app()
    app.add_api_route("/api/v1/_stream_boom", _streaming_boom, methods=["GET"])
    client = TestClient(app)  # raise_server_exceptions defaults to True

    with pytest.raises(RuntimeError, match="boom-mid-stream"):
        client.get("/api/v1/_stream_boom", headers={"Origin": ALLOWED_ORIGIN})


def test_cors_preflight_still_carries_header() -> None:
    """A handled request (CORS preflight) still carries the CORS header.

    Confirms the fix does not regress the working CORS path for responses
    built by the inner layers.
    """
    client = _client()

    resp = client.options(
        "/api/v1/_boom",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
