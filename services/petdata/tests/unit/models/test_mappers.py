"""Unit tests for the Pydantic <-> ORM mappers."""

from __future__ import annotations

import datetime

from petdata.models import mappers
from petdata.modules.db import models as pyd


def test_animal_round_trip_preserves_fields() -> None:
    model = pyd.Animal(
        id="A-55833",
        name="Buddy",
        weight_lbs=70.0,
        birth_date="2020-01-15",
        intake_date="2024-03-01",
        color_category="Green",
        behavior_mod_tags=["leash", "shy"],
        is_in_kennel=True,
        is_foster_care=False,
        created_at="2026-06-01T12:00:00+00:00",
        last_synced_at="2026-06-02T08:30:00+00:00",
    )

    row = mappers.animal_to_row(model)
    assert row.id == "A-55833"
    assert row.weight_lbs == 70.0
    assert row.birth_date == datetime.date(2020, 1, 15)
    assert row.intake_date == datetime.date(2024, 3, 1)
    assert row.behavior_mod_tags == ["leash", "shy"]
    assert row.is_in_kennel is True
    assert row.is_foster_care is False
    assert row.created_at == datetime.datetime(2026, 6, 1, 12, 0, tzinfo=datetime.UTC)

    back = mappers.animal_from_row(row)
    assert back.id == "A-55833"
    assert back.birth_date == "2020-01-15"
    assert back.behavior_mod_tags == ["leash", "shy"]
    assert back.is_in_kennel is True
    assert back.created_at == "2026-06-01T12:00:00+00:00"
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


def test_volunteer_note_round_trip() -> None:
    model = pyd.VolunteerNote(
        id=12,
        animal_id="A-55833",
        volunteer_name="Pat",
        note_date="2026-06-10T09:00:00+00:00",
        note_text="Walked well",
        rating_strong_on_leash=4,
        created_at="2026-06-10T09:05:00+00:00",
    )

    row = mappers.volunteer_note_to_row(model)
    assert row.id == 12
    assert row.animal_id == "A-55833"
    assert row.note_date == datetime.datetime(2026, 6, 10, 9, 0, tzinfo=datetime.UTC)
    assert row.rating_strong_on_leash == 4

    back = mappers.volunteer_note_from_row(row)
    assert back.note_date == "2026-06-10T09:00:00+00:00"
    assert back.volunteer_name == "Pat"
    assert back.rating_strong_on_leash == 4


def test_staff_assessment_round_trip_tags() -> None:
    model = pyd.StaffAssessment(
        animal_id="A-1",
        assessment_tags=["food-motivated", "crate-trained"],
        notes="Solid",
        recorded_at="2026-06-09T10:00:00+00:00",
    )
    row = mappers.staff_assessment_to_row(model)
    assert row.assessment_tags == ["food-motivated", "crate-trained"]

    back = mappers.staff_assessment_from_row(row)
    assert back.assessment_tags == ["food-motivated", "crate-trained"]
    assert back.recorded_at == "2026-06-09T10:00:00+00:00"


def test_sync_log_round_trip() -> None:
    model = pyd.SyncLog(
        sync_type="full",
        table_name="animals",
        started_at="2026-06-01T00:00:00+00:00",
        records_processed=10,
        status="completed",
    )
    row = mappers.sync_log_to_row(model)
    assert row.sync_type == "full"
    assert row.started_at == datetime.datetime(2026, 6, 1, 0, 0, tzinfo=datetime.UTC)

    back = mappers.sync_log_from_row(row)
    assert back.status == "completed"
    assert back.records_processed == 10
    assert back.started_at == "2026-06-01T00:00:00+00:00"
