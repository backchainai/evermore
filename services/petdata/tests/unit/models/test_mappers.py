"""Unit tests for the Pydantic <-> ORM mappers."""

from __future__ import annotations

import datetime

from petdata.models import mappers
from petdata.modules.db import models as pyd


def test_animal_round_trip_preserves_fields() -> None:
    model = pyd.Animal(
        id="A-00000",
        name="Buddy",
        aka="Bud",
        breed="Labrador",
        species="dog",
        weight_lbs=70.0,
        birth_date="2020-01-15",
        intake_date="2024-03-01",
        location="Kennel 12",
        color_category="Green",
        custody_location="kennel",
        photo_url="https://example.com/buddy.jpg",
        public_profile_url="https://example.com/animals/A-00000",
        source_record_id="sms-1",
        created_at="2026-06-01T12:00:00+00:00",
        updated_at="2026-06-01T13:00:00+00:00",
        last_synced_at="2026-06-02T08:30:00+00:00",
    )

    row = mappers.animal_to_row(model)
    assert row.id == "A-00000"
    assert row.name == "Buddy"
    assert row.aka == "Bud"
    assert row.breed == "Labrador"
    assert row.species == "dog"
    assert row.weight_lbs == 70.0
    assert row.birth_date == datetime.date(2020, 1, 15)
    assert row.intake_date == datetime.date(2024, 3, 1)
    assert row.location == "Kennel 12"
    assert row.color_category == "Green"
    assert row.custody_location == "kennel"
    assert row.photo_url == "https://example.com/buddy.jpg"
    assert row.public_profile_url == "https://example.com/animals/A-00000"
    assert row.source_record_id == "sms-1"
    assert row.created_at == datetime.datetime(2026, 6, 1, 12, 0, tzinfo=datetime.UTC)
    assert row.updated_at == datetime.datetime(2026, 6, 1, 13, 0, tzinfo=datetime.UTC)
    assert row.last_synced_at == datetime.datetime(
        2026, 6, 2, 8, 30, tzinfo=datetime.UTC
    )

    back = mappers.animal_from_row(row)
    assert back.id == "A-00000"
    assert back.name == "Buddy"
    assert back.aka == "Bud"
    assert back.breed == "Labrador"
    assert back.species == "dog"
    assert back.weight_lbs == 70.0
    assert back.birth_date == "2020-01-15"
    assert back.intake_date == "2024-03-01"
    assert back.location == "Kennel 12"
    assert back.color_category == "Green"
    assert back.custody_location == "kennel"
    assert back.photo_url == "https://example.com/buddy.jpg"
    assert back.public_profile_url == "https://example.com/animals/A-00000"
    assert back.source_record_id == "sms-1"
    assert back.created_at == "2026-06-01T12:00:00+00:00"
    assert back.updated_at == "2026-06-01T13:00:00+00:00"
    assert back.last_synced_at == "2026-06-02T08:30:00+00:00"


def test_animal_to_row_leaves_server_default_timestamps_unset() -> None:
    model = pyd.Animal(id="A-1", name="Rex")
    row = mappers.animal_to_row(model)
    # No created_at/updated_at supplied; columns fall through to server defaults.
    assert row.created_at is None
    assert row.updated_at is None


def test_birth_date_accepts_datetime_string() -> None:
    model = pyd.Animal(id="A-2", name="Mia", birth_date="2019-07-04T00:00:00")
    row = mappers.animal_to_row(model)
    assert row.birth_date == datetime.date(2019, 7, 4)


def test_behavior_profile_round_trip_preserves_fields() -> None:
    model = pyd.BehaviorProfile(
        id=7,
        animal_id="A-00000",
        dogs_compatible=True,
        dogs_compatibility_notes="Good with dogs",
        cats_compatible=False,
        cats_compatibility_notes="Chases cats",
        kids_compatible=True,
        kids_compatibility_notes="Gentle with kids",
        knows_commands=True,
        commands_notes="sit, stay",
        housebroken=False,
        housebreaking_notes="in progress",
        behavior_mod_tags=["leash", "shy"],
        things_likes=["walks"],
        things_dislikes=["baths"],
        last_synced_at="2026-06-02T08:30:00+00:00",
    )

    row = mappers.behavior_profile_to_row(model)
    assert row.id == 7
    assert row.animal_id == "A-00000"
    assert row.dogs_compatible is True
    assert row.dogs_compatibility_notes == "Good with dogs"
    assert row.cats_compatible is False
    assert row.cats_compatibility_notes == "Chases cats"
    assert row.kids_compatible is True
    assert row.kids_compatibility_notes == "Gentle with kids"
    assert row.knows_commands is True
    assert row.commands_notes == "sit, stay"
    assert row.housebroken is False
    assert row.housebreaking_notes == "in progress"
    assert row.behavior_mod_tags == ["leash", "shy"]
    assert row.things_likes == ["walks"]
    assert row.things_dislikes == ["baths"]
    assert row.last_synced_at == datetime.datetime(
        2026, 6, 2, 8, 30, tzinfo=datetime.UTC
    )

    back = mappers.behavior_profile_from_row(row)
    assert back.id == 7
    assert back.animal_id == "A-00000"
    assert back.dogs_compatible is True
    assert back.dogs_compatibility_notes == "Good with dogs"
    assert back.cats_compatible is False
    assert back.cats_compatibility_notes == "Chases cats"
    assert back.kids_compatible is True
    assert back.kids_compatibility_notes == "Gentle with kids"
    assert back.knows_commands is True
    assert back.commands_notes == "sit, stay"
    assert back.housebroken is False
    assert back.housebreaking_notes == "in progress"
    assert back.behavior_mod_tags == ["leash", "shy"]
    assert back.things_likes == ["walks"]
    assert back.things_dislikes == ["baths"]
    assert back.last_synced_at == "2026-06-02T08:30:00+00:00"


def test_volunteer_note_round_trip() -> None:
    model = pyd.VolunteerNote(
        id=12,
        animal_id="A-00000",
        source_record_id="note-abc",
        volunteer_name="Pat",
        note_date="2026-06-10T09:00:00+00:00",
        note_text="Walked well",
        rating_strong_on_leash=4,
        rating_leash_reactivity=1,
        rating_shy_fearful=0,
        rating_jumpy_mouthy=2,
        created_at="2026-06-10T09:05:00+00:00",
        last_synced_at="2026-06-10T09:10:00+00:00",
    )

    row = mappers.volunteer_note_to_row(model)
    assert row.id == 12
    assert row.animal_id == "A-00000"
    assert row.source_record_id == "note-abc"
    assert row.volunteer_name == "Pat"
    assert row.note_date == datetime.datetime(2026, 6, 10, 9, 0, tzinfo=datetime.UTC)
    assert row.note_text == "Walked well"
    assert row.rating_strong_on_leash == 4
    assert row.rating_leash_reactivity == 1
    assert row.rating_shy_fearful == 0
    assert row.rating_jumpy_mouthy == 2
    assert row.created_at == datetime.datetime(2026, 6, 10, 9, 5, tzinfo=datetime.UTC)
    assert row.last_synced_at == datetime.datetime(
        2026, 6, 10, 9, 10, tzinfo=datetime.UTC
    )

    back = mappers.volunteer_note_from_row(row)
    assert back.id == 12
    assert back.animal_id == "A-00000"
    assert back.source_record_id == "note-abc"
    assert back.volunteer_name == "Pat"
    assert back.note_date == "2026-06-10T09:00:00+00:00"
    assert back.note_text == "Walked well"
    assert back.rating_strong_on_leash == 4
    assert back.rating_leash_reactivity == 1
    assert back.rating_shy_fearful == 0
    assert back.rating_jumpy_mouthy == 2
    assert back.created_at == "2026-06-10T09:05:00+00:00"
    assert back.last_synced_at == "2026-06-10T09:10:00+00:00"


def test_staff_assessment_round_trip_tags() -> None:
    model = pyd.StaffAssessment(
        id=3,
        animal_id="A-1",
        assessment_tags=["food-motivated", "crate-trained"],
        notes="Solid",
        recorded_at="2026-06-09T10:00:00+00:00",
        last_synced_at="2026-06-09T10:05:00+00:00",
    )
    row = mappers.staff_assessment_to_row(model)
    assert row.id == 3
    assert row.animal_id == "A-1"
    assert row.assessment_tags == ["food-motivated", "crate-trained"]
    assert row.notes == "Solid"
    assert row.recorded_at == datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    assert row.last_synced_at == datetime.datetime(
        2026, 6, 9, 10, 5, tzinfo=datetime.UTC
    )

    back = mappers.staff_assessment_from_row(row)
    assert back.id == 3
    assert back.animal_id == "A-1"
    assert back.assessment_tags == ["food-motivated", "crate-trained"]
    assert back.notes == "Solid"
    assert back.recorded_at == "2026-06-09T10:00:00+00:00"
    assert back.last_synced_at == "2026-06-09T10:05:00+00:00"


def test_walk_record_round_trip_preserves_fields() -> None:
    model = pyd.WalkRecord(
        id=21,
        animal_id="A-00000",
        source_record_id="walk-abc",
        volunteer_name="Sam",
        out_time="2026-06-11T09:00:00+00:00",
        in_time="2026-06-11T09:30:00+00:00",
        created_at="2026-06-11T09:31:00+00:00",
    )

    row = mappers.walk_record_to_row(model)
    assert row.id == 21
    assert row.animal_id == "A-00000"
    assert row.source_record_id == "walk-abc"
    assert row.volunteer_name == "Sam"
    assert row.out_time == datetime.datetime(2026, 6, 11, 9, 0, tzinfo=datetime.UTC)
    assert row.in_time == datetime.datetime(2026, 6, 11, 9, 30, tzinfo=datetime.UTC)
    assert row.created_at == datetime.datetime(2026, 6, 11, 9, 31, tzinfo=datetime.UTC)

    back = mappers.walk_record_from_row(row)
    assert back.id == 21
    assert back.animal_id == "A-00000"
    assert back.source_record_id == "walk-abc"
    assert back.volunteer_name == "Sam"
    assert back.out_time == "2026-06-11T09:00:00+00:00"
    assert back.in_time == "2026-06-11T09:30:00+00:00"
    assert back.created_at == "2026-06-11T09:31:00+00:00"


def test_walk_record_to_row_leaves_created_at_unset_when_not_supplied() -> None:
    model = pyd.WalkRecord(animal_id="A-1", source_record_id="walk-1")
    row = mappers.walk_record_to_row(model)
    assert row.created_at is None


def test_animal_image_round_trip_preserves_fields() -> None:
    model = pyd.AnimalImage(
        id=5,
        animal_id="A-00000",
        image_url="https://example.com/buddy-2.jpg",
        display_order=2,
        last_synced_at="2026-06-12T09:00:00+00:00",
    )

    row = mappers.animal_image_to_row(model)
    assert row.id == 5
    assert row.animal_id == "A-00000"
    assert row.image_url == "https://example.com/buddy-2.jpg"
    assert row.display_order == 2
    assert row.last_synced_at == datetime.datetime(
        2026, 6, 12, 9, 0, tzinfo=datetime.UTC
    )

    back = mappers.animal_image_from_row(row)
    assert back.id == 5
    assert back.animal_id == "A-00000"
    assert back.image_url == "https://example.com/buddy-2.jpg"
    assert back.display_order == 2
    assert back.last_synced_at == "2026-06-12T09:00:00+00:00"


def test_sync_log_round_trip() -> None:
    model = pyd.SyncLog(
        id=9,
        sync_type="full",
        table_name="animals",
        started_at="2026-06-01T00:00:00+00:00",
        completed_at="2026-06-01T00:10:00+00:00",
        records_processed=10,
        records_created=3,
        records_updated=7,
        status="completed",
    )
    row = mappers.sync_log_to_row(model)
    assert row.id == 9
    assert row.sync_type == "full"
    assert row.table_name == "animals"
    assert row.started_at == datetime.datetime(2026, 6, 1, 0, 0, tzinfo=datetime.UTC)
    assert row.completed_at == datetime.datetime(2026, 6, 1, 0, 10, tzinfo=datetime.UTC)
    assert row.records_processed == 10
    assert row.records_created == 3
    assert row.records_updated == 7
    assert row.status == "completed"
    assert row.error_message is None

    back = mappers.sync_log_from_row(row)
    assert back.id == 9
    assert back.sync_type == "full"
    assert back.table_name == "animals"
    assert back.started_at == "2026-06-01T00:00:00+00:00"
    assert back.completed_at == "2026-06-01T00:10:00+00:00"
    assert back.records_processed == 10
    assert back.records_created == 3
    assert back.records_updated == 7
    assert back.status == "completed"
    assert back.error_message is None


def test_sync_log_round_trip_error_message() -> None:
    model = pyd.SyncLog(
        sync_type="incremental",
        table_name="volunteer_notes",
        started_at="2026-06-02T00:00:00+00:00",
        status="failed",
        error_message="connection reset",
    )
    row = mappers.sync_log_to_row(model)
    assert row.error_message == "connection reset"

    back = mappers.sync_log_from_row(row)
    assert back.error_message == "connection reset"
    assert back.status == "failed"
