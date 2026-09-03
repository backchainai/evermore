# Copyright (C) 2026 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Structlog configuration with JSON output and OTel trace correlation."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import structlog
from opentelemetry import trace

if TYPE_CHECKING:
    from collections.abc import MutableMapping


def _add_trace_context(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Structlog processor that injects OTel trace context into log events.

    Adds trace_id and span_id when an active span exists. Uses the
    OpenTelemetry API only; no SDK/exporter is required for the fields to
    populate when the ambient tracer is recording.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if ctx.is_valid:
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        event_dict["trace_id"] = trace_id
        event_dict["span_id"] = span_id

    return event_dict


def configure_logging(*, debug: bool = False) -> None:
    """Configure structlog for JSON output (or pretty-printing in debug mode)."""
    log_level = logging.DEBUG if debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_context,
    ]

    if debug:
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # structlog uses PrintLoggerFactory above, not stdlib logging, as its
    # sink. This basicConfig call scopes only to third-party/uvicorn
    # libraries that still log via the stdlib logging module.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
