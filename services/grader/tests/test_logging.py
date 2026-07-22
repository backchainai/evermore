"""Tests for structlog JSON configuration (AC5)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog

from grader.observability.logging import configure_logging

if TYPE_CHECKING:
    import pytest


def test_configure_logging_emits_single_parseable_json_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Production mode renders exactly one line of parseable JSON per event."""
    configure_logging(debug=False)
    logger = structlog.get_logger("test_grader_logging")
    logger.info("grader_logging_test_event", foo="bar")

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1

    payload = json.loads(lines[0])
    assert payload["event"] == "grader_logging_test_event"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"
