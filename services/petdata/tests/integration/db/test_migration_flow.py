"""Integration tests for end-to-end migration flow."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from petdata.modules.db import Database, init_database, migrate
from petdata.modules.db.migrate import get_current_version, get_pending_migrations
from petdata.modules.db.models import Animal
from petdata.modules.db.schema import get_table_names


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


class TestMigrationFlow:
    """End-to-end migration flow tests."""

    def test_fresh_install_applies_all(self, temp_db: Path):
        """Fresh install applies all migrations from scratch."""
        # Run migration on new database
        init_database(temp_db)

        # Verify database was created
        assert temp_db.exists()

        # Verify current version is latest
        version = get_current_version(temp_db)
        assert version >= 1

        # Verify no pending migrations
        pending = get_pending_migrations(temp_db)
        assert len(pending) == 0

        # Verify all expected tables exist
        tables = set(get_table_names(temp_db))
        assert "animals" in tables
        assert "kennel_cards" in tables
        assert "volunteer_notes" in tables
        assert "schema_versions" in tables

    def test_incremental_migration(self, temp_db: Path):
        """Migrations can be applied incrementally."""
        # Apply initial migration
        migrate(temp_db)
        initial_version = get_current_version(temp_db)

        # Running migrate again should be a no-op
        migrate(temp_db)
        final_version = get_current_version(temp_db)

        assert initial_version == final_version

    def test_database_usable_after_migration(self, temp_db: Path):
        """Database is fully usable after migration."""
        # Apply migrations
        init_database(temp_db)

        # Test that we can use the Database repository
        db = Database(temp_db)

        # Create an animal
        animal = Animal(
            id="test-001",
            name="Test Dog",
            aka=None,
            breed="Labrador",
            weight_lbs=65.5,
            birth_date=None,
            intake_date=None,
            location="Kennel A",
            color_category="yellow",
            behavior_mod_tags=None,
            is_in_kennel=True,
            is_foster_care=False,
            photo_url=None,
            public_profile_url=None,
            adalo_record_id=None,
            created_at=None,
            updated_at=None,
            last_synced_at=None,
        )

        # Insert animal
        db.insert_animal(animal)

        # Retrieve animal
        retrieved = db.get_animal("test-001")
        assert retrieved is not None
        assert retrieved.name == "Test Dog"
        assert retrieved.breed == "Labrador"

        # List animals
        all_animals = db.list_animals()
        assert len(all_animals) == 1

    def test_foreign_keys_work_after_migration(self, temp_db: Path):
        """Foreign key constraints work after migration."""
        init_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert parent record
            conn.execute(
                """
                INSERT INTO animals (id, name)
                VALUES ('dog-001', 'Test Dog')
                """
            )

            # Insert child record (should work)
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date)
                VALUES ('dog-001', 'Test Volunteer', '2024-01-01')
                """
            )

            # Try to insert child with invalid parent (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO volunteer_notes
                    (animal_id, volunteer_name, note_date)
                    VALUES ('nonexistent-dog', 'Test Volunteer', '2024-01-01')
                    """
                )

    def test_indexes_exist_after_migration(self, temp_db: Path):
        """All indexes are created after migration."""
        init_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """
            )
            indexes = {row[0] for row in cursor.fetchall()}

        # Check critical indexes exist
        assert "idx_volunteer_notes_animal_date" in indexes
        assert "idx_volunteer_notes_date" in indexes
        assert "idx_animals_color_category" in indexes

    def test_migrations_are_idempotent(self, temp_db: Path):
        """Running migrations multiple times is safe."""
        # First run
        migrate(temp_db)
        version1 = get_current_version(temp_db)

        # Insert test data
        with sqlite3.connect(temp_db) as conn:
            conn.execute(
                """
                INSERT INTO animals (id, name)
                VALUES ('dog-001', 'Test Dog')
                """
            )

        # Second run (should be no-op)
        migrate(temp_db)
        version2 = get_current_version(temp_db)

        # Version should be unchanged
        assert version1 == version2

        # Data should still exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM animals WHERE id='dog-001'")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "Test Dog"

    def test_schema_versions_table_populated(self, temp_db: Path):
        """schema_versions table is populated correctly."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                """
                SELECT version, description, checksum, execution_time_ms
                FROM schema_versions
                ORDER BY version
                """
            )
            rows = cursor.fetchall()

            # Should have at least one migration
            assert len(rows) >= 1

            # First migration should be version 1
            assert rows[0][0] == 1

            # Should have description
            assert rows[0][1]

            # Should have checksum
            assert rows[0][2]
            assert len(rows[0][2]) == 64  # SHA256 hex length

            # Should have execution time
            assert rows[0][3] is not None
            assert rows[0][3] >= 0

    def test_can_query_database_after_migration(self, temp_db: Path):
        """Can run complex queries after migration."""
        init_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            # Insert test data
            conn.execute(
                """
                INSERT INTO animals (id, name, color_category)
                VALUES ('dog-001', 'Yellow Dog', 'yellow')
                """
            )
            conn.execute(
                """
                INSERT INTO animals (id, name, color_category)
                VALUES ('dog-002', 'Red Dog', 'red')
                """
            )
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                VALUES ('dog-001', 'Volunteer 1', '2024-01-01', 3)
                """
            )
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                VALUES ('dog-001', 'Volunteer 2', '2024-01-02', 4)
                """
            )

            # Test join query with index
            cursor = conn.execute(
                """
                SELECT a.name, COUNT(vn.id) as note_count
                FROM animals a
                LEFT JOIN volunteer_notes vn ON a.id = vn.animal_id
                GROUP BY a.id
                ORDER BY a.name
                """
            )
            results = cursor.fetchall()

            assert len(results) == 2
            assert results[0][0] == "Red Dog"
            assert results[0][1] == 0
            assert results[1][0] == "Yellow Dog"
            assert results[1][1] == 2

    def test_rating_constraints_enforced(self, temp_db: Path):
        """Rating constraints are enforced after migration."""
        init_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            # Valid rating (0-5) should work
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                VALUES ('test-id', 'Test', '2024-01-01', 5)
                """
            )

            # Invalid rating should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO volunteer_notes
                    (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                    VALUES ('test-id', 'Test', '2024-01-01', 6)
                    """
                )

    def test_unique_constraints_enforced(self, temp_db: Path):
        """UNIQUE constraints are enforced after migration."""
        init_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            # First kennel card for animal
            conn.execute(
                """
                INSERT INTO kennel_cards (animal_id)
                VALUES ('test-id')
                """
            )

            # Duplicate kennel card should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO kennel_cards (animal_id)
                    VALUES ('test-id')
                    """
                )
