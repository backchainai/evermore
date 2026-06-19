"""Unit tests for repository helper functions."""

from __future__ import annotations

import pytest

from petdata.modules.db.repository import (
    _add_timestamps,
    _build_insert_sql,
    _build_update_sql,
    _build_upsert_sql,
)


class TestAddTimestamps:
    """Tests for _add_timestamps helper function."""

    def test_add_timestamps_includes_both(self):
        """_add_timestamps adds created_at and updated_at."""
        data = {"name": "test"}
        _add_timestamps(data)
        assert "created_at" in data
        assert "updated_at" in data
        assert data["name"] == "test"

    def test_add_timestamps_preserves_existing_created(self):
        """_add_timestamps preserves existing created_at."""
        timestamp = "2024-01-15T10:00:00"
        data = {"name": "test", "created_at": timestamp}
        _add_timestamps(data)
        assert data["created_at"] == timestamp
        assert "updated_at" in data

    def test_add_timestamps_preserves_existing_updated(self):
        """_add_timestamps preserves existing updated_at."""
        timestamp = "2024-01-15T10:00:00"
        data = {"name": "test", "updated_at": timestamp}
        _add_timestamps(data)
        assert "created_at" in data
        assert data["updated_at"] == timestamp

    def test_add_timestamps_update_only(self):
        """_add_timestamps can skip created_at for updates."""
        data = {"name": "test"}
        _add_timestamps(data, include_created=False)
        assert "created_at" not in data
        assert "updated_at" in data

    def test_add_timestamps_created_only(self):
        """_add_timestamps can skip updated_at for models without it."""
        data = {"name": "test"}
        _add_timestamps(data, include_updated=False)
        assert "created_at" in data
        assert "updated_at" not in data

    def test_add_timestamps_neither(self):
        """_add_timestamps can skip both timestamps."""
        data = {"name": "test"}
        _add_timestamps(data, include_created=False, include_updated=False)
        assert "created_at" not in data
        assert "updated_at" not in data
        assert data["name"] == "test"

    def test_add_timestamps_mutates_dict(self):
        """_add_timestamps mutates the input dict in place."""
        data = {"name": "test"}
        original_data = data
        _add_timestamps(data)
        assert data is original_data  # Same object
        assert "created_at" in data  # Original dict was mutated


class TestBuildInsertSql:
    """Tests for _build_insert_sql helper function."""

    def test_build_insert_sql_single_column(self):
        """_build_insert_sql handles single column."""
        data = {"name": "Buddy"}
        sql = _build_insert_sql("animals", data)
        assert sql == "INSERT INTO animals (name) VALUES (:name)"

    def test_build_insert_sql_multiple_columns(self):
        """_build_insert_sql handles multiple columns."""
        data = {"name": "Buddy", "breed": "Labrador", "weight_lbs": 65.5}
        sql = _build_insert_sql("animals", data)
        # Order should match dict order (Python 3.7+)
        assert "INSERT INTO animals" in sql
        assert "name" in sql
        assert "breed" in sql
        assert "weight_lbs" in sql
        assert ":name" in sql
        assert ":breed" in sql
        assert ":weight_lbs" in sql

    def test_build_insert_sql_empty_dict(self):
        """_build_insert_sql raises ValueError for empty dict."""
        data = {}
        with pytest.raises(ValueError, match="no data provided"):
            _build_insert_sql("animals", data)


class TestBuildUpdateSql:
    """Tests for _build_update_sql helper function."""

    def test_build_update_sql_single_column(self):
        """_build_update_sql handles single column update."""
        data = {"id": 1, "name": "Buddy"}
        sql = _build_update_sql("animals", data)
        assert sql == "UPDATE animals SET name = :name WHERE id = :id"

    def test_build_update_sql_multiple_columns(self):
        """_build_update_sql handles multiple columns."""
        data = {"id": 1, "name": "Buddy", "breed": "Labrador", "weight_lbs": 65.5}
        sql = _build_update_sql("animals", data)
        assert "UPDATE animals SET" in sql
        assert "name = :name" in sql
        assert "breed = :breed" in sql
        assert "weight_lbs = :weight_lbs" in sql
        assert "WHERE id = :id" in sql
        # Ensure id is not in SET clause
        assert sql.count("id = :id") == 1  # Only in WHERE

    def test_build_update_sql_custom_id_key(self):
        """_build_update_sql handles custom ID column name."""
        data = {"animal_id": "A-123", "name": "Buddy"}
        sql = _build_update_sql("volunteer_notes", data, id_key="animal_id")
        assert (
            sql
            == "UPDATE volunteer_notes SET name = :name WHERE animal_id = :animal_id"
        )

    def test_build_update_sql_id_only(self):
        """_build_update_sql raises ValueError when dict contains only ID."""
        data = {"id": 1}
        with pytest.raises(ValueError, match="no fields to update"):
            _build_update_sql("animals", data)


class TestBuildUpsertSql:
    """Tests for _build_upsert_sql helper function."""

    def test_build_upsert_sql_basic(self):
        """_build_upsert_sql handles basic upsert."""
        data = {"animal_id": "A-123", "about_text": "Friendly dog"}
        sql = _build_upsert_sql("kennel_cards", data, conflict_key="animal_id")
        assert "INSERT INTO kennel_cards" in sql
        assert "animal_id" in sql
        assert "about_text" in sql
        assert ":animal_id" in sql
        assert ":about_text" in sql
        assert "ON CONFLICT(animal_id)" in sql
        assert "DO UPDATE SET" in sql
        assert "about_text = excluded.about_text" in sql
        # Conflict key should not be in UPDATE clause
        assert "animal_id = excluded.animal_id" not in sql

    def test_build_upsert_sql_multiple_columns(self):
        """_build_upsert_sql handles multiple columns."""
        data = {
            "animal_id": "A-123",
            "about_text": "Friendly",
            "dogs_compatibility": "Good",
        }
        sql = _build_upsert_sql("kennel_cards", data, conflict_key="animal_id")
        assert "about_text = excluded.about_text" in sql
        assert "dogs_compatibility = excluded.dogs_compatibility" in sql
        # Only conflict key excluded from UPDATE
        assert sql.count("excluded") == 2
