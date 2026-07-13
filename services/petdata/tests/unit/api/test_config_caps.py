"""Unit tests for the response/record size cap settings on Settings.

F6 hardening: an SMS extraction endpoint returning an oversized payload (or an
unbounded number of records) should be rejected before it is fully buffered
or iterated. These settings (`max_response_bytes`, `max_records`) are the
config surface for that cap; see `test_client_size_cap.py` and
`test_parser_record_cap.py` for the enforcement paths.
"""

from __future__ import annotations

import pytest

from petdata.config import Settings


class TestMaxResponseBytesValidation:
    """Tests for Settings.max_response_bytes validation."""

    def test_default_value(self):
        """max_response_bytes defaults to 10 MB."""
        settings = Settings()
        assert settings.max_response_bytes == 10_000_000

    def test_zero_raises_value_error(self):
        """max_response_bytes of 0 is rejected."""
        with pytest.raises(ValueError, match="must be at least 1"):
            Settings(max_response_bytes=0)

    def test_negative_raises_value_error(self):
        """A negative max_response_bytes is rejected."""
        with pytest.raises(ValueError, match="must be at least 1"):
            Settings(max_response_bytes=-1)

    def test_positive_value_constructs_fine(self):
        """A valid positive max_response_bytes constructs without error."""
        settings = Settings(max_response_bytes=500)
        assert settings.max_response_bytes == 500


class TestMaxRecordsValidation:
    """Tests for Settings.max_records validation."""

    def test_default_value(self):
        """max_records defaults to 5000."""
        settings = Settings()
        assert settings.max_records == 5000

    def test_zero_raises_value_error(self):
        """max_records of 0 is rejected."""
        with pytest.raises(ValueError, match="must be at least 1"):
            Settings(max_records=0)

    def test_negative_raises_value_error(self):
        """A negative max_records is rejected."""
        with pytest.raises(ValueError, match="must be at least 1"):
            Settings(max_records=-1)

    def test_positive_value_constructs_fine(self):
        """A valid positive max_records constructs without error."""
        settings = Settings(max_records=2)
        assert settings.max_records == 2
