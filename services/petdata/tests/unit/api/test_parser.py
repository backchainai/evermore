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
                    "id": "sms123",
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
        assert animals[0].source_record_id == "sms123"

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
                    "id": "sms123",
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
                    "id": "sms123",
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

    def test_species_field_mapped(self):
        """parse_animal_response maps the SMS Species field to species."""
        raw = {
            "records": [
                {
                    "id": "sms123",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "Species": "dog",
                }
            ]
        }
        animals = parse_animal_response(raw)
        assert animals[0].species == "dog"

    def test_species_absent_defaults_to_none(self):
        """parse_animal_response leaves species None when absent."""
        raw = {
            "records": [
                {
                    "id": "sms123",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                }
            ]
        }
        animals = parse_animal_response(raw)
        assert animals[0].species is None

    def test_multiple_animals_parsed(self):
        """parse_animal_response handles multiple records."""
        raw = {
            "records": [
                {"id": "sms1", "Animal ID": "A-001", "Name": "Buddy"},
                {"id": "sms2", "Animal ID": "A-002", "Name": "Max"},
                {"id": "sms3", "Animal ID": "A-003", "Name": "Luna"},
            ]
        }
        animals = parse_animal_response(raw)
        assert len(animals) == 3
        assert [a.name for a in animals] == ["Buddy", "Max", "Luna"]

    def test_every_mapped_field_survives_a_fully_populated_record(self):
        """parse_animal_response maps every SMS field to its Animal field."""
        raw = {
            "records": [
                {
                    "id": "sms123",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "AKA": "Bud",
                    "Breed": "Labrador",
                    "Species": "dog",
                    "Weight (lbs)": 70.5,
                    "Birth Date": "2020-01-15",
                    "Intake Date": "2025-01-01",
                    "Location": "Kennel 12",
                    "Color Category": "Green",
                    "Photo URL": "https://example.com/buddy.jpg",
                    "Public Profile URL": "https://example.com/animals/A-001",
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-02T00:00:00",
                }
            ]
        }
        animal = parse_animal_response(raw)[0]
        assert animal.id == "A-001"
        assert animal.source_record_id == "sms123"
        assert animal.name == "Buddy"
        assert animal.aka == "Bud"
        assert animal.breed == "Labrador"
        assert animal.species == "dog"
        assert animal.weight_lbs == 70.5
        assert animal.birth_date == "2020-01-15"
        assert animal.intake_date == "2025-01-01"
        assert animal.location == "Kennel 12"
        assert animal.color_category == "Green"
        assert animal.photo_url == "https://example.com/buddy.jpg"
        assert animal.public_profile_url == "https://example.com/animals/A-001"
        assert animal.created_at == "2025-01-01T00:00:00"
        assert animal.updated_at == "2025-01-02T00:00:00"

    def test_custody_location_is_kennel_when_in_kennel_flag_set(self):
        """custody_location resolves to 'kennel' when 'In Kennel' is truthy."""
        raw = {
            "records": [
                {
                    "id": "sms1",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "In Kennel": True,
                }
            ]
        }
        assert parse_animal_response(raw)[0].custody_location == "kennel"

    def test_custody_location_is_foster_when_only_foster_flag_set(self):
        """custody_location resolves to 'foster' when only 'Foster Care' is truthy."""
        raw = {
            "records": [
                {
                    "id": "sms1",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "Foster Care": True,
                }
            ]
        }
        assert parse_animal_response(raw)[0].custody_location == "foster"

    def test_custody_location_is_none_when_neither_flag_set(self):
        """custody_location is None when neither SMS flag is truthy."""
        raw = {
            "records": [
                {
                    "id": "sms1",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "In Kennel": False,
                    "Foster Care": False,
                }
            ]
        }
        assert parse_animal_response(raw)[0].custody_location is None

    def test_custody_location_prefers_kennel_when_both_flags_set(self):
        """'In Kennel' takes precedence over 'Foster Care' when both are truthy."""
        raw = {
            "records": [
                {
                    "id": "sms1",
                    "Animal ID": "A-001",
                    "Name": "Buddy",
                    "In Kennel": True,
                    "Foster Care": True,
                }
            ]
        }
        assert parse_animal_response(raw)[0].custody_location == "kennel"


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

    def test_every_mapped_field_survives_a_fully_populated_record(self):
        """parse_volunteer_note_response maps every SMS field to VolunteerNote."""
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
                    "created_at": "2025-01-12T10:05:00",
                }
            ]
        }
        note = parse_volunteer_note_response(raw)[0]
        assert note.source_record_id == "note123"
        assert note.animal_id == "A-001"
        assert note.volunteer_name == "Chris Krough"
        assert note.note_date == "2025-01-12T10:00:00"
        assert note.note_text == "Good walk today"
        assert note.rating_strong_on_leash == 4
        assert note.rating_leash_reactivity == 2
        assert note.rating_shy_fearful == 1
        assert note.rating_jumpy_mouthy == 3
        assert note.created_at == "2025-01-12T10:05:00"


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

    def test_every_mapped_field_survives_a_fully_populated_record(self):
        """parse_walk_record_response maps every SMS field to WalkRecord."""
        raw = {
            "records": [
                {
                    "id": "walk123",
                    "Animal ID": "A-001",
                    "Volunteer Name": "Chris",
                    "Out Time": "2025-01-12T10:00:00",
                    "In Time": "2025-01-12T10:30:00",
                    "created_at": "2025-01-12T10:00:05",
                }
            ]
        }
        walk = parse_walk_record_response(raw)[0]
        assert walk.source_record_id == "walk123"
        assert walk.animal_id == "A-001"
        assert walk.volunteer_name == "Chris"
        assert walk.out_time == "2025-01-12T10:00:00"
        assert walk.in_time == "2025-01-12T10:30:00"
        assert walk.created_at == "2025-01-12T10:00:05"
