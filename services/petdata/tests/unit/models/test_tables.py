"""Unit tests for the ORM table metadata.

These assert the translated schema's structural properties without needing a
live database: table namespacing, tenant columns, timestamptz, JSONB, and the
preserved decay-critical indexes.
"""

from __future__ import annotations

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB

from petdata.models.base import Base
from petdata.models.tables import TENANT_OWNED_TABLES

_EXPECTED_TABLES = {
    "petdata_animals",
    "petdata_kennel_cards",
    "petdata_volunteer_notes",
    "petdata_staff_assessments",
    "petdata_walk_records",
    "petdata_animal_images",
    "petdata_sync_log",
}

_EXPECTED_INDEXES = {
    "idx_animals_color_category",
    "idx_animals_last_synced",
    "idx_kennel_cards_animal",
    "idx_volunteer_notes_animal_date",
    "idx_volunteer_notes_date",
    "idx_volunteer_notes_last_synced",
    "idx_staff_assessments_animal",
    "idx_walk_records_animal",
    "idx_animal_images_animal",
    "idx_sync_log_status",
}


def test_all_seven_tables_present_and_prefixed() -> None:
    assert set(Base.metadata.tables) == _EXPECTED_TABLES


def test_every_table_is_tenant_owned() -> None:
    assert set(TENANT_OWNED_TABLES) == _EXPECTED_TABLES


def test_every_table_has_tenant_id() -> None:
    for name, table in Base.metadata.tables.items():
        assert "tenant_id" in table.columns, f"{name} missing tenant_id"
        assert not table.columns["tenant_id"].nullable, f"{name}.tenant_id nullable"


def test_expected_indexes_present() -> None:
    found = {
        index.name for table in Base.metadata.tables.values() for index in table.indexes
    }
    assert found >= _EXPECTED_INDEXES


def test_decay_critical_indexes_on_volunteer_notes() -> None:
    notes = Base.metadata.tables["petdata_volunteer_notes"]
    index_names = {index.name for index in notes.indexes}
    assert "idx_volunteer_notes_animal_date" in index_names
    assert "idx_volunteer_notes_date" in index_names


def test_timestamp_columns_are_timezone_aware() -> None:
    animals = Base.metadata.tables["petdata_animals"]
    for col_name in ("created_at", "updated_at", "last_synced_at"):
        col = animals.columns[col_name]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True


def test_tag_columns_are_jsonb() -> None:
    animals = Base.metadata.tables["petdata_animals"]
    assert isinstance(animals.columns["behavior_mod_tags"].type, JSONB)
    assessments = Base.metadata.tables["petdata_staff_assessments"]
    assert isinstance(assessments.columns["assessment_tags"].type, JSONB)


def test_animal_child_foreign_keys_cascade() -> None:
    for name in (
        "petdata_kennel_cards",
        "petdata_volunteer_notes",
        "petdata_staff_assessments",
        "petdata_walk_records",
        "petdata_animal_images",
    ):
        table = Base.metadata.tables[name]
        fks = list(table.columns["animal_id"].foreign_keys)
        assert fks, f"{name}.animal_id has no foreign key"
        assert fks[0].ondelete == "CASCADE"
