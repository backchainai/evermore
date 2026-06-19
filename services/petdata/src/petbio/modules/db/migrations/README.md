# Database Migrations

This directory contains SQL migration files for evolving the petbio database schema.

## Overview

Migrations are numbered SQL files that apply schema changes incrementally. Each migration is tracked in the `schema_versions` table with checksums to detect tampering.

## Creating a New Migration

### 1. Determine Next Version Number

```bash
ls migrations/*.sql | sort -V | tail -1
```

The next version is one higher than the current maximum.

### 2. Create Migration File

File naming format: `{version:03d}_{description}.sql`

- **Version**: Zero-padded 3-digit integer (001, 002, 003...)
- **Description**: Snake_case brief description

Examples:
- `002_add_medical_records.sql`
- `003_add_adoption_status.sql`
- `004_add_behavior_tags_index.sql`

### 3. Write SQL with Idempotent Operations

Always use idempotent SQL to allow safe re-execution:

```sql
-- Migration: 002
-- Description: Add medical records table
-- Dependencies: 001

-- Tables
CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    record_date DATE NOT NULL,
    record_type TEXT NOT NULL,
    notes TEXT,
    veterinarian TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_medical_records_animal
    ON medical_records(animal_id);

CREATE INDEX IF NOT EXISTS idx_medical_records_date
    ON medical_records(record_date DESC);
```

**Required Header**:
- `Migration:` version number
- `Description:` brief summary
- `Dependencies:` prerequisite migration versions (or "None")

### 4. Test Migration

Test on a temporary database before committing:

```python
from pathlib import Path
from petbio.modules.db import migrate
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / "test.db"
    migrate(db_path)  # Should apply all migrations including new one
    print("Migration successful!")
```

### 5. Update Pydantic Models

If the migration adds/changes tables, update corresponding Pydantic models in `src/petbio/modules/db/models.py` to match the new schema.

## Migration Best Practices

### Idempotency
- **Always** use `CREATE TABLE IF NOT EXISTS`
- **Always** use `CREATE INDEX IF NOT EXISTS`
- **Never** use `CREATE TABLE` or `CREATE INDEX` without `IF NOT EXISTS`

### Immutability
- **Never** modify existing migration files after they're committed to git
- If you need to change schema, create a new migration that alters it
- Checksums prevent silent modification

### Testing
- Test migrations on a temporary database before committing
- Verify the migration can run multiple times safely
- Check that schema matches expectations using `PRAGMA table_info(table_name)`

### Documentation
- Document breaking changes in migration header comments
- Explain complex schema changes
- Reference related issues/tickets if applicable

### Transaction Safety
- Each migration runs in a single transaction
- If any statement fails, the entire migration rolls back
- Test complex migrations thoroughly

## Migration Workflow

### Fresh Install (New Database)
```python
from petbio.modules.db import init_database
from pathlib import Path

db_path = Path("data/petbio.db")
init_database(db_path)  # Applies all migrations
```

### Check Current Version
```python
from petbio.modules.db.migrate import get_current_version
from pathlib import Path

version = get_current_version(Path("data/petbio.db"))
print(f"Current schema version: {version}")
```

### Apply Pending Migrations
```python
from petbio.modules.db import migrate
from pathlib import Path

migrate(Path("data/petbio.db"))  # Applies all pending migrations
```

### Check Pending Migrations
```python
from petbio.modules.db.migrate import get_pending_migrations
from pathlib import Path

pending = get_pending_migrations(Path("data/petbio.db"))
print(f"Pending migrations: {[m.version for m in pending]}")
```

## Common Scenarios

### Adding a New Table
```sql
-- Migration: 00X
-- Description: Add table_name table
-- Dependencies: previous_version

CREATE TABLE IF NOT EXISTS table_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    -- other columns...
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_table_name_animal
    ON table_name(animal_id);
```

### Adding a Column (SQLite Limitation)
SQLite only supports `ADD COLUMN` (no `DROP COLUMN`, `MODIFY COLUMN`). For complex changes, create new table and migrate data:

```sql
-- Migration: 00X
-- Description: Add column to existing_table
-- Dependencies: previous_version

-- Simple case: just add column
ALTER TABLE existing_table ADD COLUMN new_column TEXT;

-- Complex case: recreate table
CREATE TABLE IF NOT EXISTS existing_table_new (
    -- full schema with changes
);

INSERT INTO existing_table_new SELECT * FROM existing_table;
DROP TABLE existing_table;
ALTER TABLE existing_table_new RENAME TO existing_table;
```

### Adding an Index
```sql
-- Migration: 00X
-- Description: Add performance index for common query
-- Dependencies: previous_version

CREATE INDEX IF NOT EXISTS idx_table_column
    ON table_name(column_name);
```

## Troubleshooting

### Migration Version Gap
```
MigrationGapError: Gap detected in migration version sequence
```
**Fix**: Ensure all migration versions are sequential (no missing numbers).

### Duplicate Version
```
MigrationDuplicateError: Duplicate migration version detected
```
**Fix**: Rename one migration file to use the next available version.

### Checksum Mismatch
```
MigrationValidationError: Migration X checksum mismatch
```
**Fix**: An applied migration file was modified. Revert the file to its original content or create a new migration with the desired changes.

### SQL Execution Error
```
MigrationExecutionError: Migration X failed
```
**Fix**: Check SQL syntax, table/column references, and constraints. Test migration on temporary database.

## Schema Versions Table

The migration system creates a `schema_versions` table to track applied migrations:

```sql
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT,
    execution_time_ms INTEGER
);
```

Query it directly to see migration history:
```sql
SELECT version, description, applied_at, execution_time_ms
FROM schema_versions
ORDER BY version;
```
