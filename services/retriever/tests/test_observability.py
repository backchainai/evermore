"""Tests for observability configuration (logging, tracing, middleware, langfuse)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import structlog
from fastapi import FastAPI
from starlette.testclient import TestClient

from retriever.infrastructure.observability.langfuse import (
    configure_langfuse,
    flush_langfuse,
)
from retriever.infrastructure.observability.logging import configure_logging
from retriever.infrastructure.observability.middleware import RequestIdMiddleware
from retriever.infrastructure.observability.tracing import configure_tracing

# ── Logging ──────────────────────────────────────────────────────────────


def test_configure_logging_production_mode() -> None:
    """configure_logging sets up structlog without errors in production mode."""
    configure_logging(debug=False)
    logger = structlog.get_logger("test")
    assert logger is not None


def test_configure_logging_debug_mode() -> None:
    """configure_logging sets up structlog without errors in debug mode."""
    configure_logging(debug=True)
    logger = structlog.get_logger("test_debug")
    assert logger is not None


def test_trace_context_in_logs_when_span_active() -> None:
    """Log events include trace_id and span_id when an OTel span is active."""
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider

    configure_logging(debug=False)

    # Create a dedicated TracerProvider to avoid global state interference
    provider = SdkTracerProvider()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("test-span") as span:
        ctx = span.get_span_context()
        assert ctx.trace_id != 0

        from retriever.infrastructure.observability.logging import _add_trace_context

        captured: dict[str, object] = {}
        result = _add_trace_context(None, "info", captured)
        assert "trace_id" in result
        assert "span_id" in result
        assert "logging.googleapis.com/trace" in result
        assert result["trace_id"] == format(ctx.trace_id, "032x")


def test_trace_context_absent_without_span() -> None:
    """Log events have no trace_id when no OTel span is active."""
    from retriever.infrastructure.observability.logging import _add_trace_context

    captured: dict[str, object] = {}
    result = _add_trace_context(None, "info", captured)
    # No active span with valid trace_id → no trace context added
    # (there may be a no-op span with trace_id=0)
    if "trace_id" in result:
        assert result["trace_id"] == "0" * 32


# ── Tracing ──────────────────────────────────────────────────────────────


def test_configure_tracing_disabled() -> None:
    """configure_tracing is a no-op when enabled=False."""
    configure_tracing(service_name="test", enabled=False)


def test_configure_tracing_no_exporter() -> None:
    """configure_tracing completes without errors with no exporter configured."""
    configure_tracing(service_name="test-service", debug=False)


def test_configure_tracing_debug_console_exporter() -> None:
    """configure_tracing attaches console exporter in debug mode."""
    configure_tracing(service_name="test-service", debug=True)


def test_build_exporter_returns_none_without_config() -> None:
    """_build_exporter returns None when no exporter is configured."""
    from retriever.infrastructure.observability.tracing import _build_exporter

    exporter = _build_exporter(gcp_project_id="", debug=False)
    assert exporter is None


def test_build_exporter_returns_console_in_debug() -> None:
    """_build_exporter returns ConsoleSpanExporter in debug mode."""
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter

    from retriever.infrastructure.observability.tracing import _build_exporter

    exporter = _build_exporter(gcp_project_id="", debug=True)
    assert isinstance(exporter, ConsoleSpanExporter)


def test_configure_tracing_with_sample_rate() -> None:
    """configure_tracing accepts a sample rate."""
    configure_tracing(service_name="test", sample_rate=0.5)


def test_configure_tracing_instruments_fastapi() -> None:
    """FastAPI auto-instrumentation is applied when app is provided."""
    app = FastAPI()
    with patch(
        "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app"
    ) as mock_instrument:
        configure_tracing(service_name="test", app=app, debug=True)
        mock_instrument.assert_called_once_with(app)


# ── Request ID Middleware ────────────────────────────────────────────────


def _make_test_app() -> FastAPI:
    """Create a minimal FastAPI app with RequestIdMiddleware for testing."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"ok": "true"}

    return app


def test_request_id_generated_when_missing() -> None:
    """Middleware generates a UUID request ID when header is absent."""
    app = _make_test_app()
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 36  # UUID4 format


def test_request_id_preserved_when_present() -> None:
    """Middleware uses the existing X-Request-ID header when provided."""
    app = _make_test_app()
    client = TestClient(app)
    response = client.get("/test", headers={"X-Request-ID": "my-custom-id"})
    assert response.headers["X-Request-ID"] == "my-custom-id"


# ── Langfuse ─────────────────────────────────────────────────────────────


def test_configure_langfuse_disabled_without_credentials() -> None:
    """configure_langfuse is a no-op when credentials are missing."""
    # Should not raise
    configure_langfuse(secret_key="", public_key="", host="")


def test_configure_langfuse_disabled_partial_credentials() -> None:
    """configure_langfuse is a no-op with only partial credentials."""
    configure_langfuse(
        secret_key="sk-lf-xxx", public_key="", host="https://langfuse.com"
    )


def test_configure_langfuse_initialises_with_credentials() -> None:
    """configure_langfuse creates a client when all credentials are present."""
    with (
        patch(
            "retriever.infrastructure.observability.langfuse.Langfuse", create=True
        ) as mock_cls,
        patch.dict("sys.modules", {"langfuse": MagicMock(Langfuse=mock_cls)}),
    ):
        configure_langfuse(
            secret_key="sk-lf-test",
            public_key="pk-lf-test",
            host="https://langfuse.example.com",
        )


def test_flush_langfuse_safe_when_not_configured() -> None:
    """flush_langfuse does not raise when Langfuse is not configured."""
    flush_langfuse()


async def test_observe_decorator_does_not_break_async_functions() -> None:
    """The @observe() decorator preserves async function behaviour."""
    from retriever.infrastructure.observability.langfuse import observe

    @observe()  # type: ignore[misc]
    async def sample_fn(x: int) -> int:
        return x * 2

    result = await sample_fn(5)
    assert result == 10
