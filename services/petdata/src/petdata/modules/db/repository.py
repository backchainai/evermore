"""Database repository for CRUD operations.

Security Note: Dynamic SQL construction uses column names from Pydantic's
model_dump() which only returns fixed, known field names from the model schema.
All data values are properly parameterized. The # nosec B608 comments acknowledge
this pattern is safe in this context. See code review for detailed analysis.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any

from petdata.modules.db.models import (
    Animal,
    AnimalImage,
    KennelCard,
    StaffAssessment,
    SyncLog,
    VolunteerNote,
    WalkRecord,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def _add_timestamps(
    data: dict[str, Any],
    *,
    include_created: bool = True,
    include_updated: bool = True,
) -> None:
    """Add default timestamps to data dict if not present.

    Mutates data dict in place.

    Args:
        data: Dictionary of model data to mutate.
        include_created: Whether to add created_at (False for updates).
        include_updated: Whether to add updated_at (False for models without it).
    """
    now = datetime.now().isoformat()
    if include_created and "created_at" not in data:
        data["created_at"] = now
    if include_updated and "updated_at" not in data:
        data["updated_at"] = now


def _build_insert_sql(table_name: str, data: dict[str, Any]) -> str:
    """Build parameterized INSERT SQL statement.

    Args:
        table_name: Name of table to insert into.
        data: Dictionary of column names to values (must not be empty).

    Returns:
        SQL INSERT statement with named placeholders.

    Raises:
        ValueError: If data is empty.
    """
    if not data:
        msg = f"Cannot insert into {table_name}: no data provided"
        raise ValueError(msg)
    columns = ", ".join(data)
    placeholders = ", ".join(f":{k}" for k in data)
    return f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"  # nosec B608


def _build_update_sql(table_name: str, data: dict[str, Any], id_key: str = "id") -> str:
    """Build parameterized UPDATE SQL statement.

    Args:
        table_name: Name of table to update.
        data: Dictionary of column names to values (must include id_key).
        id_key: Name of ID column (default: "id").

    Returns:
        SQL UPDATE statement with named placeholders.

    Raises:
        ValueError: If data contains no fields to update (only ID).
    """
    set_fields = [k for k in data if k != id_key]
    if not set_fields:
        msg = f"Cannot update {table_name}: no fields to update besides {id_key}"
        raise ValueError(msg)
    set_clause = ", ".join(f"{k} = :{k}" for k in set_fields)
    return f"UPDATE {table_name} SET {set_clause} WHERE {id_key} = :{id_key}"  # nosec B608


def _build_upsert_sql(table_name: str, data: dict[str, Any], conflict_key: str) -> str:
    """Build parameterized UPSERT (INSERT ... ON CONFLICT) SQL statement.

    Args:
        table_name: Name of table to upsert into.
        data: Dictionary of column names to values.
        conflict_key: Column name that triggers conflict (e.g., "animal_id").

    Returns:
        SQL UPSERT statement with named placeholders.
    """
    columns = ", ".join(data)
    placeholders = ", ".join(f":{k}" for k in data)
    update_clause = ", ".join(f"{k} = excluded.{k}" for k in data if k != conflict_key)
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) "  # nosec B608
    sql += f"ON CONFLICT({conflict_key}) DO UPDATE SET {update_clause}"  # nosec B608
    return sql


class Database:
    """Database connection and operations manager."""

    def __init__(self, db_path: Path) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Create a database connection context.

        Yields:
            SQLite connection with row factory set.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Create a database transaction context.

        Commits on success, rolls back on exception.

        Yields:
            SQLite connection with row factory set.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Animal operations

    def insert_animal(self, animal: Animal) -> None:
        """Insert an animal record.

        Args:
            animal: Animal to insert.
        """
        data = animal.model_dump(mode="json", exclude_none=True)
        _add_timestamps(data)
        sql = _build_insert_sql("animals", data)

        with self.transaction() as conn:
            # Column names from model_dump() are fixed; values are parameterized
            conn.execute(sql, data)  # nosec B608

    def get_animal(self, animal_id: str) -> Animal | None:
        """Get an animal by ID.

        Args:
            animal_id: Animal ID (e.g., A-55833).

        Returns:
            Animal if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
            row = cursor.fetchone()
            return Animal.model_validate(dict(row)) if row else None

    def update_animal(self, animal: Animal) -> None:
        """Update an existing animal record.

        Args:
            animal: Animal with updated data.
        """
        data = animal.model_dump(mode="json", exclude_unset=True)
        _add_timestamps(data, include_created=False)
        sql = _build_update_sql("animals", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def delete_animal(self, animal_id: str) -> None:
        """Delete an animal and all related records (auto-cascade).

        Deletes all related records first (images, walks, notes, assessments,
        kennel cards) before deleting the animal, all within a single transaction.

        Args:
            animal_id: Animal ID to delete.
        """
        with self.transaction() as conn:
            # Delete children first (FK constraints require this order)
            conn.execute("DELETE FROM animal_images WHERE animal_id = ?", (animal_id,))
            conn.execute("DELETE FROM walk_records WHERE animal_id = ?", (animal_id,))
            conn.execute(
                "DELETE FROM volunteer_notes WHERE animal_id = ?", (animal_id,)
            )
            conn.execute(
                "DELETE FROM staff_assessments WHERE animal_id = ?", (animal_id,)
            )
            conn.execute("DELETE FROM kennel_cards WHERE animal_id = ?", (animal_id,))
            # Delete parent last
            conn.execute("DELETE FROM animals WHERE id = ?", (animal_id,))

    def list_animals(self, limit: int = 100, offset: int = 0) -> list[Animal]:
        """List animals with pagination.

        Args:
            limit: Maximum number of animals to return.
            offset: Number of animals to skip.

        Returns:
            List of animals.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM animals ORDER BY name LIMIT ? OFFSET ?", (limit, offset)
            )
            return [Animal.model_validate(dict(row)) for row in cursor.fetchall()]

    # Volunteer note operations

    def insert_volunteer_note(self, note: VolunteerNote) -> int:
        """Insert a volunteer note.

        Args:
            note: VolunteerNote to insert.

        Returns:
            ID of inserted note.
        """
        data = note.model_dump(mode="json", exclude_none=True, exclude={"id"})
        _add_timestamps(data, include_updated=False)
        sql = _build_insert_sql("volunteer_notes", data)

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to insert volunteer_notes record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def get_notes_for_animal(
        self, animal_id: str, limit: int = 100
    ) -> list[VolunteerNote]:
        """Get volunteer notes for an animal, ordered by date descending.

        Args:
            animal_id: Animal ID.
            limit: Maximum number of notes to return.

        Returns:
            List of volunteer notes, most recent first.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM volunteer_notes
                WHERE animal_id = ?
                ORDER BY note_date DESC
                LIMIT ?
                """,
                (animal_id, limit),
            )
            return [
                VolunteerNote.model_validate(dict(row)) for row in cursor.fetchall()
            ]

    def get_volunteer_note_by_id(self, note_id: int) -> VolunteerNote | None:
        """Get a volunteer note by ID.

        Args:
            note_id: Volunteer note ID.

        Returns:
            VolunteerNote if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM volunteer_notes WHERE id = ?", (note_id,)
            )
            row = cursor.fetchone()
            return VolunteerNote.model_validate(dict(row)) if row else None

    def update_volunteer_note(self, note: VolunteerNote) -> None:
        """Update an existing volunteer note.

        Args:
            note: VolunteerNote with updated data (must have ID).

        Raises:
            ValueError: If note.id is None.
        """
        if note.id is None:
            msg = "Cannot update volunteer note without ID"
            raise ValueError(msg)

        data = note.model_dump(mode="json", exclude_unset=True)
        sql = _build_update_sql("volunteer_notes", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def delete_notes_for_animal(self, animal_id: str) -> None:
        """Delete all volunteer notes for an animal.

        Args:
            animal_id: Animal ID.
        """
        with self.transaction() as conn:
            conn.execute(
                "DELETE FROM volunteer_notes WHERE animal_id = ?", (animal_id,)
            )

    # Kennel card operations

    def upsert_kennel_card(self, card: KennelCard) -> int:
        """Insert or update a kennel card.

        Args:
            card: KennelCard to upsert.

        Returns:
            ID of upserted card.
        """
        data = card.model_dump(mode="json", exclude_none=True, exclude={"id"})
        sql = _build_upsert_sql("kennel_cards", data, conflict_key="animal_id")

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to upsert kennel_cards record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def get_kennel_card(self, animal_id: str) -> KennelCard | None:
        """Get kennel card for an animal.

        Args:
            animal_id: Animal ID.

        Returns:
            KennelCard if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM kennel_cards WHERE animal_id = ?", (animal_id,)
            )
            row = cursor.fetchone()
            return KennelCard.model_validate(dict(row)) if row else None

    def get_kennel_card_by_id(self, card_id: int) -> KennelCard | None:
        """Get a kennel card by ID.

        Args:
            card_id: Kennel card ID.

        Returns:
            KennelCard if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM kennel_cards WHERE id = ?", (card_id,))
            row = cursor.fetchone()
            return KennelCard.model_validate(dict(row)) if row else None

    def delete_kennel_card_for_animal(self, animal_id: str) -> None:
        """Delete kennel card for an animal.

        Args:
            animal_id: Animal ID.
        """
        with self.transaction() as conn:
            conn.execute("DELETE FROM kennel_cards WHERE animal_id = ?", (animal_id,))

    # Staff assessment operations

    def insert_staff_assessment(self, assessment: StaffAssessment) -> int:
        """Insert a staff assessment.

        Args:
            assessment: StaffAssessment to insert.

        Returns:
            ID of inserted assessment.
        """
        data = assessment.model_dump(mode="json", exclude_none=True, exclude={"id"})
        sql = _build_insert_sql("staff_assessments", data)

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to insert staff_assessments record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def get_assessments_for_animal(self, animal_id: str) -> list[StaffAssessment]:
        """Get staff assessments for an animal.

        Args:
            animal_id: Animal ID.

        Returns:
            List of staff assessments.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM staff_assessments
                WHERE animal_id = ?
                ORDER BY recorded_at DESC
                """,
                (animal_id,),
            )
            return [
                StaffAssessment.model_validate(dict(row)) for row in cursor.fetchall()
            ]

    def get_staff_assessment_by_id(self, assessment_id: int) -> StaffAssessment | None:
        """Get a staff assessment by ID.

        Args:
            assessment_id: Staff assessment ID.

        Returns:
            StaffAssessment if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM staff_assessments WHERE id = ?", (assessment_id,)
            )
            row = cursor.fetchone()
            return StaffAssessment.model_validate(dict(row)) if row else None

    def update_staff_assessment(self, assessment: StaffAssessment) -> None:
        """Update an existing staff assessment.

        Args:
            assessment: StaffAssessment with updated data (must have ID).

        Raises:
            ValueError: If assessment.id is None.
        """
        if assessment.id is None:
            msg = "Cannot update staff assessment without ID"
            raise ValueError(msg)

        data = assessment.model_dump(mode="json", exclude_unset=True)
        sql = _build_update_sql("staff_assessments", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def delete_assessments_for_animal(self, animal_id: str) -> None:
        """Delete all staff assessments for an animal.

        Args:
            animal_id: Animal ID.
        """
        with self.transaction() as conn:
            conn.execute(
                "DELETE FROM staff_assessments WHERE animal_id = ?", (animal_id,)
            )

    # Walk record operations

    def insert_walk_record(self, record: WalkRecord) -> int:
        """Insert a walk record.

        Args:
            record: WalkRecord to insert.

        Returns:
            ID of inserted record.
        """
        data = record.model_dump(mode="json", exclude_none=True, exclude={"id"})
        _add_timestamps(data, include_updated=False)
        sql = _build_insert_sql("walk_records", data)

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to insert walk_records record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def get_walks_for_animal(
        self, animal_id: str, limit: int = 100
    ) -> list[WalkRecord]:
        """Get walk records for an animal.

        Args:
            animal_id: Animal ID.
            limit: Maximum number of records to return.

        Returns:
            List of walk records, most recent first.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM walk_records
                WHERE animal_id = ?
                ORDER BY out_time DESC
                LIMIT ?
                """,
                (animal_id, limit),
            )
            return [WalkRecord.model_validate(dict(row)) for row in cursor.fetchall()]

    def get_walk_record_by_id(self, record_id: int) -> WalkRecord | None:
        """Get a walk record by ID.

        Args:
            record_id: Walk record ID.

        Returns:
            WalkRecord if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM walk_records WHERE id = ?", (record_id,)
            )
            row = cursor.fetchone()
            return WalkRecord.model_validate(dict(row)) if row else None

    def update_walk_record(self, record: WalkRecord) -> None:
        """Update an existing walk record.

        Args:
            record: WalkRecord with updated data (must have ID).

        Raises:
            ValueError: If record.id is None.
        """
        if record.id is None:
            msg = "Cannot update walk record without ID"
            raise ValueError(msg)

        data = record.model_dump(mode="json", exclude_unset=True)
        sql = _build_update_sql("walk_records", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def delete_walks_for_animal(self, animal_id: str) -> None:
        """Delete all walk records for an animal.

        Args:
            animal_id: Animal ID.
        """
        with self.transaction() as conn:
            conn.execute("DELETE FROM walk_records WHERE animal_id = ?", (animal_id,))

    # Animal image operations

    def insert_animal_image(self, image: AnimalImage) -> int:
        """Insert an animal image.

        Args:
            image: AnimalImage to insert.

        Returns:
            ID of inserted image.
        """
        data = image.model_dump(mode="json", exclude_none=True, exclude={"id"})
        sql = _build_insert_sql("animal_images", data)

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to insert animal_images record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def get_images_for_animal(self, animal_id: str) -> list[AnimalImage]:
        """Get images for an animal.

        Args:
            animal_id: Animal ID.

        Returns:
            List of animal images, ordered by display order.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM animal_images
                WHERE animal_id = ?
                ORDER BY display_order
                """,
                (animal_id,),
            )
            return [AnimalImage.model_validate(dict(row)) for row in cursor.fetchall()]

    def get_animal_image_by_id(self, image_id: int) -> AnimalImage | None:
        """Get an animal image by ID.

        Args:
            image_id: Animal image ID.

        Returns:
            AnimalImage if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM animal_images WHERE id = ?", (image_id,)
            )
            row = cursor.fetchone()
            return AnimalImage.model_validate(dict(row)) if row else None

    def update_animal_image(self, image: AnimalImage) -> None:
        """Update an existing animal image.

        Args:
            image: AnimalImage with updated data (must have ID).

        Raises:
            ValueError: If image.id is None.
        """
        if image.id is None:
            msg = "Cannot update animal image without ID"
            raise ValueError(msg)

        data = image.model_dump(mode="json", exclude_unset=True)
        sql = _build_update_sql("animal_images", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def delete_images_for_animal(self, animal_id: str) -> None:
        """Delete all images for an animal.

        Args:
            animal_id: Animal ID.
        """
        with self.transaction() as conn:
            conn.execute("DELETE FROM animal_images WHERE animal_id = ?", (animal_id,))

    # Sync log operations

    def insert_sync_log(self, log: SyncLog) -> int:
        """Insert a sync log entry.

        Args:
            log: SyncLog to insert.

        Returns:
            ID of inserted log.
        """
        data = log.model_dump(mode="json", exclude_none=True, exclude={"id"})
        sql = _build_insert_sql("sync_log", data)

        with self.transaction() as conn:
            cursor = conn.execute(sql, data)  # nosec B608
            if cursor.lastrowid is None:
                msg = "Failed to insert sync_log record"
                raise RuntimeError(msg)
            return cursor.lastrowid

    def update_sync_log(self, log: SyncLog) -> None:
        """Update a sync log entry.

        Args:
            log: SyncLog with updated data.
        """
        if log.id is None:
            msg = "Cannot update sync log without ID"
            raise ValueError(msg)

        data = log.model_dump(mode="json", exclude_unset=True)
        sql = _build_update_sql("sync_log", data)

        with self.transaction() as conn:
            conn.execute(sql, data)  # nosec B608

    def get_latest_sync(self, table_name: str) -> SyncLog | None:
        """Get the most recent completed sync for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Most recent completed SyncLog if found, None otherwise.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sync_log
                WHERE table_name = ? AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 1
                """,
                (table_name,),
            )
            row = cursor.fetchone()
            return SyncLog.model_validate(dict(row)) if row else None

    def delete_sync_log(self, log_id: int) -> None:
        """Delete a sync log entry.

        Args:
            log_id: Sync log ID to delete.
        """
        with self.transaction() as conn:
            conn.execute("DELETE FROM sync_log WHERE id = ?", (log_id,))

    def delete_sync_logs_before(self, table_name: str, before_date: str) -> None:
        """Delete old sync logs for a table (cleanup operation).

        Args:
            table_name: Name of the table.
            before_date: Delete logs completed before this ISO timestamp.
        """
        with self.transaction() as conn:
            conn.execute(
                """
                DELETE FROM sync_log
                WHERE table_name = ? AND completed_at < ?
                """,
                (table_name, before_date),
            )
