"""Integration tests for the async ``Database`` repository against Postgres.

Each test runs on a request-scoped session bound to a freshly-created schema
(see ``tests/conftest.py``). The suite skips automatically when no Postgres is
reachable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from petdata.modules.db.repository import Database

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration


async def _insert_animal(
    repo: Database, animal_id: str = "A-1", name: str = "Buddy"
) -> Animal:
    """Insert and return a minimal animal to satisfy child-row foreign keys."""
    animal = Animal(id=animal_id, name=name)
    await repo.insert_animal(animal)
    return animal


# ── Animal ───────────────────────────────────────────────────────────────────


async def test_insert_and_get_animal_round_trips_fields(session: AsyncSession) -> None:
    repo = Database(session)
    animal = Animal(
        id="A-100",
        name="Rex",
        breed="Lab",
        weight_lbs=65.5,
        birth_date="2020-01-15",
        color_category="Green",
        behavior_mod_tags=["leash", "shy"],
        is_in_kennel=True,
    )
    await repo.insert_animal(animal)

    fetched = await repo.get_animal("A-100")

    assert fetched is not None
    assert fetched.name == "Rex"
    assert fetched.breed == "Lab"
    assert fetched.weight_lbs == 65.5
    assert fetched.birth_date == "2020-01-15"
    assert fetched.behavior_mod_tags == ["leash", "shy"]
    assert fetched.is_in_kennel is True
    # Server defaults are populated on insert.
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


async def test_get_animal_missing_returns_none(session: AsyncSession) -> None:
    repo = Database(session)
    assert await repo.get_animal("A-nope") is None


async def test_update_animal_applies_partial_change(session: AsyncSession) -> None:
    repo = Database(session)
    animal = await _insert_animal(repo, "A-200", "Daisy")

    animal.weight_lbs = 40.0
    await repo.update_animal(animal)

    fetched = await repo.get_animal("A-200")
    assert fetched is not None
    assert fetched.weight_lbs == 40.0
    assert fetched.name == "Daisy"


async def test_list_animals_orders_by_name_with_pagination(
    session: AsyncSession,
) -> None:
    repo = Database(session)
    await repo.insert_animal(Animal(id="A-c", name="Charlie"))
    await repo.insert_animal(Animal(id="A-a", name="Apple"))
    await repo.insert_animal(Animal(id="A-b", name="Bravo"))

    names = [a.name for a in await repo.list_animals(limit=2, offset=0)]
    assert names == ["Apple", "Bravo"]

    second_page = await repo.list_animals(limit=2, offset=2)
    assert [a.name for a in second_page] == ["Charlie"]


async def test_delete_animal_cascades_to_children(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-300", "Cascade")
    note_id = await repo.insert_volunteer_note(
        VolunteerNote(
            animal_id="A-300",
            volunteer_name="V",
            note_date="2026-06-01T10:00:00+00:00",
        )
    )
    await repo.upsert_kennel_card(KennelCard(animal_id="A-300", about_text="hi"))

    await repo.delete_animal("A-300")

    assert await repo.get_animal("A-300") is None
    assert await repo.get_volunteer_note_by_id(note_id) is None
    assert await repo.get_kennel_card("A-300") is None


# ── VolunteerNote ────────────────────────────────────────────────────────────


async def test_insert_volunteer_note_returns_id_and_fetches(
    session: AsyncSession,
) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-400")
    note_id = await repo.insert_volunteer_note(
        VolunteerNote(
            animal_id="A-400",
            volunteer_name="Pat",
            note_date="2026-06-01T09:00:00+00:00",
            rating_shy_fearful=3,
        )
    )

    assert isinstance(note_id, int)
    fetched = await repo.get_volunteer_note_by_id(note_id)
    assert fetched is not None
    assert fetched.volunteer_name == "Pat"
    assert fetched.rating_shy_fearful == 3


async def test_get_notes_for_animal_orders_recent_first(
    session: AsyncSession,
) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-410")
    await repo.insert_volunteer_note(
        VolunteerNote(
            animal_id="A-410",
            volunteer_name="old",
            note_date="2026-01-01T00:00:00+00:00",
        )
    )
    await repo.insert_volunteer_note(
        VolunteerNote(
            animal_id="A-410",
            volunteer_name="new",
            note_date="2026-06-01T00:00:00+00:00",
        )
    )

    notes = await repo.get_notes_for_animal("A-410")
    assert [n.volunteer_name for n in notes] == ["new", "old"]


async def test_update_volunteer_note_without_id_raises(
    session: AsyncSession,
) -> None:
    repo = Database(session)
    with pytest.raises(ValueError, match="without ID"):
        await repo.update_volunteer_note(
            VolunteerNote(
                animal_id="A-1",
                volunteer_name="x",
                note_date="2026-06-01T00:00:00+00:00",
            )
        )


async def test_update_and_delete_volunteer_notes(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-420")
    note_id = await repo.insert_volunteer_note(
        VolunteerNote(
            animal_id="A-420",
            volunteer_name="V",
            note_date="2026-06-01T00:00:00+00:00",
        )
    )
    note = await repo.get_volunteer_note_by_id(note_id)
    assert note is not None
    note.note_text = "updated"
    await repo.update_volunteer_note(note)
    assert (await repo.get_volunteer_note_by_id(note_id)).note_text == "updated"  # type: ignore[union-attr]

    await repo.delete_notes_for_animal("A-420")
    assert await repo.get_notes_for_animal("A-420") == []


# ── KennelCard (upsert) ──────────────────────────────────────────────────────


async def test_upsert_kennel_card_inserts_then_updates_same_row(
    session: AsyncSession,
) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-500")

    first_id = await repo.upsert_kennel_card(
        KennelCard(animal_id="A-500", about_text="first", dogs_compatibility="Good")
    )
    second_id = await repo.upsert_kennel_card(
        KennelCard(animal_id="A-500", about_text="second")
    )

    assert first_id == second_id
    card = await repo.get_kennel_card("A-500")
    assert card is not None
    assert card.about_text == "second"
    # Omitted field keeps the prior value (conflict update skips unset columns).
    assert card.dogs_compatibility == "Good"


async def test_get_kennel_card_by_id_and_delete(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-510")
    card_id = await repo.upsert_kennel_card(
        KennelCard(animal_id="A-510", about_text="x")
    )

    assert (await repo.get_kennel_card_by_id(card_id)) is not None
    await repo.delete_kennel_card_for_animal("A-510")
    assert await repo.get_kennel_card("A-510") is None


# ── StaffAssessment ──────────────────────────────────────────────────────────


async def test_staff_assessment_crud_and_tags(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-600")
    assessment_id = await repo.insert_staff_assessment(
        StaffAssessment(
            animal_id="A-600",
            assessment_tags=["calm", "social"],
            recorded_at="2026-05-01T00:00:00+00:00",
        )
    )

    fetched = await repo.get_staff_assessment_by_id(assessment_id)
    assert fetched is not None
    assert fetched.assessment_tags == ["calm", "social"]

    fetched.notes = "reviewed"
    await repo.update_staff_assessment(fetched)
    listed = await repo.get_assessments_for_animal("A-600")
    assert len(listed) == 1
    assert listed[0].notes == "reviewed"

    await repo.delete_assessments_for_animal("A-600")
    assert await repo.get_assessments_for_animal("A-600") == []


# ── WalkRecord ───────────────────────────────────────────────────────────────


async def test_walk_record_crud_and_ordering(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-700")
    await repo.insert_walk_record(
        WalkRecord(animal_id="A-700", out_time="2026-01-01T08:00:00+00:00")
    )
    recent_id = await repo.insert_walk_record(
        WalkRecord(animal_id="A-700", out_time="2026-06-01T08:00:00+00:00")
    )

    walks = await repo.get_walks_for_animal("A-700")
    assert walks[0].id == recent_id

    record = await repo.get_walk_record_by_id(recent_id)
    assert record is not None
    record.volunteer_name = "Sam"
    await repo.update_walk_record(record)
    assert (await repo.get_walk_record_by_id(recent_id)).volunteer_name == "Sam"  # type: ignore[union-attr]

    await repo.delete_walks_for_animal("A-700")
    assert await repo.get_walks_for_animal("A-700") == []


# ── AnimalImage ──────────────────────────────────────────────────────────────


async def test_animal_image_crud_and_ordering(session: AsyncSession) -> None:
    repo = Database(session)
    await _insert_animal(repo, "A-800")
    await repo.insert_animal_image(
        AnimalImage(animal_id="A-800", image_url="b.jpg", display_order=2)
    )
    first_id = await repo.insert_animal_image(
        AnimalImage(animal_id="A-800", image_url="a.jpg", display_order=1)
    )

    images = await repo.get_images_for_animal("A-800")
    assert images[0].id == first_id

    img = await repo.get_animal_image_by_id(first_id)
    assert img is not None
    img.image_url = "updated.jpg"
    await repo.update_animal_image(img)
    assert (await repo.get_animal_image_by_id(first_id)).image_url == "updated.jpg"  # type: ignore[union-attr]

    await repo.delete_images_for_animal("A-800")
    assert await repo.get_images_for_animal("A-800") == []


# ── SyncLog ──────────────────────────────────────────────────────────────────


async def test_sync_log_lifecycle_and_latest(session: AsyncSession) -> None:
    repo = Database(session)
    older = await repo.insert_sync_log(
        SyncLog(
            sync_type="full",
            table_name="animals",
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:05:00+00:00",
            status="completed",
        )
    )
    newer = await repo.insert_sync_log(
        SyncLog(
            sync_type="incremental",
            table_name="animals",
            started_at="2026-06-01T00:00:00+00:00",
            completed_at="2026-06-01T00:05:00+00:00",
            status="completed",
        )
    )
    # A running sync must not count as the latest completed one.
    await repo.insert_sync_log(
        SyncLog(
            sync_type="incremental",
            table_name="animals",
            started_at="2026-07-01T00:00:00+00:00",
            status="running",
        )
    )

    latest = await repo.get_latest_sync("animals")
    assert latest is not None
    assert latest.id == newer

    await repo.delete_sync_log(older)
    await repo.delete_sync_logs_before("animals", "2026-12-31T00:00:00+00:00")
    assert await repo.get_latest_sync("animals") is None
