"""SQLite schema creation and management."""

from __future__ import annotations

import sqlite3
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

TABLES_SQL = """
-- Animals table
CREATE TABLE IF NOT EXISTS animals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aka TEXT,
    breed TEXT,
    weight_lbs REAL,
    birth_date DATE,
    intake_date DATE,
    location TEXT,
    color_category TEXT,
    behavior_mod_tags TEXT,
    is_in_kennel BOOLEAN,
    is_foster_care BOOLEAN,
    photo_url TEXT,
    public_profile_url TEXT,
    adalo_record_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Kennel card structured data
CREATE TABLE IF NOT EXISTS kennel_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    about_text TEXT,
    dogs_compatibility TEXT,
    dogs_compatibility_notes TEXT,
    cats_compatibility TEXT,
    cats_compatibility_notes TEXT,
    kids_compatibility TEXT,
    kids_compatibility_notes TEXT,
    commands_known TEXT,
    housebreaking_status TEXT,
    things_likes TEXT,
    things_dislikes TEXT,
    last_synced_at TIMESTAMP,
    UNIQUE(animal_id)
);

-- Staff behavioral assessments
CREATE TABLE IF NOT EXISTS staff_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    assessment_tags TEXT,
    notes TEXT,
    recorded_at TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Volunteer notes with ratings (CRITICAL for time-decay)
CREATE TABLE IF NOT EXISTS volunteer_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    adalo_record_id TEXT UNIQUE,
    volunteer_name TEXT NOT NULL,
    note_date TIMESTAMP NOT NULL,
    note_text TEXT,
    rating_strong_on_leash INTEGER CHECK (rating_strong_on_leash BETWEEN 0 AND 5),
    rating_leash_reactivity INTEGER CHECK (rating_leash_reactivity BETWEEN 0 AND 5),
    rating_shy_fearful INTEGER CHECK (rating_shy_fearful BETWEEN 0 AND 5),
    rating_jumpy_mouthy INTEGER CHECK (rating_jumpy_mouthy BETWEEN 0 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Walk records
CREATE TABLE IF NOT EXISTS walk_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    adalo_record_id TEXT UNIQUE,
    volunteer_name TEXT,
    out_time TIMESTAMP,
    in_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync tracking
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,
    table_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT
);

-- Animal images
CREATE TABLE IF NOT EXISTS animal_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    image_url TEXT NOT NULL,
    display_order INTEGER,
    last_synced_at TIMESTAMP
);
"""

INDEXES_SQL = """
-- Critical indexes for decay algorithm (Phase 2)
CREATE INDEX IF NOT EXISTS idx_volunteer_notes_animal_date
    ON volunteer_notes(animal_id, note_date DESC);

CREATE INDEX IF NOT EXISTS idx_volunteer_notes_date
    ON volunteer_notes(note_date DESC);

CREATE INDEX IF NOT EXISTS idx_animals_color_category
    ON animals(color_category);

CREATE INDEX IF NOT EXISTS idx_animals_last_synced
    ON animals(last_synced_at);

CREATE INDEX IF NOT EXISTS idx_volunteer_notes_last_synced
    ON volunteer_notes(last_synced_at);

-- Additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_kennel_cards_animal
    ON kennel_cards(animal_id);

CREATE INDEX IF NOT EXISTS idx_staff_assessments_animal
    ON staff_assessments(animal_id);

CREATE INDEX IF NOT EXISTS idx_walk_records_animal
    ON walk_records(animal_id);

CREATE INDEX IF NOT EXISTS idx_animal_images_animal
    ON animal_images(animal_id);

CREATE INDEX IF NOT EXISTS idx_sync_log_status
    ON sync_log(status, started_at DESC);
"""

DROP_TABLES_SQL = """
DROP TABLE IF EXISTS animal_images;
DROP TABLE IF EXISTS sync_log;
DROP TABLE IF EXISTS walk_records;
DROP TABLE IF EXISTS volunteer_notes;
DROP TABLE IF EXISTS staff_assessments;
DROP TABLE IF EXISTS kennel_cards;
DROP TABLE IF EXISTS animals;
"""


def create_tables(db_path: Path) -> None:
    """Create all database tables and indexes.

    .. deprecated::
        Use :func:`migrate` or :func:`init_database` instead.
        This function will be removed in a future version.

    Args:
        db_path: Path to the SQLite database file.
    """
    warnings.warn(
        "create_tables() is deprecated. Use migrate() or init_database() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(TABLES_SQL)
        conn.executescript(INDEXES_SQL)
        conn.commit()


def drop_tables(db_path: Path) -> None:
    """Drop all database tables.

    Args:
        db_path: Path to the SQLite database file.
    """
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(DROP_TABLES_SQL)
        conn.commit()


def get_table_names(db_path: Path) -> list[str]:
    """Get list of all table names in the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of table names.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]


def get_index_names(db_path: Path) -> list[str]:
    """Get list of all index names in the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of index names.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
