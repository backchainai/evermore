# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Async database repository for CRUD operations.

The repository speaks the Pydantic contract (``petdata.modules.db.models``) on
its boundary and persists through the SQLAlchemy 2.0 async ORM
(``petdata.models.tables``), bridging the two with ``petdata.models.mappers``.
Each instance is bound to a request-scoped ``AsyncSession`` (see
``petdata.infrastructure.database.session.get_session``); the session owns the
transaction and commits or rolls back when the request ends.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from petdata.models import mappers
from petdata.models import tables as orm

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.ext.asyncio import AsyncSession

    from petdata.modules.db.models import (
        Animal,
        AnimalImage,
        KennelCard,
        StaffAssessment,
        SyncLog,
        VolunteerNote,
        WalkRecord,
    )

# Contract fields whose Pydantic value is an ISO string but whose ORM column is
# a native ``date`` / ``datetime``. Used to coerce partial-update payloads; the
# names do not collide across models (birth/intake are dates everywhere, the
# rest are timestamps everywhere).
_DATE_FIELDS = frozenset({"birth_date", "intake_date"})
_DATETIME_FIELDS = frozenset(
    {
        "note_date",
        "recorded_at",
        "out_time",
        "in_time",
        "started_at",
        "completed_at",
        "last_synced_at",
        "created_at",
        "updated_at",
    }
)


def _to_date(value: str) -> datetime.date:
    """Parse an ISO date (or datetime) string into a date."""
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return datetime.datetime.fromisoformat(value).date()


def _coerce(key: str, value: Any) -> Any:
    """Coerce a contract value to the ORM column's native type."""
    if value is None:
        return None
    if key in _DATETIME_FIELDS and isinstance(value, str):
        return datetime.datetime.fromisoformat(value)
    if key in _DATE_FIELDS and isinstance(value, str):
        return _to_date(value)
    return value


def _changed_values(model: BaseModel) -> dict[str, Any]:
    """Return the explicitly-set fields of ``model`` as ORM column values.

    Preserves partial-update semantics: only fields the caller set are written,
    each coerced from the Pydantic contract type to the ORM column type. The
    primary key is excluded; it identifies the row, it is not a mutation.
    """
    raw = model.model_dump(exclude_unset=True)
    raw.pop("id", None)
    return {key: _coerce(key, value) for key, value in raw.items()}


class Database:
    """Async repository bound to a single request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Request-scoped async session that owns the transaction.
        """
        self._session = session

    # Animal operations

    async def insert_animal(self, animal: Animal) -> None:
        """Insert an animal record.

        Args:
            animal: Animal to insert.
        """
        self._session.add(mappers.animal_to_row(animal))
        await self._session.flush()

    async def get_animal(self, animal_id: str) -> Animal | None:
        """Get an animal by ID.

        Args:
            animal_id: Animal ID (e.g., A-00000).

        Returns:
            Animal if found, None otherwise.
        """
        row = await self._session.get(orm.Animal, animal_id)
        return mappers.animal_from_row(row) if row else None

    async def update_animal(self, animal: Animal) -> None:
        """Update an existing animal record.

        Args:
            animal: Animal with updated data.
        """
        values = _changed_values(animal)
        if not values:
            return
        await self._session.execute(
            update(orm.Animal).where(orm.Animal.id == animal.id).values(**values)
        )

    async def delete_animal(self, animal_id: str) -> None:
        """Delete an animal and all related records.

        Related rows (images, walks, notes, assessments, kennel card) are
        removed by the ``ON DELETE CASCADE`` foreign keys.

        Args:
            animal_id: Animal ID to delete.
        """
        await self._session.execute(
            delete(orm.Animal).where(orm.Animal.id == animal_id)
        )

    async def list_animals(self, limit: int = 100, offset: int = 0) -> list[Animal]:
        """List animals with pagination.

        Args:
            limit: Maximum number of animals to return.
            offset: Number of animals to skip.

        Returns:
            List of animals ordered by name.
        """
        stmt = select(orm.Animal).order_by(orm.Animal.name).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [mappers.animal_from_row(row) for row in result.scalars().all()]

    # Volunteer note operations

    async def insert_volunteer_note(self, note: VolunteerNote) -> int:
        """Insert a volunteer note.

        Args:
            note: VolunteerNote to insert.

        Returns:
            ID of inserted note.
        """
        row = mappers.volunteer_note_to_row(note)
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def get_notes_for_animal(
        self, animal_id: str, limit: int = 100
    ) -> list[VolunteerNote]:
        """Get volunteer notes for an animal, most recent first.

        Args:
            animal_id: Animal ID.
            limit: Maximum number of notes to return.

        Returns:
            List of volunteer notes, ordered by note_date descending.
        """
        stmt = (
            select(orm.VolunteerNote)
            .where(orm.VolunteerNote.animal_id == animal_id)
            .order_by(orm.VolunteerNote.note_date.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.volunteer_note_from_row(row) for row in result.scalars().all()]

    async def get_volunteer_note_by_id(self, note_id: int) -> VolunteerNote | None:
        """Get a volunteer note by ID.

        Args:
            note_id: Volunteer note ID.

        Returns:
            VolunteerNote if found, None otherwise.
        """
        row = await self._session.get(orm.VolunteerNote, note_id)
        return mappers.volunteer_note_from_row(row) if row else None

    async def update_volunteer_note(self, note: VolunteerNote) -> None:
        """Update an existing volunteer note.

        Args:
            note: VolunteerNote with updated data (must have ID).

        Raises:
            ValueError: If note.id is None.
        """
        if note.id is None:
            msg = "Cannot update volunteer note without ID"
            raise ValueError(msg)
        values = _changed_values(note)
        if not values:
            return
        await self._session.execute(
            update(orm.VolunteerNote)
            .where(orm.VolunteerNote.id == note.id)
            .values(**values)
        )

    async def delete_notes_for_animal(self, animal_id: str) -> None:
        """Delete all volunteer notes for an animal.

        Args:
            animal_id: Animal ID.
        """
        await self._session.execute(
            delete(orm.VolunteerNote).where(orm.VolunteerNote.animal_id == animal_id)
        )

    # Kennel card operations

    async def upsert_kennel_card(self, card: KennelCard) -> int:
        """Insert or update a kennel card (one per animal).

        Args:
            card: KennelCard to upsert.

        Returns:
            ID of upserted card.
        """
        row = mappers.kennel_card_to_row(card)
        insert_values: dict[str, Any] = {
            "animal_id": row.animal_id,
            "about_text": row.about_text,
            "dogs_compatibility": row.dogs_compatibility,
            "dogs_compatibility_notes": row.dogs_compatibility_notes,
            "cats_compatibility": row.cats_compatibility,
            "cats_compatibility_notes": row.cats_compatibility_notes,
            "kids_compatibility": row.kids_compatibility,
            "kids_compatibility_notes": row.kids_compatibility_notes,
            "commands_known": row.commands_known,
            "housebreaking_status": row.housebreaking_status,
            "things_likes": row.things_likes,
            "things_dislikes": row.things_dislikes,
            "last_synced_at": row.last_synced_at,
        }
        # Drop unset values so omitted columns keep their defaults and a conflict
        # does not overwrite existing data with NULL.
        present = {k: v for k, v in insert_values.items() if v is not None}
        update_set = {k: v for k, v in present.items() if k != "animal_id"}
        stmt = (
            pg_insert(orm.KennelCard)
            .values(**present)
            .on_conflict_do_update(index_elements=["animal_id"], set_=update_set)
            .returning(orm.KennelCard.id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        card_id: int = result.scalar_one()
        return card_id

    async def get_kennel_card(self, animal_id: str) -> KennelCard | None:
        """Get kennel card for an animal.

        Args:
            animal_id: Animal ID.

        Returns:
            KennelCard if found, None otherwise.
        """
        stmt = select(orm.KennelCard).where(orm.KennelCard.animal_id == animal_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return mappers.kennel_card_from_row(row) if row else None

    async def get_kennel_card_by_id(self, card_id: int) -> KennelCard | None:
        """Get a kennel card by ID.

        Args:
            card_id: Kennel card ID.

        Returns:
            KennelCard if found, None otherwise.
        """
        row = await self._session.get(orm.KennelCard, card_id)
        return mappers.kennel_card_from_row(row) if row else None

    async def delete_kennel_card_for_animal(self, animal_id: str) -> None:
        """Delete kennel card for an animal.

        Args:
            animal_id: Animal ID.
        """
        await self._session.execute(
            delete(orm.KennelCard).where(orm.KennelCard.animal_id == animal_id)
        )

    # Staff assessment operations

    async def insert_staff_assessment(self, assessment: StaffAssessment) -> int:
        """Insert a staff assessment.

        Args:
            assessment: StaffAssessment to insert.

        Returns:
            ID of inserted assessment.
        """
        row = mappers.staff_assessment_to_row(assessment)
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def get_assessments_for_animal(self, animal_id: str) -> list[StaffAssessment]:
        """Get staff assessments for an animal, most recent first.

        Args:
            animal_id: Animal ID.

        Returns:
            List of staff assessments ordered by recorded_at descending.
        """
        stmt = (
            select(orm.StaffAssessment)
            .where(orm.StaffAssessment.animal_id == animal_id)
            .order_by(orm.StaffAssessment.recorded_at.desc())
        )
        result = await self._session.execute(stmt)
        return [
            mappers.staff_assessment_from_row(row) for row in result.scalars().all()
        ]

    async def get_staff_assessment_by_id(
        self, assessment_id: int
    ) -> StaffAssessment | None:
        """Get a staff assessment by ID.

        Args:
            assessment_id: Staff assessment ID.

        Returns:
            StaffAssessment if found, None otherwise.
        """
        row = await self._session.get(orm.StaffAssessment, assessment_id)
        return mappers.staff_assessment_from_row(row) if row else None

    async def update_staff_assessment(self, assessment: StaffAssessment) -> None:
        """Update an existing staff assessment.

        Args:
            assessment: StaffAssessment with updated data (must have ID).

        Raises:
            ValueError: If assessment.id is None.
        """
        if assessment.id is None:
            msg = "Cannot update staff assessment without ID"
            raise ValueError(msg)
        values = _changed_values(assessment)
        if not values:
            return
        await self._session.execute(
            update(orm.StaffAssessment)
            .where(orm.StaffAssessment.id == assessment.id)
            .values(**values)
        )

    async def delete_assessments_for_animal(self, animal_id: str) -> None:
        """Delete all staff assessments for an animal.

        Args:
            animal_id: Animal ID.
        """
        await self._session.execute(
            delete(orm.StaffAssessment).where(
                orm.StaffAssessment.animal_id == animal_id
            )
        )

    # Walk record operations

    async def insert_walk_record(self, record: WalkRecord) -> int:
        """Insert a walk record.

        Args:
            record: WalkRecord to insert.

        Returns:
            ID of inserted record.
        """
        row = mappers.walk_record_to_row(record)
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def get_walks_for_animal(
        self, animal_id: str, limit: int = 100
    ) -> list[WalkRecord]:
        """Get walk records for an animal, most recent first.

        Args:
            animal_id: Animal ID.
            limit: Maximum number of records to return.

        Returns:
            List of walk records ordered by out_time descending.
        """
        stmt = (
            select(orm.WalkRecord)
            .where(orm.WalkRecord.animal_id == animal_id)
            .order_by(orm.WalkRecord.out_time.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.walk_record_from_row(row) for row in result.scalars().all()]

    async def get_walk_record_by_id(self, record_id: int) -> WalkRecord | None:
        """Get a walk record by ID.

        Args:
            record_id: Walk record ID.

        Returns:
            WalkRecord if found, None otherwise.
        """
        row = await self._session.get(orm.WalkRecord, record_id)
        return mappers.walk_record_from_row(row) if row else None

    async def update_walk_record(self, record: WalkRecord) -> None:
        """Update an existing walk record.

        Args:
            record: WalkRecord with updated data (must have ID).

        Raises:
            ValueError: If record.id is None.
        """
        if record.id is None:
            msg = "Cannot update walk record without ID"
            raise ValueError(msg)
        values = _changed_values(record)
        if not values:
            return
        await self._session.execute(
            update(orm.WalkRecord)
            .where(orm.WalkRecord.id == record.id)
            .values(**values)
        )

    async def delete_walks_for_animal(self, animal_id: str) -> None:
        """Delete all walk records for an animal.

        Args:
            animal_id: Animal ID.
        """
        await self._session.execute(
            delete(orm.WalkRecord).where(orm.WalkRecord.animal_id == animal_id)
        )

    # Animal image operations

    async def insert_animal_image(self, image: AnimalImage) -> int:
        """Insert an animal image.

        Args:
            image: AnimalImage to insert.

        Returns:
            ID of inserted image.
        """
        row = mappers.animal_image_to_row(image)
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def get_images_for_animal(self, animal_id: str) -> list[AnimalImage]:
        """Get images for an animal, ordered by display order.

        Args:
            animal_id: Animal ID.

        Returns:
            List of animal images.
        """
        stmt = (
            select(orm.AnimalImage)
            .where(orm.AnimalImage.animal_id == animal_id)
            .order_by(orm.AnimalImage.display_order)
        )
        result = await self._session.execute(stmt)
        return [mappers.animal_image_from_row(row) for row in result.scalars().all()]

    async def get_animal_image_by_id(self, image_id: int) -> AnimalImage | None:
        """Get an animal image by ID.

        Args:
            image_id: Animal image ID.

        Returns:
            AnimalImage if found, None otherwise.
        """
        row = await self._session.get(orm.AnimalImage, image_id)
        return mappers.animal_image_from_row(row) if row else None

    async def update_animal_image(self, image: AnimalImage) -> None:
        """Update an existing animal image.

        Args:
            image: AnimalImage with updated data (must have ID).

        Raises:
            ValueError: If image.id is None.
        """
        if image.id is None:
            msg = "Cannot update animal image without ID"
            raise ValueError(msg)
        values = _changed_values(image)
        if not values:
            return
        await self._session.execute(
            update(orm.AnimalImage)
            .where(orm.AnimalImage.id == image.id)
            .values(**values)
        )

    async def delete_images_for_animal(self, animal_id: str) -> None:
        """Delete all images for an animal.

        Args:
            animal_id: Animal ID.
        """
        await self._session.execute(
            delete(orm.AnimalImage).where(orm.AnimalImage.animal_id == animal_id)
        )

    # Sync log operations

    async def insert_sync_log(self, log: SyncLog) -> int:
        """Insert a sync log entry.

        Args:
            log: SyncLog to insert.

        Returns:
            ID of inserted log.
        """
        row = mappers.sync_log_to_row(log)
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def update_sync_log(self, log: SyncLog) -> None:
        """Update a sync log entry.

        Args:
            log: SyncLog with updated data (must have ID).

        Raises:
            ValueError: If log.id is None.
        """
        if log.id is None:
            msg = "Cannot update sync log without ID"
            raise ValueError(msg)
        values = _changed_values(log)
        if not values:
            return
        await self._session.execute(
            update(orm.SyncLog).where(orm.SyncLog.id == log.id).values(**values)
        )

    async def get_latest_sync(self, table_name: str) -> SyncLog | None:
        """Get the most recent completed sync for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Most recent completed SyncLog if found, None otherwise.
        """
        stmt = (
            select(orm.SyncLog)
            .where(
                orm.SyncLog.table_name == table_name,
                orm.SyncLog.status == "completed",
            )
            .order_by(orm.SyncLog.completed_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return mappers.sync_log_from_row(row) if row else None

    async def delete_sync_log(self, log_id: int) -> None:
        """Delete a sync log entry.

        Args:
            log_id: Sync log ID to delete.
        """
        await self._session.execute(delete(orm.SyncLog).where(orm.SyncLog.id == log_id))

    async def delete_sync_logs_before(self, table_name: str, before_date: str) -> None:
        """Delete old sync logs for a table (cleanup operation).

        Args:
            table_name: Name of the table.
            before_date: Delete logs completed before this ISO timestamp.
        """
        cutoff = datetime.datetime.fromisoformat(before_date)
        await self._session.execute(
            delete(orm.SyncLog).where(
                orm.SyncLog.table_name == table_name,
                orm.SyncLog.completed_at < cutoff,
            )
        )
