"""Unit tests for response parsers."""

from __future__ import annotations

import pytest

from petdata.modules.api.exceptions import APIValidationError
from petdata.modules.api.parser import (
    parse_animal_response,
    parse_volunteer_note_response,
    parse_walk_record_response,
)


class TestParseAnimalResponse:
    """Tests for parse_animal_response."""

    def test_valid_animal_response_returns_models(self):
        """parse_animal_response returns list of Animal models."""
        raw = {
            "records": [
                {
                    "id": "adalo123",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "AKA": "Bud",
                    "Breed": "Labrador",
                    "Weight (lbs)": 70.5,
                    "Birth Date": "2020-01-15",
                    "Intake Date": "2025-01-01",
                }
            ]
        }
        animals = parse_animal_response(raw)
        assert len(animals) == 1
        assert animals[0].id == "A-001"
        assert animals[0].name == "Buddy"
        assert animals[0].adalo_record_id == "adalo123"

    def test_empty_records_list_returns_empty_list(self):
        """parse_animal_response returns empty list for no records."""
        raw = {"records": []}
        animals = parse_animal_response(raw)
        assert animals == []

    def test_missing_records_key_returns_empty_list(self):
        """parse_animal_response returns empty list when records key missing."""
        raw = {}
        animals = parse_animal_response(raw)
        assert animals == []

    def test_records_not_list_raises_validation_error(self):
        """parse_animal_response raises error when records is not a list."""
        raw = {"records": "not_a_list"}
        with pytest.raises(APIValidationError, match="Expected 'records' to be list"):
            parse_animal_response(raw)

    def test_pydantic_validation_error_wrapped(self):
        """parse_animal_response wraps Pydantic ValidationError."""
        raw = {
            "records": [
                {
                    "id": "adalo123",
                    "Animal ID": None,  # None ID will fail (str required)
                    "Name": None,  # None name will fail (str required)
                }
            ]
        }
        with pytest.raises(APIValidationError, match="Failed to validate animal"):
            parse_animal_response(raw)

    def test_partial_data_with_optional_fields(self):
        """parse_animal_response handles partial data with None values."""
        raw = {
            "records": [
                {
                    "id": "adalo123",
                    "Animal ID": "A-002",
                    "Name": "Max",
                    "AKA": None,
                    "Breed": None,
                    "Weight (lbs)": None,
                }
            ]
        }
        animals = parse_animal_response(raw)
        assert len(animals) == 1
        assert animals[0].id == "A-002"
        assert animals[0].aka is None
        assert animals[0].breed is None

    def test_multiple_animals_parsed(self):
        """parse_animal_response handles multiple records."""
        raw = {
            "records": [
                {"id": "adalo1", "Animal ID": "A-001", "Name": "Buddy"},
                {"id": "adalo2", "Animal ID": "A-002", "Name": "Max"},
                {"id": "adalo3", "Animal ID": "A-003", "Name": "Luna"},
            ]
        }
        animals = parse_animal_response(raw)
        assert len(animals) == 3
        assert [a.name for a in animals] == ["Buddy", "Max", "Luna"]


class TestParseVolunteerNoteResponse:
    """Tests for parse_volunteer_note_response."""

    def test_valid_note_response_returns_models(self):
        """parse_volunteer_note_response returns list of VolunteerNote models."""
        raw = {
            "records": [
                {
                    "id": "note123",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris Krough",
                    "Note Date": "2025-01-12T10:00:00",
                    "Note Text": "Good walk today",
                    "Strong on Leash": 4,
                    "Leash Reactivity": 2,
                    "Shy/Fearful": 1,
                    "Jumpy/Mouthy": 3,
                }
            ]
        }
        notes = parse_volunteer_note_response(raw)
        assert len(notes) == 1
        assert notes[0].animal_id == "A-001"
        assert notes[0].volunteer_name == "Chris Krough"
        assert notes[0].rating_strong_on_leash == 4

    def test_empty_records_list_returns_empty_list(self):
        """parse_volunteer_note_response returns empty list for no records."""
        raw = {"records": []}
        notes = parse_volunteer_note_response(raw)
        assert notes == []

    def test_records_not_list_raises_validation_error(self):
        """parse_volunteer_note_response raises error when records not list."""
        raw = {"records": {"not": "a list"}}
        with pytest.raises(APIValidationError, match="Expected 'records' to be list"):
            parse_volunteer_note_response(raw)

    def test_rating_out_of_range_raises_validation_error(self):
        """parse_volunteer_note_response validates rating range (0-5)."""
        raw = {
            "records": [
                {
                    "id": "note123",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Note Date": "2025-01-12T10:00:00",
                    "Strong on Leash": 10,  # Out of range (>5)
                }
            ]
        }
        with pytest.raises(
            APIValidationError, match="Failed to validate volunteer note"
        ):
            parse_volunteer_note_response(raw)

    def test_optional_ratings_can_be_none(self):
        """parse_volunteer_note_response handles None ratings."""
        raw = {
            "records": [
                {
                    "id": "note123",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Note Date": "2025-01-12T10:00:00",
                    "Note Text": "No ratings today",
                    "Strong on Leash": None,
                    "Leash Reactivity": None,
                }
            ]
        }
        notes = parse_volunteer_note_response(raw)
        assert len(notes) == 1
        assert notes[0].rating_strong_on_leash is None
        assert notes[0].rating_leash_reactivity is None

    def test_multiple_notes_parsed(self):
        """parse_volunteer_note_response handles multiple records."""
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
        notes = parse_volunteer_note_response(raw)
        assert len(notes) == 2
        assert notes[0].volunteer_name == "Chris"
        assert notes[1].volunteer_name == "Sam"


class TestParseWalkRecordResponse:
    """Tests for parse_walk_record_response."""

    def test_valid_walk_record_response_returns_models(self):
        """parse_walk_record_response returns list of WalkRecord models."""
        raw = {
            "records": [
                {
                    "id": "walk123",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Out Time": "2025-01-12T10:00:00",
                    "In Time": "2025-01-12T10:30:00",
                }
            ]
        }
        walks = parse_walk_record_response(raw)
        assert len(walks) == 1
        assert walks[0].animal_id == "A-001"
        assert walks[0].volunteer_name == "Chris"

    def test_empty_records_list_returns_empty_list(self):
        """parse_walk_record_response returns empty list for no records."""
        raw = {"records": []}
        walks = parse_walk_record_response(raw)
        assert walks == []

    def test_records_not_list_raises_validation_error(self):
        """parse_walk_record_response raises error when records not list."""
        raw = {"records": 42}
        with pytest.raises(APIValidationError, match="Expected 'records' to be list"):
            parse_walk_record_response(raw)

    def test_optional_fields_can_be_none(self):
        """parse_walk_record_response handles None for optional fields."""
        raw = {
            "records": [
                {
                    "id": "walk123",
                    "Animal ID": "A-001",
                    "Volunteer Name": None,
                    "Out Time": None,
                    "In Time": None,
                }
            ]
        }
        walks = parse_walk_record_response(raw)
        assert len(walks) == 1
        assert walks[0].volunteer_name is None
        assert walks[0].out_time is None

    def test_multiple_walks_parsed(self):
        """parse_walk_record_response handles multiple records."""
        raw = {
            "records": [
                {
                    "id": "walk1",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                },
                {
                    "id": "walk2",
                    "Animal ID": "A-002",
                    "Volunteer Name": "Sam",
                },
                {
                    "id": "walk3",
                    "Animal ID": "A-003",
                    "Volunteer Name": "Alex",
                },
            ]
        }
        walks = parse_walk_record_response(raw)
        assert len(walks) == 3
        assert [w.volunteer_name for w in walks] == ["Chris", "Sam", "Alex"]
