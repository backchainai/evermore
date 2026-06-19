# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""OpenTelemetry tracing configuration.

Supports three exporter backends:
- GCP Cloud Trace (production, when gcp_project_id is set)
- OTLP/gRPC (local dev with Jaeger, when OTEL_EXPORTER_OTLP_ENDPOINT is set)
- Console (debug mode fallback)
"""

from __future__ import annotations

import os

import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.semconv.resource import ResourceAttributes

logger = structlog.get_logger(__name__)


def _build_exporter(
    *, gcp_project_id: str, debug: bool, otlp_endpoint: str = ""
) -> SpanExporter | None:
    """Select the appropriate span exporter based on environment.

    Priority:
    1. GCP Cloud Trace — if gcp_project_id is set
    2. OTLP/gRPC — if OTEL_EXPORTER_OTLP_ENDPOINT env var is set (Jaeger)
    3. Console — if debug is True
    4. None — no exporter (otel still provides no-op spans)
    """
    if gcp_project_id:
        try:
            from opentelemetry.exporter.cloud_trace import (
                CloudTraceSpanExporter,
            )

            logger.info("tracing.exporter.gcp", project_id=gcp_project_id)
            return CloudTraceSpanExporter(project_id=gcp_project_id)  # type: ignore[no-untyped-call]
        except ImportError:
            logger.warning("tracing.exporter.gcp_unavailable")
        except Exception:
            # GCP credentials not available (local dev without ADC)
            logger.warning("tracing.exporter.gcp_auth_failed", exc_info=True)

    resolved_endpoint = otlp_endpoint or os.environ.get(
        "OTEL_EXPORTER_OTLP_ENDPOINT", ""
    )
    if resolved_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            logger.info("tracing.exporter.otlp", endpoint=resolved_endpoint)
            return OTLPSpanExporter(endpoint=resolved_endpoint, insecure=True)
        except ImportError:
            logger.warning("tracing.exporter.otlp_unavailable")

    if debug:
        logger.info("tracing.exporter.console")
        return ConsoleSpanExporter()

    return None


def _build_resource(service_name: str, gcp_project_id: str) -> Resource:
    """Build OTel resource with optional GCP resource detection."""
    base = Resource.create({ResourceAttributes.SERVICE_NAME: service_name})

    if gcp_project_id:
        try:
            from opentelemetry.resourcedetector.gcp_resource_detector import (
                GoogleCloudResourceDetector,
            )

            detected = GoogleCloudResourceDetector().detect()
            return base.merge(detected)
        except ImportError:
            logger.debug("tracing.gcp_resource_detector_unavailable")

    return base


def configure_tracing(
    *,
    service_name: str,
    debug: bool = False,
    gcp_project_id: str = "",
    sample_rate: float = 1.0,
    app: FastAPI | None = None,
    enabled: bool = True,
    otlp_endpoint: str = "",
) -> None:
    """Configure OTel tracing with the appropriate exporter.

    Args:
        service_name: Name for this service in traces.
        debug: Enable debug mode (console exporter fallback).
        gcp_project_id: GCP project ID for Cloud Trace export.
        sample_rate: Fraction of traces to sample (0.0–1.0).
        app: FastAPI app instance for auto-instrumentation.
        enabled: Master switch — when False, tracing is fully disabled.
        otlp_endpoint: OTLP/gRPC endpoint (e.g. http://localhost:4317).
    """
    if not enabled:
        logger.info("tracing.disabled")
        return

    resource = _build_resource(service_name, gcp_project_id)
    sampler = TraceIdRatioBased(sample_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = _build_exporter(
        gcp_project_id=gcp_project_id, debug=debug, otlp_endpoint=otlp_endpoint
    )
    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI if app is provided
    if app is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("tracing.fastapi_instrumented")

    logger.info(
        "tracing.configured",
        service_name=service_name,
        sample_rate=sample_rate,
        has_exporter=exporter is not None,
    )
