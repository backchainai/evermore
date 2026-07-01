"""Unit tests for the Animal Record layer relocated into evermore-schema."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from evermore_schema import (
    Animal,
    AnimalImage,
    AnimalRecord,
    BehaviorProfile,
    StaffAssessment,
    VolunteerNote,
    WalkRecord,
)


class TestAnimalComputedProperties:
    """Smoke tests that the relocated Animal computed properties still behave."""

    def test_age_years(self):
        """age_years derives from birth_date."""
        two_years_ago = (date.today() - timedelta(days=730)).isoformat()
        animal = Animal(id="A-1", name="Buddy", birth_date=two_years_ago)
        assert animal.age_years == 2.0

    def test_age_years_none_without_birth_date(self):
        """age_years is None when birth_date is unset."""
        assert Animal(id="A-1", name="Buddy").age_years is None

    def test_age_years_none_for_future_birth_date(self):
        """A future birth_date yields None."""
        future = (date.today() + timedelta(days=30)).isoformat()
        assert Animal(id="A-1", name="Buddy", birth_date=future).age_years is None

    def test_days_in_custody(self):
        """days_in_custody derives from intake_date."""
        ten_days_ago = (date.today() - timedelta(days=10)).isoformat()
        animal = Animal(id="A-1", name="Buddy", intake_date=ten_days_ago)
        assert animal.days_in_custody == 10

    def test_is_adoptable_true(self):
        """Green/Yellow/Orange color categories are adoptable."""
        assert Animal(id="A-1", name="Buddy", color_category="Green").is_adoptable

    def test_is_adoptable_false(self):
        """Other color categories are not adoptable."""
        animal = Animal(id="A-1", name="Buddy", color_category="Senior")
        assert animal.is_adoptable is False

    def test_is_adoptable_none(self):
        """A missing color category yields None."""
        assert Animal(id="A-1", name="Buddy").is_adoptable is None

    def test_custody_location_accepts_kennel_and_foster(self):
        """custody_location accepts the two allowed literal values."""
        assert (
            Animal(id="A-1", name="Buddy", custody_location="kennel").custody_location
            == "kennel"
        )
        assert (
            Animal(id="A-1", name="Buddy", custody_location="foster").custody_location
            == "foster"
        )

    def test_custody_location_rejects_invalid_value(self):
        """An unknown custody_location raises ValidationError."""
        with pytest.raises(ValidationError):
            Animal(id="A-1", name="Buddy", custody_location="offsite")


class TestBehaviorProfile:
    """Tests for BehaviorProfile field validation and JSON serialization."""

    def test_behavior_mod_tags_parsed_from_json(self):
        """behavior_mod_tags parses a JSON string into a list."""
        profile = BehaviorProfile(animal_id="A-1", behavior_mod_tags='["shy", "leash"]')
        assert profile.behavior_mod_tags == ["shy", "leash"]

    def test_behavior_mod_tags_serialized_to_json(self):
        """behavior_mod_tags serializes back to a JSON string in json mode."""
        profile = BehaviorProfile(animal_id="A-1", behavior_mod_tags=["shy"])
        dumped = profile.model_dump(mode="json")
        assert dumped["behavior_mod_tags"] == '["shy"]'

    def test_commands_and_housebreaking_booleans_with_notes(self):
        """knows_commands/housebroken booleans carry companion notes."""
        profile = BehaviorProfile(
            animal_id="A-1",
            knows_commands=True,
            commands_notes="sit, stay, down",
            housebroken=False,
            housebreaking_notes="in progress",
        )
        assert profile.knows_commands is True
        assert profile.commands_notes == "sit, stay, down"
        assert profile.housebroken is False
        assert profile.housebreaking_notes == "in progress"


class TestAnimalRecord:
    """Tests for the composite AnimalRecord."""

    def test_defaults(self):
        """AnimalRecord aggregates an animal with empty evidence defaults."""
        record = AnimalRecord(animal=Animal(id="A-1", name="Buddy"))
        assert record.animal.name == "Buddy"
        assert record.behavior_profile is None
        assert record.volunteer_notes == []
        assert record.staff_assessments == []
        assert record.walk_records == []
        assert record.images == []

    def test_default_lists_are_independent(self):
        """Two AnimalRecords do not share mutable default lists."""
        a = AnimalRecord(animal=Animal(id="A-1", name="A"))
        b = AnimalRecord(animal=Animal(id="A-2", name="B"))
        a.volunteer_notes.append(VolunteerNote(animal_id="A-1", volunteer_name="v"))
        assert b.volunteer_notes == []

    def test_full_composition(self):
        """AnimalRecord holds all related evidence types."""
        record = AnimalRecord(
            animal=Animal(id="A-1", name="Buddy"),
            behavior_profile=BehaviorProfile(
                animal_id="A-1",
                dogs_compatible=True,
                things_likes=["walks", "treats"],
                things_dislikes=["baths"],
            ),
            volunteer_notes=[VolunteerNote(animal_id="A-1", volunteer_name="v")],
            staff_assessments=[StaffAssessment(animal_id="A-1")],
            walk_records=[WalkRecord(animal_id="A-1")],
            images=[AnimalImage(animal_id="A-1", image_url="http://x/y.jpg")],
        )
        assert record.behavior_profile is not None
        assert record.behavior_profile.dogs_compatible is True
        assert record.behavior_profile.things_likes == ["walks", "treats"]
        assert len(record.volunteer_notes) == 1
        assert len(record.staff_assessments) == 1
        assert len(record.walk_records) == 1
        assert record.images[0].image_url == "http://x/y.jpg"
