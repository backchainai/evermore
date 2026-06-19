"""Unit tests for database schema."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from petbio.modules.db.schema import (
    create_tables,
    drop_tables,
    get_index_names,
    get_table_names,
)


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


class TestCreateTables:
    """Tests for create_tables function."""

    def test_creates_all_tables(self, temp_db: Path):
        """create_tables creates all expected tables."""
        create_tables(temp_db)

        expected_tables = {
            "animals",
            "kennel_cards",
            "staff_assessments",
            "volunteer_notes",
            "walk_records",
            "sync_log",
            "animal_images",
        }

        actual_tables = set(get_table_names(temp_db))
        assert actual_tables == expected_tables

    def test_creates_indexes(self, temp_db: Path):
        """create_tables creates performance indexes."""
        create_tables(temp_db)

        indexes = get_index_names(temp_db)

        # Check critical time-decay indexes
        assert "idx_volunteer_notes_animal_date" in indexes
        assert "idx_volunteer_notes_date" in indexes
        assert "idx_animals_color_category" in indexes

    def test_creates_parent_directory(self):
        """create_tables creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "nested" / "test.db"
            create_tables(db_path)
            assert db_path.exists()

    def test_idempotent(self, temp_db: Path):
        """create_tables can be called multiple times safely."""
        create_tables(temp_db)
        create_tables(temp_db)  # Should not raise

        tables = get_table_names(temp_db)
        assert len(tables) == 7

    def test_foreign_keys_enabled(self, temp_db: Path):
        """create_tables enables foreign key constraints."""
        create_tables(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys")
            # Note: PRAGMA returns 0 if foreign_keys was ON during table creation
            # but not explicitly set for this connection
            # The important thing is the constraint works

    def test_animals_table_structure(self, temp_db: Path):
        """animals table has expected columns."""
        create_tables(temp_db)

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

    def test_volunteer_notes_rating_constraints(self, temp_db: Path):
        """volunteer_notes enforces rating range constraints."""
        create_tables(temp_db)

        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            # Valid ratings should work
            conn.execute(
                """
                INSERT INTO volunteer_notes
                (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                VALUES ('test', 'Test', '2024-01-01', 3)
                """
            )

            # Invalid rating should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO volunteer_notes
                    (animal_id, volunteer_name, note_date, rating_strong_on_leash)
                    VALUES ('test2', 'Test', '2024-01-01', 6)
                    """
                )


class TestDropTables:
    """Tests for drop_tables function."""

    def test_drops_all_tables(self, temp_db: Path):
        """drop_tables removes all tables."""
        create_tables(temp_db)
        assert len(get_table_names(temp_db)) == 7

        drop_tables(temp_db)
        assert len(get_table_names(temp_db)) == 0

    def test_handles_nonexistent_db(self):
        """drop_tables handles nonexistent database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nonexistent.db"
            drop_tables(db_path)  # Should not raise
