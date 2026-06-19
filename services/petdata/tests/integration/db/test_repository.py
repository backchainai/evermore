"""Integration tests for database repository."""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

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
from petdata.modules.db.schema import create_tables


@pytest.fixture
def db() -> Database:
    """Create a temporary database with schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        create_tables(db_path)
        yield Database(db_path)


@pytest.fixture
def sample_animal() -> Animal:
    """Create a sample animal for testing."""
    return Animal(
        id="A-55833",
        name="Buddy",
        breed="Labrador",
        weight_lbs=65.5,
        color_category="Green",
        is_in_kennel=True,
    )


class TestAnimalOperations:
    """Tests for animal CRUD operations."""

    def test_insert_and_get_animal(self, db: Database, sample_animal: Animal):
        """Can insert and retrieve an animal."""
        db.insert_animal(sample_animal)

        retrieved = db.get_animal("A-55833")
        assert retrieved is not None
        assert retrieved.id == "A-55833"
        assert retrieved.name == "Buddy"
        assert retrieved.breed == "Labrador"
        assert retrieved.weight_lbs == 65.5

    def test_get_nonexistent_animal(self, db: Database):
        """get_animal returns None for missing animal."""
        retrieved = db.get_animal("NONEXISTENT")
        assert retrieved is None

    def test_update_animal(self, db: Database, sample_animal: Animal):
        """Can update an existing animal."""
        db.insert_animal(sample_animal)

        sample_animal.weight_lbs = 70.0
        sample_animal.location = "Line 5, 5H"
        db.update_animal(sample_animal)

        retrieved = db.get_animal("A-55833")
        assert retrieved is not None
        assert retrieved.weight_lbs == 70.0
        assert retrieved.location == "Line 5, 5H"

    def test_list_animals(self, db: Database):
        """Can list animals with pagination."""
        for i in range(5):
            animal = Animal(id=f"A-{i:05d}", name=f"Dog {i}")
            db.insert_animal(animal)

        animals = db.list_animals(limit=3)
        assert len(animals) == 3

        all_animals = db.list_animals(limit=10)
        assert len(all_animals) == 5

    def test_roundtrip_behavior_tags(self, db: Database):
        """Tags roundtrip through database correctly."""
        animal = Animal(
            id="A-99999",
            name="Test Dog",
            behavior_mod_tags=["Shy", "Reactive", "Good with Dogs"],
        )
        db.insert_animal(animal)

        retrieved = db.get_animal("A-99999")
        assert retrieved is not None
        assert retrieved.behavior_mod_tags == ["Shy", "Reactive", "Good with Dogs"]

        # Update with new tags
        retrieved.behavior_mod_tags = ["Friendly", "Energetic"]
        db.update_animal(retrieved)

        updated = db.get_animal("A-99999")
        assert updated is not None
        assert updated.behavior_mod_tags == ["Friendly", "Energetic"]


class TestVolunteerNoteOperations:
    """Tests for volunteer note CRUD operations."""

    def test_insert_and_get_notes(self, db: Database, sample_animal: Animal):
        """Can insert and retrieve volunteer notes."""
        db.insert_animal(sample_animal)

        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
            note_text="Great walk today!",
            rating_strong_on_leash=4,
            rating_leash_reactivity=2,
        )
        note_id = db.insert_volunteer_note(note)
        assert note_id > 0

        notes = db.get_notes_for_animal("A-55833")
        assert len(notes) == 1
        assert notes[0].volunteer_name == "Chris"
        assert notes[0].rating_strong_on_leash == 4

    def test_notes_ordered_by_date_desc(self, db: Database, sample_animal: Animal):
        """Notes are returned most recent first."""
        db.insert_animal(sample_animal)

        for i in range(3):
            note = VolunteerNote(
                animal_id="A-55833",
                volunteer_name=f"Volunteer {i}",
                note_date=f"2024-12-{20 + i:02d}T10:00:00",
            )
            db.insert_volunteer_note(note)

        notes = db.get_notes_for_animal("A-55833")
        assert notes[0].note_date == "2024-12-22T10:00:00"  # Most recent
        assert notes[2].note_date == "2024-12-20T10:00:00"  # Oldest

    def test_foreign_key_constraint(self, db: Database):
        """Cannot insert note for nonexistent animal."""
        note = VolunteerNote(
            animal_id="NONEXISTENT",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_volunteer_note(note)


class TestKennelCardOperations:
    """Tests for kennel card CRUD operations."""

    def test_upsert_creates_card(self, db: Database, sample_animal: Animal):
        """upsert_kennel_card creates new card."""
        db.insert_animal(sample_animal)

        card = KennelCard(
            animal_id="A-55833",
            about_text="Friendly dog",
            dogs_compatibility="Good",
        )
        card_id = db.upsert_kennel_card(card)
        assert card_id > 0

        retrieved = db.get_kennel_card("A-55833")
        assert retrieved is not None
        assert retrieved.about_text == "Friendly dog"

    def test_upsert_updates_existing_card(self, db: Database, sample_animal: Animal):
        """upsert_kennel_card updates existing card."""
        db.insert_animal(sample_animal)

        card1 = KennelCard(animal_id="A-55833", about_text="Version 1")
        db.upsert_kennel_card(card1)

        card2 = KennelCard(animal_id="A-55833", about_text="Version 2")
        db.upsert_kennel_card(card2)

        retrieved = db.get_kennel_card("A-55833")
        assert retrieved is not None
        assert retrieved.about_text == "Version 2"


class TestStaffAssessmentOperations:
    """Tests for staff assessment operations."""

    def test_insert_and_get_assessments(self, db: Database, sample_animal: Animal):
        """Can insert and retrieve staff assessments."""
        db.insert_animal(sample_animal)

        assessment = StaffAssessment(
            animal_id="A-55833",
            assessment_tags=["Cat Test Complete"],
            notes="Passed all tests",
            recorded_at="2024-12-01T10:00:00",
        )
        assessment_id = db.insert_staff_assessment(assessment)
        assert assessment_id > 0

        assessments = db.get_assessments_for_animal("A-55833")
        assert len(assessments) == 1
        assert "Cat Test Complete" in assessments[0].assessment_tags


class TestWalkRecordOperations:
    """Tests for walk record operations."""

    def test_insert_and_get_walks(self, db: Database, sample_animal: Animal):
        """Can insert and retrieve walk records."""
        db.insert_animal(sample_animal)

        record = WalkRecord(
            animal_id="A-55833",
            volunteer_name="Chris",
            out_time="2024-12-23T14:00:00",
            in_time="2024-12-23T14:45:00",
        )
        record_id = db.insert_walk_record(record)
        assert record_id > 0

        walks = db.get_walks_for_animal("A-55833")
        assert len(walks) == 1
        assert walks[0].volunteer_name == "Chris"


class TestAnimalImageOperations:
    """Tests for animal image operations."""

    def test_insert_and_get_images(self, db: Database, sample_animal: Animal):
        """Can insert and retrieve animal images."""
        db.insert_animal(sample_animal)

        image = AnimalImage(
            animal_id="A-55833",
            image_url="https://example.com/photo.jpg",
            display_order=1,
        )
        image_id = db.insert_animal_image(image)
        assert image_id > 0

        images = db.get_images_for_animal("A-55833")
        assert len(images) == 1
        assert images[0].display_order == 1


class TestSyncLogOperations:
    """Tests for sync log operations."""

    def test_insert_and_update_sync_log(self, db: Database):
        """Can insert and update sync log."""
        log = SyncLog(
            sync_type="full",
            table_name="animals",
            started_at=datetime.now().isoformat(),
            status="running",
        )
        log_id = db.insert_sync_log(log)
        assert log_id > 0

        log.id = log_id
        log.status = "completed"
        log.records_processed = 100
        log.records_created = 100
        log.completed_at = datetime.now().isoformat()
        db.update_sync_log(log)

        latest = db.get_latest_sync("animals")
        assert latest is not None
        assert latest.status == "completed"
        assert latest.records_processed == 100

    def test_get_latest_sync_returns_most_recent(self, db: Database):
        """get_latest_sync returns most recent completed sync."""
        for i in range(3):
            log = SyncLog(
                sync_type="incremental",
                table_name="volunteer_notes",
                started_at=f"2024-12-{20 + i:02d}T10:00:00",
                completed_at=f"2024-12-{20 + i:02d}T10:05:00",
                status="completed",
                records_processed=i * 10,
            )
            db.insert_sync_log(log)

        latest = db.get_latest_sync("volunteer_notes")
        assert latest is not None
        assert latest.records_processed == 20  # From the most recent


class TestTransactions:
    """Tests for transaction handling."""

    def test_transaction_rollback_on_error(self, db: Database, sample_animal: Animal):
        """Transaction rolls back on error."""
        db.insert_animal(sample_animal)

        # Try to insert with invalid foreign key - should fail and rollback
        note = VolunteerNote(
            animal_id="NONEXISTENT",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.insert_volunteer_note(note)

        # Original animal should still exist (not affected by rollback)
        animal = db.get_animal("A-55833")
        assert animal is not None


class TestUniqueConstraints:
    """Tests for unique constraint enforcement."""

    def test_adalo_record_id_unique_in_notes(self, db: Database, sample_animal: Animal):
        """adalo_record_id must be unique in volunteer_notes."""
        db.insert_animal(sample_animal)

        note1 = VolunteerNote(
            animal_id="A-55833",
            adalo_record_id="unique123",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        db.insert_volunteer_note(note1)

        note2 = VolunteerNote(
            animal_id="A-55833",
            adalo_record_id="unique123",  # Duplicate
            volunteer_name="Other",
            note_date="2024-12-24T17:37:00",
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_volunteer_note(note2)


class TestUpdateOperations:
    """Tests for update operations on all models."""

    def test_update_volunteer_note(self, db: Database, sample_animal: Animal):
        """Can update an existing volunteer note."""
        db.insert_animal(sample_animal)

        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
            note_text="Initial note",
            rating_strong_on_leash=3,
        )
        note_id = db.insert_volunteer_note(note)

        # Update the note
        note.id = note_id
        note.note_text = "Updated note"
        note.rating_strong_on_leash = 5
        db.update_volunteer_note(note)

        # Verify update
        retrieved = db.get_volunteer_note_by_id(note_id)
        assert retrieved is not None
        assert retrieved.note_text == "Updated note"
        assert retrieved.rating_strong_on_leash == 5

    def test_update_volunteer_note_without_id_raises_error(self, db: Database):
        """Updating a volunteer note without ID raises ValueError."""
        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )

        with pytest.raises(ValueError, match="Cannot update volunteer note without ID"):
            db.update_volunteer_note(note)

    def test_update_staff_assessment(self, db: Database, sample_animal: Animal):
        """Can update an existing staff assessment."""
        db.insert_animal(sample_animal)

        assessment = StaffAssessment(
            animal_id="A-55833",
            recorded_at="2024-12-23T17:37:00",
            notes="Initial assessment",
        )
        assessment_id = db.insert_staff_assessment(assessment)

        # Update the assessment
        assessment.id = assessment_id
        assessment.notes = "Updated assessment"
        db.update_staff_assessment(assessment)

        # Verify update
        retrieved = db.get_staff_assessment_by_id(assessment_id)
        assert retrieved is not None
        assert retrieved.notes == "Updated assessment"

    def test_update_staff_assessment_without_id_raises_error(self, db: Database):
        """Updating a staff assessment without ID raises ValueError."""
        assessment = StaffAssessment(
            animal_id="A-55833", recorded_at="2024-12-23T17:37:00"
        )

        with pytest.raises(
            ValueError, match="Cannot update staff assessment without ID"
        ):
            db.update_staff_assessment(assessment)

    def test_update_walk_record(self, db: Database, sample_animal: Animal):
        """Can update an existing walk record."""
        db.insert_animal(sample_animal)

        record = WalkRecord(
            animal_id="A-55833",
            volunteer_name="Chris",
            out_time="2024-12-23T10:00:00",
        )
        record_id = db.insert_walk_record(record)

        # Update with in_time (common use case - checking back in)
        record.id = record_id
        record.in_time = "2024-12-23T10:30:00"
        db.update_walk_record(record)

        # Verify update
        retrieved = db.get_walk_record_by_id(record_id)
        assert retrieved is not None
        assert retrieved.in_time == "2024-12-23T10:30:00"

    def test_update_walk_record_without_id_raises_error(self, db: Database):
        """Updating a walk record without ID raises ValueError."""
        record = WalkRecord(
            animal_id="A-55833",
            volunteer_name="Chris",
            out_time="2024-12-23T10:00:00",
        )

        with pytest.raises(ValueError, match="Cannot update walk record without ID"):
            db.update_walk_record(record)

    def test_update_animal_image(self, db: Database, sample_animal: Animal):
        """Can update an existing animal image."""
        db.insert_animal(sample_animal)

        image = AnimalImage(
            animal_id="A-55833",
            image_url="https://example.com/image1.jpg",
            display_order=1,
        )
        image_id = db.insert_animal_image(image)

        # Update the image
        image.id = image_id
        image.display_order = 2
        image.image_url = "https://example.com/image2.jpg"
        db.update_animal_image(image)

        # Verify update
        retrieved = db.get_animal_image_by_id(image_id)
        assert retrieved is not None
        assert retrieved.display_order == 2
        assert retrieved.image_url == "https://example.com/image2.jpg"

    def test_update_animal_image_without_id_raises_error(self, db: Database):
        """Updating an animal image without ID raises ValueError."""
        image = AnimalImage(
            animal_id="A-55833", image_url="https://example.com/image1.jpg"
        )

        with pytest.raises(ValueError, match="Cannot update animal image without ID"):
            db.update_animal_image(image)


class TestDeleteOperations:
    """Tests for delete operations and cascade behavior."""

    def test_delete_notes_for_animal(self, db: Database, sample_animal: Animal):
        """Can delete all volunteer notes for an animal."""
        db.insert_animal(sample_animal)

        # Insert multiple notes
        for i in range(3):
            note = VolunteerNote(
                animal_id="A-55833",
                volunteer_name=f"Volunteer {i}",
                note_date="2024-12-23T17:37:00",
            )
            db.insert_volunteer_note(note)

        # Delete all notes
        db.delete_notes_for_animal("A-55833")

        # Verify deletion
        notes = db.get_notes_for_animal("A-55833")
        assert len(notes) == 0

    def test_delete_assessments_for_animal(self, db: Database, sample_animal: Animal):
        """Can delete all staff assessments for an animal."""
        db.insert_animal(sample_animal)

        # Insert multiple assessments
        for _i in range(2):
            assessment = StaffAssessment(
                animal_id="A-55833", recorded_at="2024-12-23T17:37:00"
            )
            db.insert_staff_assessment(assessment)

        # Delete all assessments
        db.delete_assessments_for_animal("A-55833")

        # Verify deletion
        assessments = db.get_assessments_for_animal("A-55833")
        assert len(assessments) == 0

    def test_delete_walks_for_animal(self, db: Database, sample_animal: Animal):
        """Can delete all walk records for an animal."""
        db.insert_animal(sample_animal)

        # Insert multiple walk records
        for i in range(3):
            record = WalkRecord(
                animal_id="A-55833",
                volunteer_name=f"Volunteer {i}",
                out_time="2024-12-23T10:00:00",
            )
            db.insert_walk_record(record)

        # Delete all walks
        db.delete_walks_for_animal("A-55833")

        # Verify deletion
        walks = db.get_walks_for_animal("A-55833")
        assert len(walks) == 0

    def test_delete_images_for_animal(self, db: Database, sample_animal: Animal):
        """Can delete all images for an animal."""
        db.insert_animal(sample_animal)

        # Insert multiple images
        for i in range(2):
            image = AnimalImage(
                animal_id="A-55833",
                image_url=f"https://example.com/image{i}.jpg",
                display_order=i,
            )
            db.insert_animal_image(image)

        # Delete all images
        db.delete_images_for_animal("A-55833")

        # Verify deletion
        images = db.get_images_for_animal("A-55833")
        assert len(images) == 0

    def test_delete_kennel_card_for_animal(self, db: Database, sample_animal: Animal):
        """Can delete kennel card for an animal."""
        db.insert_animal(sample_animal)

        card = KennelCard(animal_id="A-55833", about_text="Friendly dog")
        db.upsert_kennel_card(card)

        # Delete kennel card
        db.delete_kennel_card_for_animal("A-55833")

        # Verify deletion
        card = db.get_kennel_card("A-55833")
        assert card is None

    def test_delete_animal_cascades_to_all_related_records(
        self, db: Database, sample_animal: Animal
    ):
        """Delete animal auto-cascades to all related records."""
        db.insert_animal(sample_animal)

        # Insert related records
        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        db.insert_volunteer_note(note)

        assessment = StaffAssessment(
            animal_id="A-55833", recorded_at="2024-12-23T17:37:00"
        )
        db.insert_staff_assessment(assessment)

        record = WalkRecord(
            animal_id="A-55833",
            volunteer_name="Chris",
            out_time="2024-12-23T10:00:00",
        )
        db.insert_walk_record(record)

        image = AnimalImage(
            animal_id="A-55833", image_url="https://example.com/image.jpg"
        )
        db.insert_animal_image(image)

        card = KennelCard(animal_id="A-55833", about_text="Friendly")
        db.upsert_kennel_card(card)

        # Delete animal (should cascade)
        db.delete_animal("A-55833")

        # Verify all related records are deleted
        assert db.get_animal("A-55833") is None
        assert len(db.get_notes_for_animal("A-55833")) == 0
        assert len(db.get_assessments_for_animal("A-55833")) == 0
        assert len(db.get_walks_for_animal("A-55833")) == 0
        assert len(db.get_images_for_animal("A-55833")) == 0
        assert db.get_kennel_card("A-55833") is None

    def test_delete_animal_transaction_atomicity(
        self, db: Database, sample_animal: Animal
    ):
        """Delete animal uses single transaction for atomicity."""
        db.insert_animal(sample_animal)

        # Insert related records
        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        db.insert_volunteer_note(note)

        # Delete should succeed atomically
        db.delete_animal("A-55833")

        # Both animal and note should be gone
        assert db.get_animal("A-55833") is None
        assert len(db.get_notes_for_animal("A-55833")) == 0

    def test_delete_sync_log(self, db: Database):
        """Can delete a sync log entry."""
        log = SyncLog(
            table_name="animals",
            sync_type="full",
            status="completed",
            started_at="2024-12-23T10:00:00",
        )
        log_id = db.insert_sync_log(log)

        # Delete the log
        db.delete_sync_log(log_id)

        # Verify deletion (should return None since completed log is gone)
        latest = db.get_latest_sync("animals")
        assert latest is None

    def test_delete_sync_logs_before(self, db: Database):
        """Can delete old sync logs for cleanup."""
        # Insert multiple logs with different timestamps
        log1 = SyncLog(
            table_name="animals",
            sync_type="full",
            status="completed",
            started_at="2024-12-20T10:00:00",
            completed_at="2024-12-20T10:05:00",
        )
        db.insert_sync_log(log1)

        log2 = SyncLog(
            table_name="animals",
            sync_type="full",
            status="completed",
            started_at="2024-12-23T10:00:00",
            completed_at="2024-12-23T10:05:00",
        )
        db.insert_sync_log(log2)

        # Delete logs before 2024-12-22
        db.delete_sync_logs_before("animals", "2024-12-22T00:00:00")

        # Only the newer log should remain
        latest = db.get_latest_sync("animals")
        assert latest is not None
        assert latest.completed_at == "2024-12-23T10:05:00"


class TestGetByIdOperations:
    """Tests for get_*_by_id() methods."""

    def test_get_volunteer_note_by_id(self, db: Database, sample_animal: Animal):
        """Can get volunteer note by ID."""
        db.insert_animal(sample_animal)

        note = VolunteerNote(
            animal_id="A-55833",
            volunteer_name="Chris",
            note_date="2024-12-23T17:37:00",
        )
        note_id = db.insert_volunteer_note(note)

        retrieved = db.get_volunteer_note_by_id(note_id)
        assert retrieved is not None
        assert retrieved.id == note_id
        assert retrieved.volunteer_name == "Chris"

    def test_get_volunteer_note_by_id_not_found(self, db: Database):
        """Returns None when volunteer note not found."""
        retrieved = db.get_volunteer_note_by_id(9999)
        assert retrieved is None

    def test_get_kennel_card_by_id(self, db: Database, sample_animal: Animal):
        """Can get kennel card by ID."""
        db.insert_animal(sample_animal)

        card = KennelCard(animal_id="A-55833", about_text="Friendly dog")
        card_id = db.upsert_kennel_card(card)

        retrieved = db.get_kennel_card_by_id(card_id)
        assert retrieved is not None
        assert retrieved.id == card_id
        assert retrieved.about_text == "Friendly dog"

    def test_get_kennel_card_by_id_not_found(self, db: Database):
        """Returns None when kennel card not found."""
        retrieved = db.get_kennel_card_by_id(9999)
        assert retrieved is None

    def test_get_staff_assessment_by_id(self, db: Database, sample_animal: Animal):
        """Can get staff assessment by ID."""
        db.insert_animal(sample_animal)

        assessment = StaffAssessment(
            animal_id="A-55833",
            recorded_at="2024-12-23T17:37:00",
            notes="Assessment notes",
        )
        assessment_id = db.insert_staff_assessment(assessment)

        retrieved = db.get_staff_assessment_by_id(assessment_id)
        assert retrieved is not None
        assert retrieved.id == assessment_id
        assert retrieved.notes == "Assessment notes"

    def test_get_staff_assessment_by_id_not_found(self, db: Database):
        """Returns None when staff assessment not found."""
        retrieved = db.get_staff_assessment_by_id(9999)
        assert retrieved is None

    def test_get_walk_record_by_id(self, db: Database, sample_animal: Animal):
        """Can get walk record by ID."""
        db.insert_animal(sample_animal)

        record = WalkRecord(
            animal_id="A-55833",
            volunteer_name="Chris",
            out_time="2024-12-23T10:00:00",
        )
        record_id = db.insert_walk_record(record)

        retrieved = db.get_walk_record_by_id(record_id)
        assert retrieved is not None
        assert retrieved.id == record_id
        assert retrieved.volunteer_name == "Chris"

    def test_get_walk_record_by_id_not_found(self, db: Database):
        """Returns None when walk record not found."""
        retrieved = db.get_walk_record_by_id(9999)
        assert retrieved is None

    def test_get_animal_image_by_id(self, db: Database, sample_animal: Animal):
        """Can get animal image by ID."""
        db.insert_animal(sample_animal)

        image = AnimalImage(
            animal_id="A-55833",
            image_url="https://example.com/image.jpg",
            display_order=1,
        )
        image_id = db.insert_animal_image(image)

        retrieved = db.get_animal_image_by_id(image_id)
        assert retrieved is not None
        assert retrieved.id == image_id
        assert retrieved.image_url == "https://example.com/image.jpg"

    def test_get_animal_image_by_id_not_found(self, db: Database):
        """Returns None when animal image not found."""
        retrieved = db.get_animal_image_by_id(9999)
        assert retrieved is None
