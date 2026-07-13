"""Unit tests for the parser record-count cap (F6 hardening).

An unbounded `records` array in an SMS API response could exhaust memory or
CPU while the parser iterates every record. Each parse function accepts an
optional `max_records` override (defaulting to `Settings.max_records`) and
raises `APIValidationError` when the response declares more records than the
cap allows.
"""

from __future__ import annotations

import pytest

from petdata.modules.api.exceptions import APIValidationError
from petdata.modules.api.parser import (
    parse_animal_response,
    parse_volunteer_note_response,
    parse_walk_record_response,
)


class TestParseAnimalResponseRecordCap:
    """Tests for parse_animal_response's max_records cap."""

    def test_records_over_cap_raises_validation_error(self):
        """A response with more records than max_records is rejected."""
        raw = {
            "records": [
                {"id": "sms1", "Animal ID": "A-001", "Name": "Buddy"},
                {"id": "sms2", "Animal ID": "A-002", "Name": "Max"},
                {"id": "sms3", "Animal ID": "A-003", "Name": "Luna"},
            ]
        }
        with pytest.raises(APIValidationError, match="max_records"):
            parse_animal_response(raw, max_records=2)

    def test_records_at_or_under_cap_parses_normally(self):
        """A response within the cap parses without error."""
        raw = {
            "records": [
                {"id": "sms1", "Animal ID": "A-001", "Name": "Buddy"},
                {"id": "sms2", "Animal ID": "A-002", "Name": "Max"},
            ]
        }
        animals = parse_animal_response(raw, max_records=2)
        assert len(animals) == 2


class TestParseVolunteerNoteResponseRecordCap:
    """Tests for parse_volunteer_note_response's max_records cap."""

    def test_records_over_cap_raises_validation_error(self):
        """A response with more records than max_records is rejected."""
        raw = {
            "records": [
                {
                    "id": "note1",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Note Date": "2025-01-12T10:00:00",
                },
                {
                    "id": "note2",
                    "Animal ID": "A-002",
                    "Volunteer Name": "Sam",
                    "Note Date": "2025-01-12T11:00:00",
                },
                {
                    "id": "note3",
                    "Animal ID": "A-003",
                    "Volunteer Name": "Alex",
                    "Note Date": "2025-01-12T12:00:00",
                },
            ]
        }
        with pytest.raises(APIValidationError, match="max_records"):
            parse_volunteer_note_response(raw, max_records=2)

    def test_records_at_or_under_cap_parses_normally(self):
        """A response within the cap parses without error."""
        raw = {
            "records": [
                {
                    "id": "note1",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Note Date": "2025-01-12T10:00:00",
                },
                {
                    "id": "note2",
                    "Animal ID": "A-002",
                    "Volunteer Name": "Sam",
                    "Note Date": "2025-01-12T11:00:00",
                },
            ]
        }
        notes = parse_volunteer_note_response(raw, max_records=2)
        assert len(notes) == 2


class TestParseWalkRecordResponseRecordCap:
    """Tests for parse_walk_record_response's max_records cap."""

    def test_records_over_cap_raises_validation_error(self):
        """A response with more records than max_records is rejected."""
        raw = {
            "records": [
                {"id": "walk1", "Animal ID": "A-001", "Volunteer Name": "Chris"},
                {"id": "walk2", "Animal ID": "A-002", "Volunteer Name": "Sam"},
                {"id": "walk3", "Animal ID": "A-003", "Volunteer Name": "Alex"},
            ]
        }
        with pytest.raises(APIValidationError, match="max_records"):
            parse_walk_record_response(raw, max_records=2)

    def test_records_at_or_under_cap_parses_normally(self):
        """A response within the cap parses without error."""
        raw = {
            "records": [
                {"id": "walk1", "Animal ID": "A-001", "Volunteer Name": "Chris"},
                {"id": "walk2", "Animal ID": "A-002", "Volunteer Name": "Sam"},
            ]
        }
        walks = parse_walk_record_response(raw, max_records=2)
        assert len(walks) == 2
