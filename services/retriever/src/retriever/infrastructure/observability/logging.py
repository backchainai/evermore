# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Structlog configuration with JSON output and OTel trace correlation."""

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog
from opentelemetry import trace


def _add_trace_context(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Structlog processor that injects OTel trace context into log events.

    Adds trace_id and span_id when an active span exists.
    In GCP environments, also adds the Cloud Logging trace correlation field.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if ctx and ctx.trace_id != 0:
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        event_dict["trace_id"] = trace_id
        event_dict["span_id"] = span_id

        # GCP Cloud Logging correlation field
        event_dict["logging.googleapis.com/trace"] = trace_id

    return event_dict


def configure_logging(*, debug: bool = False) -> None:
    """Configure structlog for JSON output (or pretty-printing in debug mode)."""
    log_level = logging.DEBUG if debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_context,
        structlog.processors.StackInfoRenderer(),
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

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
