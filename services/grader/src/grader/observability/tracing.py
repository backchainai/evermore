# Copyright (C) 2026 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""OpenTelemetry tracing, API only.

grader depends on opentelemetry-api only (no SDK, no exporters, no
opentelemetry-instrumentation-* packages) per the tech-stack standard's
API-only observability rule for this service. Without a host process
installing a real SDK TracerProvider, `tracer` yields no-op spans; the
module still exercises the API surface so structured tracing is a drop-in
addition later without touching call sites.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from opentelemetry import trace

if TYPE_CHECKING:
    from collections.abc import Iterator

    from opentelemetry.trace import Span

tracer = trace.get_tracer(__name__)


@contextmanager
def traced_span(name: str) -> Iterator[Span]:
    """Start a span named `name` on the module tracer.

    Thin wrapper around `tracer.start_as_current_span` so call sites (e.g.
    `main.py` request handlers) exercise OTel instrumentation without each
    importing `opentelemetry.trace` directly.
    """
    with tracer.start_as_current_span(name) as span:
        yield span
