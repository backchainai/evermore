"""Database migration engine for petdata.

This module provides simple version-tracked migrations for SQLite schema evolution.
Migrations are numbered SQL files that apply schema changes incrementally.

Example:
    Initialize a new database:
        >>> from petdata.modules.db import init_database
        >>> init_database(Path("data/petdata.db"))

    Apply pending migrations:
        >>> from petdata.modules.db import migrate
        >>> migrate(Path("data/petdata.db"))

    Check current version:
        >>> from petdata.modules.db.migrate import get_current_version
        >>> version = get_current_version(Path("data/petdata.db"))
"""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

# Exception Hierarchy


class MigrationError(Exception):
    """Base exception for migration operations."""


class MigrationValidationError(MigrationError):
    """Migration file validation failed."""


class MigrationGapError(MigrationValidationError):
    """Gap detected in migration version sequence."""


class MigrationDuplicateError(MigrationValidationError):
    """Duplicate migration version detected."""


class MigrationExecutionError(MigrationError):
    """Migration SQL execution failed."""


# Migration Data Model


@dataclass(frozen=True)
class Migration:
    """Represents a database migration.

    Attributes:
        version: Migration version number (must be >= 1).
        description: Brief description of the migration.
        sql: SQL statements to execute.
        checksum: SHA256 checksum of the SQL content.
    """

    version: int
    description: str
    sql: str
    checksum: str

    def __post_init__(self) -> None:
        """Validate migration fields."""
        if self.version < 1:
            msg = f"Migration version must be >= 1, got {self.version}"
            raise ValueError(msg)
        if not self.description:
            msg = "Migration description cannot be empty"
            raise ValueError(msg)
        if not self.sql.strip():
            msg = "Migration SQL cannot be empty"
            raise ValueError(msg)


# SQL Parsing Utilities


def _split_sql_statements(sql: str) -> list[str]:
    """Split SQL into individual statements for transaction-safe execution.

    This is CRITICAL because executescript() implicitly commits, breaking
    transaction boundaries. We must split SQL and execute each statement
    individually within a single transaction.

    Args:
        sql: SQL content potentially containing multiple statements.

    Returns:
        List of individual SQL statements, with comments removed.

    Example:
        >>> sql = "CREATE TABLE foo (id INT); -- comment\\nCREATE INDEX idx ON foo(id);"
        >>> statements = _split_sql_statements(sql)
        >>> len(statements)
        2
    """
    # Remove single-line comments
    sql = re.sub(r"--[^\n]*", "", sql)

    # Remove multi-line comments using non-backtracking pattern
    sql = re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", sql)

    # Split on semicolons
    statements = [s.strip() for s in sql.split(";")]

    # Filter empty statements
    return [s for s in statements if s]


# Schema Versions Table


def _create_schema_versions_table(conn: sqlite3.Connection) -> None:
    """Create the schema_versions table if it doesn't exist.

    This table tracks all applied migrations with checksums and timing.

    Args:
        conn: Active database connection.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT,
            execution_time_ms INTEGER
        )
        """
    )


# Version Queries


def _schema_versions_exists(conn: sqlite3.Connection) -> bool:
    """Check if schema_versions table exists.

    Args:
        conn: Active database connection.

    Returns:
        True if schema_versions table exists.
    """
    cursor = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='schema_versions'
        """
    )
    return cursor.fetchone() is not None


def get_current_version(db_path: Path) -> int:
    """Get the current schema version of the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Current version number, or 0 if database is uninitialized.

    Example:
        >>> version = get_current_version(Path("data/petdata.db"))
        >>> print(f"Schema version: {version}")
    """
    if not db_path.exists():
        return 0

    with sqlite3.connect(db_path) as conn:
        if not _schema_versions_exists(conn):
            return 0

        cursor = conn.execute("SELECT MAX(version) FROM schema_versions")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0


# Migration File Scanning


def _scan_migration_files(migrations_dir: Path) -> Sequence[Migration]:
    """Scan migration directory and load all migration files.

    Validates:
    - Filename format matches {version:03d}_{description}.sql
    - No duplicate version numbers
    - No gaps in version sequence

    Args:
        migrations_dir: Directory containing migration SQL files.

    Returns:
        Sequence of Migration objects sorted by version.

    Raises:
        MigrationDuplicateError: If duplicate version numbers found.
        MigrationGapError: If gap detected in version sequence.
        MigrationValidationError: If filename format invalid.

    Example:
        >>> migrations = _scan_migration_files(Path("modules/db/migrations"))
        >>> print(f"Found {len(migrations)} migrations")
    """
    migration_files = sorted(migrations_dir.glob("*.sql"))
    migrations: list[Migration] = []
    versions_seen: set[int] = set()

    # Filename pattern: {version:03d}_{description}.sql
    pattern = re.compile(r"^(\d{3})_([a-z0-9_]+)\.sql$")

    for filepath in migration_files:
        match = pattern.match(filepath.name)
        if not match:
            msg = f"Invalid migration filename format: {filepath.name}"
            raise MigrationValidationError(msg)

        version = int(match.group(1))
        description = match.group(2).replace("_", " ")

        # Check for duplicates
        if version in versions_seen:
            msg = f"Duplicate migration version {version}: {filepath.name}"
            raise MigrationDuplicateError(msg)
        versions_seen.add(version)

        # Read SQL content
        sql = filepath.read_text(encoding="utf-8")

        # Calculate checksum
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

        migrations.append(
            Migration(
                version=version,
                description=description,
                sql=sql,
                checksum=checksum,
            )
        )

    # Validate no gaps in version sequence
    if migrations:
        expected_versions = set(range(1, len(migrations) + 1))
        actual_versions = {m.version for m in migrations}
        if actual_versions != expected_versions:
            missing = expected_versions - actual_versions
            msg = f"Gap detected in migration versions. Missing: {sorted(missing)}"
            raise MigrationGapError(msg)

    return migrations


# Migration Validation


def _validate_applied_migrations(
    db_path: Path, migrations: Sequence[Migration]
) -> None:
    """Validate that applied migrations match migration files.

    This is CRITICAL to detect if migration files were modified after
    application, which could cause silent schema corruption.

    Args:
        db_path: Path to the SQLite database file.
        migrations: All available migration objects.

    Raises:
        MigrationValidationError: If checksums don't match.

    Example:
        >>> migrations = _scan_migration_files(migrations_dir)
        >>> _validate_applied_migrations(db_path, migrations)
    """
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        if not _schema_versions_exists(conn):
            return

        cursor = conn.execute(
            "SELECT version, checksum FROM schema_versions WHERE checksum IS NOT NULL"
        )
        applied = {row[0]: row[1] for row in cursor.fetchall()}

        for migration in migrations:
            if migration.version not in applied:
                continue
            # Use constant-time comparison to prevent timing attacks
            if not secrets.compare_digest(
                applied[migration.version], migration.checksum
            ):
                msg = (
                    f"Migration {migration.version} checksum mismatch. "
                    f"Migration file was modified after application."
                )
                raise MigrationValidationError(msg)


# Pending Migrations


def get_pending_migrations(db_path: Path) -> list[Migration]:
    """Get all migrations that haven't been applied yet.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of pending Migration objects, sorted by version.

    Example:
        >>> pending = get_pending_migrations(Path("data/petdata.db"))
        >>> for migration in pending:
        ...     print(f"Pending: {migration.version} - {migration.description}")
    """
    current_version = get_current_version(db_path)

    # Find migrations directory relative to this file
    migrations_dir = Path(__file__).parent / "migrations"

    migrations = _scan_migration_files(migrations_dir)

    # Validate applied migrations haven't been tampered with
    _validate_applied_migrations(db_path, migrations)

    # Filter to pending only
    pending = [m for m in migrations if m.version > current_version]

    return sorted(pending, key=lambda m: m.version)


# Execution Timing


@contextmanager
def _measure_execution() -> Iterator[dict[str, int]]:
    """Context manager to measure execution time in milliseconds.

    Yields:
        Dictionary with 'ms' key that will be populated with execution time.

    Example:
        >>> with _measure_execution() as timing:
        ...     # do work
        ...     pass
        >>> print(f"Took {timing['ms']}ms")
    """
    timing: dict[str, int] = {"ms": 0}
    start_time = time.perf_counter()
    try:
        yield timing
    finally:
        end_time = time.perf_counter()
        timing["ms"] = int((end_time - start_time) * 1000)


# Migration Application


def apply_migration(db_path: Path, migration: Migration) -> None:
    """Apply a single migration to the database.

    CRITICAL: Uses context manager + execute() for proper transaction handling.
    Does NOT use executescript() which would implicitly commit.

    Args:
        db_path: Path to the SQLite database file.
        migration: Migration object to apply.

    Raises:
        MigrationExecutionError: If SQL execution fails.

    Example:
        >>> migration = Migration(
        ...     version=1, description="initial", sql="...", checksum="..."
        ... )
        >>> apply_migration(Path("data/petdata.db"), migration)
    """
    # Create parent directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        # Enable foreign keys and verify support
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute("PRAGMA foreign_keys")
        if cursor.fetchone()[0] != 1:
            msg = "SQLite was compiled without foreign key support"
            raise MigrationExecutionError(msg)

        # Ensure schema_versions table exists
        _create_schema_versions_table(conn)

        # Split SQL into statements for transaction safety
        statements = _split_sql_statements(migration.sql)

        # Execute migration SQL with timing
        try:
            with _measure_execution() as timing:
                for statement in statements:
                    conn.execute(statement)
        except sqlite3.Error as e:
            msg = (
                f"Migration {migration.version} SQL execution failed: "
                f"{type(e).__name__}: {e}"
            )
            raise MigrationExecutionError(msg) from e

        # Record migration in schema_versions
        try:
            conn.execute(
                """
                INSERT INTO schema_versions
                (version, description, checksum, execution_time_ms)
                VALUES (?, ?, ?, ?)
                """,
                (
                    migration.version,
                    migration.description,
                    migration.checksum,
                    timing["ms"],
                ),
            )
        except sqlite3.Error as e:
            msg = (
                f"Migration {migration.version} succeeded but failed to record: "
                f"{type(e).__name__}: {e}"
            )
            raise MigrationExecutionError(msg) from e

        # Commit happens automatically when exiting context manager


# Main Migration Entry Point


def migrate(db_path: Path, target_version: int | None = None) -> None:
    """Apply all pending migrations to the database.

    This is the main entry point for applying migrations. It:
    1. Scans migration files
    2. Validates applied migrations (checksum verification)
    3. Applies pending migrations in order
    4. Stops at target_version if specified

    Args:
        db_path: Path to the SQLite database file.
        target_version: Optional version to migrate to (applies all if None).

    Raises:
        MigrationError: If migration validation or execution fails.

    Example:
        >>> # Apply all pending migrations
        >>> migrate(Path("data/petdata.db"))
        >>>
        >>> # Apply up to version 3
        >>> migrate(Path("data/petdata.db"), target_version=3)
    """
    # Create parent directories if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Get pending migrations (includes validation)
    pending = get_pending_migrations(db_path)

    # Filter to target version if specified
    if target_version is not None:
        pending = [m for m in pending if m.version <= target_version]

    # Apply each migration
    for migration in pending:
        apply_migration(db_path, migration)


# Convenience Alias


def init_database(db_path: Path) -> None:
    """Initialize a new database by applying all migrations.

    This is an alias for migrate() that makes intent clearer for fresh installs.

    Args:
        db_path: Path to the SQLite database file.

    Example:
        >>> init_database(Path("data/petdata.db"))
    """
    migrate(db_path)
