"""Unit tests for migration file validation."""

from __future__ import annotations

import re
import sqlite3
import tempfile
from pathlib import Path

import pytest

from petdata.modules.db.migrate import (
    _scan_migration_files,
    get_current_version,
    migrate,
)
from petdata.modules.db.schema import get_index_names, get_table_names

MIGRATIONS_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "petdata"
    / "modules"
    / "db"
    / "migrations"
)


class TestMigrationFiles:
    """Tests for migration file structure and naming."""

    def test_001_exists(self):
        """Migration 001_initial_schema.sql exists."""
        migration_001 = MIGRATIONS_DIR / "001_initial_schema.sql"
        assert migration_001.exists(), "001_initial_schema.sql must exist"

    def test_all_migrations_have_sequential_versions(self):
        """All migrations have sequential version numbers (no gaps)."""
        migrations = _scan_migration_files(MIGRATIONS_DIR)
        versions = [m.version for m in migrations]
        expected_versions = list(range(1, len(versions) + 1))
        assert versions == expected_versions

    def test_no_duplicate_versions(self):
        """No duplicate migration version numbers."""
        migrations = _scan_migration_files(MIGRATIONS_DIR)
        versions = [m.version for m in migrations]
        assert len(versions) == len(set(versions))

    def test_migrations_are_valid_sql(self):
        """All migration files contain valid SQL."""
        migrations = _scan_migration_files(MIGRATIONS_DIR)

        for migration in migrations:
            # Try to parse SQL in a temporary database
            with tempfile.NamedTemporaryFile(suffix=".db") as tmpfile:
                db_path = Path(tmpfile.name)

                try:
                    with sqlite3.connect(db_path) as conn:
                        conn.executescript(migration.sql)
                except sqlite3.Error as e:
                    pytest.fail(
                        f"Migration {migration.version} contains invalid SQL: {e}"
                    )

    def test_migrations_have_proper_headers(self):
        """All migrations have proper header comments."""
        required_headers = [
            (r"--\s*Migration:\s*\d+", "Migration"),
            (r"--\s*Description:", "Description"),
            (r"--\s*Dependencies:", "Dependencies"),
        ]

        for filepath in sorted(MIGRATIONS_DIR.glob("*.sql")):
            content = filepath.read_text()
            for pattern, header_name in required_headers:
                assert re.search(pattern, content), (
                    f"{filepath.name} missing {header_name} header"
                )


class TestMigration001:
    """Tests for migration 001_initial_schema.sql."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test.db"

    def test_creates_all_tables(self, temp_db: Path):
        """Migration 001 creates all expected tables."""
        migrate(temp_db)

        expected_tables = {
            "animals",
            "kennel_cards",
            "staff_assessments",
            "volunteer_notes",
            "walk_records",
            "sync_log",
            "animal_images",
            "schema_versions",  # Created by migration system
        }

        actual_tables = set(get_table_names(temp_db))
        assert actual_tables == expected_tables

    def test_creates_all_indexes(self, temp_db: Path):
        """Migration 001 creates all expected indexes."""
        migrate(temp_db)

        expected_indexes = {
            "idx_volunteer_notes_animal_date",
            "idx_volunteer_notes_date",
            "idx_animals_color_category",
            "idx_animals_last_synced",
            "idx_volunteer_notes_last_synced",
            "idx_kennel_cards_animal",
            "idx_staff_assessments_animal",
            "idx_walk_records_animal",
            "idx_animal_images_animal",
            "idx_sync_log_status",
        }

        actual_indexes = set(get_index_names(temp_db))
        assert actual_indexes == expected_indexes

    def test_creates_foreign_keys(self, temp_db: Path):
        """Migration 001 creates foreign key relationships."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert parent record
            conn.execute(
                """
                INSERT INTO animals (id, name)
                VALUES ('test-id', 'Test Animal')
                """
            )

            # Valid foreign key should work
            conn.execute(
                """
                INSERT INTO kennel_cards (animal_id)
                VALUES ('test-id')
                """
            )

            # Invalid foreign key should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO kennel_cards (animal_id)
                    VALUES ('nonexistent-id')
                    """
                )

    def test_creates_unique_constraints(self, temp_db: Path):
        """Migration 001 creates UNIQUE constraints."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            # Insert first record
            conn.execute(
                """
                INSERT INTO kennel_cards (animal_id)
                VALUES ('test-id')
                """
            )

            # Duplicate animal_id should fail (UNIQUE constraint)
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO kennel_cards (animal_id)
                    VALUES ('test-id')
                    """
                )

    def test_creates_check_constraints(self, temp_db: Path):
        """Migration 001 creates CHECK constraints."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            # Valid rating (0-5) should work
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                VALUES ('test-id', 'Test Volunteer', '2024-01-01', 3)
                """
            )

            # Invalid rating (>5) should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO volunteer_notes
                    (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                    VALUES ('test-id', 'Test Volunteer', '2024-01-01', 6)
                    """
                )

    def test_idempotent(self, temp_db: Path):
        """Migration 001 can be run multiple times safely."""
        # First application
        migrate(temp_db)
        version1 = get_current_version(temp_db)
        tables1 = set(get_table_names(temp_db))

        # Second application (should be no-op)
        migrate(temp_db)
        version2 = get_current_version(temp_db)
        tables2 = set(get_table_names(temp_db))

        assert version1 == version2
        assert tables1 == tables2

    def test_animals_table_structure(self, temp_db: Path):
        """Migration 001 creates animals table with correct columns."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("PRAGMA table_info(animals)")
            columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            "id",
            "name",
            "aka",
            "breed",
            "weight_lbs",
            "birth_date",
            "intake_date",
            "location",
            "color_category",
            "behavior_mod_tags",
            "is_in_kennel",
            "is_foster_care",
            "photo_url",
            "public_profile_url",
            "adalo_record_id",
            "created_at",
            "updated_at",
            "last_synced_at",
        }

        assert columns == expected_columns

    def test_volunteer_notes_table_structure(self, temp_db: Path):
        """Migration 001 creates volunteer_notes table with rating columns."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("PRAGMA table_info(volunteer_notes)")
            columns = {row[1] for row in cursor.fetchall()}

        expected_rating_columns = {
            "rating_strong_on_leash",
            "rating_leash_reactivity",
            "rating_shy_fearful",
            "rating_jumpy_mouthy",
        }

        assert expected_rating_columns.issubset(columns)

    def test_schema_versions_populated(self, temp_db: Path):
        """Migration 001 is recorded in schema_versions."""
        migrate(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT version, description FROM schema_versions WHERE version=1"
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == 1
            assert "initial" in row[1].lower()
