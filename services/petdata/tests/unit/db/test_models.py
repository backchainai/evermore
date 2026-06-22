"""Unit tests for database models."""

from __future__ import annotations

from datetime import datetime

import pytest

from petdata.modules.db.models import (
    Animal,
    AnimalImage,
    KennelCard,
    StaffAssessment,
    SyncLog,
    VolunteerNote,
    WalkRecord,
)


class TestAnimal:
    """Tests for Animal model."""

    def test_create_animal_minimal(self):
        """Animal can be created with minimal required fields."""
        animal = Animal(id="A-00000", name="Buddy")
        assert animal.id == "A-00000"
        assert animal.name == "Buddy"
        assert animal.breed is None

    def test_create_animal_full(self):
        """Animal can be created with all fields."""
        animal = Animal(
            id="A-00000",
            name="Buddy",
            aka="Bud",
            breed="Labrador",
            weight_lbs=65.5,
            birth_date="2022-01-15",
            intake_date="2024-06-01",
            location="Line 3, 3A",
            color_category="Green",
            behavior_mod_tags=["Shy"],
            is_in_kennel=True,
            is_foster_care=False,
            photo_url="https://example.com/photo.jpg",
            public_profile_url="https://example.org/pet/buddy/",
            source_record_id="abc123",
        )
        assert animal.weight_lbs == 65.5
        assert animal.is_in_kennel is True
        assert animal.color_category == "Green"

    def test_model_dump_excludes_none(self):
        """model_dump excludes None values when exclude_none=True."""
        animal = Animal(id="A-00000", name="Buddy")
        data = animal.model_dump(mode="json", exclude_none=True)
        assert "aka" not in data  # None field excluded
        assert "name" in data  # Non-None field included
        assert data["name"] == "Buddy"

    def test_model_dump_includes_none(self):
        """model_dump includes None values when exclude_none=False."""
        animal = Animal(id="A-00000", name="Buddy")
        data = animal.model_dump(mode="json", exclude_none=False)
        assert "aka" in data  # None field included
        assert data["aka"] is None

    def test_sqlite_bool_conversion_from_dict(self):
        """model_validate(dict) correctly converts SQLite bools."""
        row_dict = {
            "id": "A-00000",
            "name": "Buddy",
            "aka": None,
            "breed": "Labrador",
            "weight_lbs": 65.5,
            "birth_date": "2022-01-15",
            "intake_date": "2024-06-01",
            "location": "Line 3",
            "color_category": "Green",
            "behavior_mod_tags": None,
            "is_in_kennel": 1,  # SQLite stores as int
            "is_foster_care": 0,
            "photo_url": None,
            "public_profile_url": None,
            "source_record_id": "abc123",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
            "last_synced_at": None,
        }

        animal = Animal.model_validate(row_dict)
        assert animal.id == "A-00000"
        assert animal.name == "Buddy"
        assert animal.is_in_kennel is True  # Converted from 1
        assert animal.is_foster_care is False  # Converted from 0

    def test_sqlite_bool_none_preserved(self):
        """None values in boolean fields are preserved."""
        animal = Animal.model_validate(
            {
                "id": "TEST-1",
                "name": "Test",
                "is_in_kennel": None,
                "is_foster_care": None,
            }
        )
        assert animal.is_in_kennel is None
        assert animal.is_foster_care is None

    def test_sqlite_bool_direct_bool_passthrough(self):
        """Direct boolean values pass through unchanged."""
        animal = Animal(
            id="TEST-1", name="Test", is_in_kennel=True, is_foster_care=False
        )
        assert animal.is_in_kennel is True
        assert animal.is_foster_care is False

    def test_animal_behavior_tags_from_json_string(self):
        """Validator parses JSON string from database."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags='["Shy"]')
        assert animal.behavior_mod_tags == ["Shy"]

    def test_animal_behavior_tags_from_list(self):
        """Direct list instantiation works."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags=["Shy"])
        assert animal.behavior_mod_tags == ["Shy"]

    def test_animal_behavior_tags_none(self):
        """None values handled gracefully."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags=None)
        assert animal.behavior_mod_tags is None

    def test_animal_behavior_tags_empty_string(self):
        """Empty strings become None."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags="")
        assert animal.behavior_mod_tags is None

    def test_animal_behavior_tags_empty_array(self):
        """Empty arrays are preserved."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags="[]")
        assert animal.behavior_mod_tags == []

    def test_animal_behavior_tags_invalid_json(self):
        """Invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            Animal(id="TEST-1", name="Test", behavior_mod_tags="[invalid")

    def test_animal_behavior_tags_non_array_json(self):
        """Non-array JSON raises ValueError."""
        with pytest.raises(ValueError, match="Expected JSON array"):
            Animal(id="TEST-1", name="Test", behavior_mod_tags='"string"')

    def test_animal_model_dump_serializes_tags(self):
        """model_dump(mode='json') serializes back to JSON string."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags=["Shy", "Reactive"])
        data = animal.model_dump(mode="json", exclude_none=True)
        assert data["behavior_mod_tags"] == '["Shy", "Reactive"]'

    def test_animal_behavior_tags_coerces_to_strings(self):
        """Validator coerces non-string values to strings."""
        animal = Animal(id="TEST-1", name="Test", behavior_mod_tags="[1, true, null]")
        assert animal.behavior_mod_tags == ["1", "True", "None"]

    def test_animal_behavior_tags_size_limit(self):
        """Validator rejects JSON exceeding 10KB."""
        large_json = '["' + "x" * 10001 + '"]'
        with pytest.raises(ValueError, match="exceeds maximum size"):
            Animal(id="TEST-1", name="Test", behavior_mod_tags=large_json)

    def test_age_years_with_birth_date(self):
        """age_years computed property calculates age from birth_date."""
        animal = Animal(id="TEST-1", name="Test", birth_date="2020-01-15")
        age = animal.age_years
        assert age is not None
        assert age > 0  # Should be several years old
        assert isinstance(age, float)

    def test_age_years_without_birth_date(self):
        """age_years returns None when birth_date is not set."""
        animal = Animal(id="TEST-1", name="Test")
        assert animal.age_years is None

    def test_age_years_with_invalid_date(self):
        """age_years returns None for invalid date format."""
        animal = Animal(id="TEST-1", name="Test", birth_date="invalid-date")
        assert animal.age_years is None

    def test_age_years_with_future_date(self):
        """age_years returns None for future birth dates."""
        future_date = "2030-01-01"
        animal = Animal(id="TEST-1", name="Test", birth_date=future_date)
        assert animal.age_years is None

    def test_days_in_shelter_with_intake_date(self):
        """days_in_shelter computed property calculates days from intake."""
        animal = Animal(id="TEST-1", name="Test", intake_date="2024-01-01")
        days = animal.days_in_shelter
        assert days is not None
        assert days >= 0  # Should be some days
        assert isinstance(days, int)

    def test_days_in_shelter_without_intake_date(self):
        """days_in_shelter returns None when intake_date is not set."""
        animal = Animal(id="TEST-1", name="Test")
        assert animal.days_in_shelter is None

    def test_days_in_shelter_with_invalid_date(self):
        """days_in_shelter returns None for invalid date format."""
        animal = Animal(id="TEST-1", name="Test", intake_date="not-a-date")
        assert animal.days_in_shelter is None

    def test_days_in_shelter_with_future_date(self):
        """days_in_shelter returns None for future intake dates."""
        future_date = "2030-06-15"
        animal = Animal(id="TEST-1", name="Test", intake_date=future_date)
        assert animal.days_in_shelter is None

    def test_is_adoptable_green_category(self):
        """is_adoptable returns True for Green category."""
        animal = Animal(id="TEST-1", name="Test", color_category="Green")
        assert animal.is_adoptable is True

    def test_is_adoptable_yellow_category(self):
        """is_adoptable returns True for Yellow category."""
        animal = Animal(id="TEST-1", name="Test", color_category="Yellow")
        assert animal.is_adoptable is True

    def test_is_adoptable_orange_category(self):
        """is_adoptable returns True for Orange category."""
        animal = Animal(id="TEST-1", name="Test", color_category="Orange")
        assert animal.is_adoptable is True

    def test_is_adoptable_senior_category(self):
        """is_adoptable returns False for Senior category."""
        animal = Animal(id="TEST-1", name="Test", color_category="Senior")
        assert animal.is_adoptable is False

    def test_is_adoptable_designated_category(self):
        """is_adoptable returns False for Designated category."""
        animal = Animal(id="TEST-1", name="Test", color_category="Designated")
        assert animal.is_adoptable is False

    def test_is_adoptable_without_category(self):
        """is_adoptable returns None when color_category is not set."""
        animal = Animal(id="TEST-1", name="Test")
        assert animal.is_adoptable is None

    def test_is_adoptable_case_insensitive(self):
        """is_adoptable handles case variations in color_category."""
        # Lowercase
        animal_lower = Animal(id="TEST-1", name="Test", color_category="green")
        assert animal_lower.is_adoptable is True

        # Uppercase
        animal_upper = Animal(id="TEST-2", name="Test", color_category="YELLOW")
        assert animal_upper.is_adoptable is True

        # Mixed case
        animal_mixed = Animal(id="TEST-3", name="Test", color_category="OrAnGe")
        assert animal_mixed.is_adoptable is True

        # Non-adoptable with different case
        animal_senior = Animal(id="TEST-4", name="Test", color_category="SENIOR")
        assert animal_senior.is_adoptable is False

    def test_is_adoptable_unknown_category(self):
        """is_adoptable returns False for unknown categories."""
        animal = Animal(id="TEST-1", name="Test", color_category="Purple")
        assert animal.is_adoptable is False


class TestVolunteerNote:
    """Tests for VolunteerNote model."""

    def test_create_note_with_ratings(self):
        """VolunteerNote can store all rating categories."""
        note = VolunteerNote(
            animal_id="A-00000",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
            note_text="Great walk today!",
            rating_strong_on_leash=4,
            rating_leash_reactivity=2,
            rating_shy_fearful=1,
            rating_jumpy_mouthy=3,
        )
        assert note.rating_strong_on_leash == 4
        assert note.rating_leash_reactivity == 2
        assert note.rating_shy_fearful == 1
        assert note.rating_jumpy_mouthy == 3

    def test_model_dump_excludes_id(self):
        """model_dump can exclude id field."""
        note = VolunteerNote(
            animal_id="A-00000",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        data = note.model_dump(mode="json", exclude={"id"})
        assert "id" not in data
        assert "animal_id" in data

    def test_model_dump_includes_id_when_present(self):
        """model_dump includes id when set (if not excluded)."""
        note = VolunteerNote(
            id=42,
            animal_id="A-00000",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        data = note.model_dump(mode="json", exclude_none=True)
        assert data["id"] == 42


class TestKennelCard:
    """Tests for KennelCard model."""

    def test_create_kennel_card(self):
        """KennelCard stores compatibility info."""
        card = KennelCard(
            animal_id="A-00000",
            about_text="Friendly and playful dog",
            dogs_compatibility="Good",
            dogs_compatibility_notes="Gets along with most dogs",
            cats_compatibility="Unknown",
            kids_compatibility="Good",
            kids_compatibility_notes="Great with kids over 8",
        )
        assert card.dogs_compatibility == "Good"
        assert card.cats_compatibility == "Unknown"


class TestStaffAssessment:
    """Tests for StaffAssessment model."""

    def test_create_assessment(self):
        """StaffAssessment stores tags as list[str]."""
        assessment = StaffAssessment(
            animal_id="A-00000",
            assessment_tags=["Cat Test Complete", "Good with Dogs"],
            notes="Passed all tests",
            recorded_at="2024-12-01T10:00:00",
        )
        assert "Cat Test Complete" in assessment.assessment_tags

    def test_assessment_tags_from_json_string(self):
        """Validator parses JSON string from database."""
        assessment = StaffAssessment(
            animal_id="TEST-1", assessment_tags='["Cat Test Complete"]'
        )
        assert assessment.assessment_tags == ["Cat Test Complete"]

    def test_assessment_tags_from_list(self):
        """Direct list instantiation works."""
        assessment = StaffAssessment(
            animal_id="TEST-1", assessment_tags=["Cat Test Complete"]
        )
        assert assessment.assessment_tags == ["Cat Test Complete"]

    def test_assessment_tags_none(self):
        """None values handled gracefully."""
        assessment = StaffAssessment(animal_id="TEST-1", assessment_tags=None)
        assert assessment.assessment_tags is None

    def test_assessment_tags_empty_string(self):
        """Empty strings become None."""
        assessment = StaffAssessment(animal_id="TEST-1", assessment_tags="")
        assert assessment.assessment_tags is None

    def test_assessment_tags_empty_array(self):
        """Empty arrays are preserved."""
        assessment = StaffAssessment(animal_id="TEST-1", assessment_tags="[]")
        assert assessment.assessment_tags == []

    def test_assessment_tags_invalid_json(self):
        """Invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            StaffAssessment(animal_id="TEST-1", assessment_tags="[invalid")

    def test_assessment_tags_non_array_json(self):
        """Non-array JSON raises ValueError."""
        with pytest.raises(ValueError, match="Expected JSON array"):
            StaffAssessment(animal_id="TEST-1", assessment_tags='"string"')

    def test_assessment_model_dump_serializes_tags(self):
        """model_dump(mode='json') serializes back to JSON string."""
        assessment = StaffAssessment(
            animal_id="TEST-1",
            assessment_tags=["Cat Test Complete", "Good with Dogs"],
        )
        data = assessment.model_dump(mode="json", exclude_none=True)
        assert data["assessment_tags"] == '["Cat Test Complete", "Good with Dogs"]'

    def test_assessment_tags_coerces_to_strings(self):
        """Validator coerces non-string values to strings."""
        assessment = StaffAssessment(
            animal_id="TEST-1", assessment_tags="[1, true, null]"
        )
        assert assessment.assessment_tags == ["1", "True", "None"]

    def test_assessment_tags_size_limit(self):
        """Validator rejects JSON exceeding 10KB."""
        large_json = '["' + "x" * 10001 + '"]'
        with pytest.raises(ValueError, match="exceeds maximum size"):
            StaffAssessment(animal_id="TEST-1", assessment_tags=large_json)


class TestWalkRecord:
    """Tests for WalkRecord model."""

    def test_create_walk_record(self):
        """WalkRecord tracks check-in/out times."""
        record = WalkRecord(
            animal_id="A-00000",
            volunteer_name="Chris",
            out_time="2024-12-23T14:00:00",
            in_time="2024-12-23T14:45:00",
        )
        assert record.out_time == "2024-12-23T14:00:00"
        assert record.in_time == "2024-12-23T14:45:00"


class TestAnimalImage:
    """Tests for AnimalImage model."""

    def test_create_image(self):
        """AnimalImage stores URL and order."""
        image = AnimalImage(
            animal_id="A-00000",
            image_url="https://example.com/photo1.jpg",
            display_order=1,
        )
        assert image.display_order == 1


class TestSyncLog:
    """Tests for SyncLog model."""

    def test_create_sync_log(self):
        """SyncLog tracks sync operations."""
        log = SyncLog(
            sync_type="full",
            table_name="animals",
            started_at=datetime.now().isoformat(),
            status="running",
        )
        assert log.sync_type == "full"
        assert log.status == "running"
        assert log.records_processed == 0

    def test_sync_log_defaults(self):
        """SyncLog has sensible defaults."""
        log = SyncLog(
            sync_type="incremental",
            table_name="volunteer_notes",
            started_at=datetime.now().isoformat(),
        )
        assert log.records_created == 0
        assert log.records_updated == 0
        assert log.status == "running"

    def test_sync_log_none_to_zero_conversion(self):
        """None values in count fields convert to 0."""
        log = SyncLog.model_validate(
            {
                "id": 1,
                "sync_type": "full",
                "table_name": "animals",
                "started_at": "2024-01-15T10:00:00",
                "records_processed": None,
                "records_created": None,
                "records_updated": None,
                "status": "running",
            }
        )
        assert log.records_processed == 0
        assert log.records_created == 0
        assert log.records_updated == 0

    def test_sync_log_zero_preserved(self):
        """Explicit zero values are preserved."""
        log = SyncLog.model_validate(
            {
                "sync_type": "full",
                "table_name": "animals",
                "started_at": "2024-01-15T10:00:00",
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0,
                "status": "running",
            }
        )
        assert log.records_processed == 0
        assert log.records_created == 0
        assert log.records_updated == 0
