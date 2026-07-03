"""Tests for observability configuration (logging, tracing, middleware, langfuse)."""

from __future__ import annotations

import json
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import opentelemetry.trace as otel_trace
import pytest
import structlog
from fastapi import FastAPI
from opentelemetry.util._once import Once
from starlette.testclient import TestClient

from retriever.infrastructure.observability.langfuse import (
    configure_langfuse,
    flush_langfuse,
)
from retriever.infrastructure.observability.logging import configure_logging
from retriever.infrastructure.observability.middleware import RequestIdMiddleware
from retriever.infrastructure.observability.tracing import configure_tracing


@pytest.fixture(autouse=True)
def _reset_otel_tracer_provider() -> Generator[None]:
    """Reset OTel's global TracerProvider before and after every test.

    OpenTelemetry's global ``TracerProvider`` is set-once per process: once
    installed, a later ``set_tracer_provider()`` call is silently ignored
    (with a logged warning) instead of overriding it. Several tests below
    call ``configure_tracing()`` and then assert on the *actual* installed
    global provider, so without a reset each test after the first one in
    the process would inherit whatever provider an earlier test installed
    and fail (or pass for the wrong reason). Resetting the private
    ``_TRACER_PROVIDER`` / ``_TRACER_PROVIDER_SET_ONCE`` globals around each
    test makes ``configure_tracing()`` install fresh state every time,
    independent of test order.
    """
    original_provider = otel_trace._TRACER_PROVIDER
    original_once = otel_trace._TRACER_PROVIDER_SET_ONCE
    otel_trace._TRACER_PROVIDER = None
    otel_trace._TRACER_PROVIDER_SET_ONCE = Once()
    try:
        yield
    finally:
        otel_trace._TRACER_PROVIDER = original_provider
        otel_trace._TRACER_PROVIDER_SET_ONCE = original_once


# ── Logging ──────────────────────────────────────────────────────────────


def test_configure_logging_production_mode_emits_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Production mode renders each log line as a single parseable JSON object."""
    configure_logging(debug=False)
    logger = structlog.get_logger("test_prod_json")
    logger.info("observability_prod_test_event", foo="bar")

    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "observability_prod_test_event"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"


def test_configure_logging_debug_mode_emits_console_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Debug mode renders human-readable console output, not JSON."""
    configure_logging(debug=True)
    logger = structlog.get_logger("test_debug_console")
    logger.info("observability_debug_test_event", foo="bar")

    out = capsys.readouterr().out
    assert "observability_debug_test_event" in out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out.strip().splitlines()[-1])


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
    # No active span → the default no-op span (trace_id=0) adds no context.
    assert "trace_id" not in result
    assert "span_id" not in result


# ── Tracing ──────────────────────────────────────────────────────────────


def test_configure_tracing_disabled_leaves_provider_unset() -> None:
    """configure_tracing is a no-op when enabled=False: global provider is untouched."""
    from opentelemetry import trace

    before = trace.get_tracer_provider()
    configure_tracing(service_name="test-disabled", enabled=False)
    assert trace.get_tracer_provider() is before


def test_configure_tracing_no_exporter_installs_provider_without_processor() -> None:
    """With no exporter configured, an SDK provider is installed with zero processors."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider

    configure_tracing(service_name="test-service", debug=False)

    provider = trace.get_tracer_provider()
    assert isinstance(provider, SdkTracerProvider)
    assert provider._active_span_processor._span_processors == ()  # type: ignore[attr-defined]


def test_configure_tracing_debug_console_exporter_adds_batch_processor() -> None:
    """Debug mode wires a BatchSpanProcessor around a ConsoleSpanExporter."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    configure_tracing(service_name="test-service", debug=True)

    provider = trace.get_tracer_provider()
    processors = provider._active_span_processor._span_processors  # type: ignore[attr-defined]
    assert len(processors) == 1
    assert isinstance(processors[0], BatchSpanProcessor)
    assert isinstance(processors[0].span_exporter, ConsoleSpanExporter)


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


def test_configure_tracing_with_sample_rate_threads_rate_to_sampler() -> None:
    """sample_rate is threaded through to the installed TraceIdRatioBased sampler."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

    configure_tracing(service_name="test-sample-rate", sample_rate=0.5)

    provider = trace.get_tracer_provider()
    sampler = provider.sampler  # type: ignore[attr-defined]
    assert isinstance(sampler, TraceIdRatioBased)
    assert sampler._rate == 0.5  # type: ignore[attr-defined]


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


def test_configure_langfuse_disabled_without_credentials_skips_client() -> None:
    """configure_langfuse does not construct a client when credentials are missing."""
    mock_cls = MagicMock()
    with patch.dict("sys.modules", {"langfuse": MagicMock(Langfuse=mock_cls)}):
        configure_langfuse(secret_key="", public_key="", host="")
    mock_cls.assert_not_called()


def test_configure_langfuse_disabled_partial_credentials_skips_client() -> None:
    """configure_langfuse does not construct a client with only partial credentials."""
    mock_cls = MagicMock()
    with patch.dict("sys.modules", {"langfuse": MagicMock(Langfuse=mock_cls)}):
        configure_langfuse(
            secret_key="sk-lf-xxx", public_key="", host="https://langfuse.com"
        )
    mock_cls.assert_not_called()


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
        mock_cls.assert_called_once_with(
            secret_key="sk-lf-test",
            public_key="pk-lf-test",
            host="https://langfuse.example.com",
        )


def test_flush_langfuse_safe_when_not_configured() -> None:
    """flush_langfuse does not raise when Langfuse is not configured."""
    flush_langfuse()


def test_flush_langfuse_swallows_client_errors() -> None:
    """flush_langfuse swallows exceptions raised by a misbehaving Langfuse client."""
    mock_instance = MagicMock()
    mock_instance.flush.side_effect = RuntimeError("boom")
    mock_cls = MagicMock(return_value=mock_instance)
    with patch.dict("sys.modules", {"langfuse": MagicMock(Langfuse=mock_cls)}):
        flush_langfuse()  # must not raise
    mock_instance.flush.assert_called_once()


async def test_observe_decorator_does_not_break_async_functions() -> None:
    """The @observe() decorator preserves async function behaviour."""
    from retriever.infrastructure.observability.langfuse import observe

    @observe()  # type: ignore[misc]
    async def sample_fn(x: int) -> int:
        return x * 2

    result = await sample_fn(5)
    assert result == 10
