# petbio

## Repository Overview

petbio is an automated adoption profile generator for animal shelters, built for Friends of Homeless Animals (FOHA). The project extracts animal data from shelter management systems, analyzes behavioral trends using time-decay algorithms, and generates evidence-based adoption profiles using LLMs.

**Current Phase:** Phase 1 complete (data extraction and storage)
**Next Phase:** Time-decay behavioral analysis

## Project Status

### Phase 1: Data Extraction (✓ Complete)

- 7 Pydantic data models with computed properties and validation
- SQLite schema with foreign keys, indexes, and cascade deletes
- Migration system with version tracking, checksum verification, and idempotent SQL
- Repository pattern with full CRUD operations and transaction management
- 187 passing tests (unit + integration)
- Quality tooling: ruff, mypy (strict mode), bandit, pytest with coverage

### Phase 2: Behavioral Analysis (Next)

- Time-decay algorithm for volunteer ratings (exponential decay)
- Behavioral trend detection over shelter stay
- Weight recent observations (last 3 months) more heavily
- Aggregate scoring with confidence levels

### Phase 3: Profile Generation (Planned)

- LLM-generated adoption profiles (Claude/GPT integration)
- Evidence-based behavioral descriptions from analysis
- Shelter-approved content guidelines and templates

## Tech Stack

**Core:**
- Python 3.13 (strict type checking with mypy)
- Pydantic 2.9+ (data modeling and validation)
- SQLite (Phase 1 database)
- pydantic-settings (environment-based configuration)

**Development:**
- uv (package manager - ALWAYS use `uv run` prefix)
- pytest + pytest-cov (testing framework)
- ruff (linting and formatting)
- mypy --strict (type checking)
- bandit (security scanning)
- pre-commit (git hooks)
- python-semantic-release (automated versioning)

## Project Structure

```
src/petbio/
├── config.py                      # Settings via pydantic-settings
└── modules/
    └── db/                        # Phase 1: Data layer
        ├── models.py              # 7 Pydantic models (Animal, VolunteerNote, etc.)
        ├── schema.py              # SQLite table definitions
        ├── migrate.py             # Migration engine with version tracking
        ├── repository.py          # Database class with CRUD operations
        └── migrations/            # Numbered SQL migration files

tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Fast, isolated tests
│   └── db/                        # Model, migration, schema tests
└── integration/                   # Tests with real SQLite database
    └── db/                        # Repository, migration flow tests
```

## Build/Test Commands

**CRITICAL:** Always use `uv run` prefix (enforced by pre_tool_use_uv.py hook)

```bash
# Run tests
uv run pytest                                        # All tests
uv run pytest tests/unit/                            # Unit tests only
uv run pytest tests/integration/                     # Integration tests only
uv run pytest --cov=src --cov-report=term-missing    # With coverage

# Quality gates (must all pass before commit)
uv run ruff format src/ tests/                       # Auto-format
uv run ruff check src/ tests/                        # Lint
uv run bandit -r src/                                # Security scan
uv run mypy src/                                     # Type check (strict mode)

# All quality gates at once
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run bandit -r src/ && \
uv run mypy src/ && \
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Coding Conventions

### Data Models (Pydantic)

**Mutability Pattern (ADR-002):**
Models use `validate_assignment=True` for the repository pattern:

1. Fetch: `animal = db.get_animal(id)`
2. Modify: `animal.weight_lbs = 70.0`
3. Persist: `db.update_animal(animal)`

**Why mutable?**
- Validators run on field assignment (JSON parsing, SQLite bool conversion)
- `exclude_unset=True` enables partial update tracking
- 18+ mutation sites in codebase, no hashability requirement

**Model Features:**
- Type-safe field validation with Pydantic Field constraints
- Computed properties (`age_years`, `days_in_shelter`, `is_adoptable`)
- JSON field handling (tags stored as TEXT, parsed to `list[str]`)
- SQLite boolean conversion (0/1 → False/True)

### Repository Pattern

**CRUD Operations:**
All database access goes through `Database` class methods:
- `insert_X(model)` - Create new record
- `get_X(id)` - Fetch single record
- `update_X(model)` - Update existing record
- `delete_X(id)` - Remove record
- `list_Xs()` - Query multiple records
- `get_Xs_for_animal(animal_id)` - Fetch related records

**Usage Pattern:**
```python
from petbio.modules.db import Database, Animal
from pathlib import Path

db = Database(Path("data/petbio.db"))

# Create
animal = Animal(id="FOHA-A-12345", name="Buddy")
db.insert_animal(animal)

# Read
animal = db.get_animal("FOHA-A-12345")

# Update (mutable pattern)
animal.weight_lbs = 70.0
db.update_animal(animal)

# Delete
db.delete_animal("FOHA-A-12345")
```

**Context Managers:**
- `with db.connection()` - Read-only operations
- `with db.transaction()` - Write operations with automatic rollback on error

**SQL Construction:**
- Column names from `model_dump()` (fixed, known fields)
- All values are parameterized (no SQL injection risk)
- `# nosec B608` comments acknowledge safe pattern

### Migration System

**Migration Files:**
- Numbered format: `001_create_tables.sql`, `002_add_indexes.sql`
- Idempotent: Use `IF NOT EXISTS` clauses
- Checksum verification prevents tampering
- Apply in sequence: gaps or duplicates raise errors

**Public API:**
```python
from petbio.modules.db import init_database, migrate

init_database(db_path)           # Create migration_history table
migrate(db_path)                 # Apply pending migrations
get_current_version(db_path)     # Query schema version
get_pending_migrations(db_path)  # List unapplied migrations
```

**Exception Hierarchy:**
```
MigrationError (base)
├── MigrationValidationError
│   ├── MigrationGapError
│   ├── MigrationDuplicateError
│   └── MigrationChecksumError
└── MigrationExecutionError
```

### Type Hints

**Required everywhere (mypy --strict enforced):**
- All function signatures must have types
- Return types required (including `-> None`)
- Use `from __future__ import annotations` for forward references
- Type checking disabled in tests via `mypy.ini` override

**Example:**
```python
from __future__ import annotations

def process_animal(db: Database, animal_id: str) -> Animal | None:
    """Get and process an animal record."""
    return db.get_animal(animal_id)
```

### Testing

**Structure:**
- `tests/unit/` - Fast, isolated tests (mock external dependencies)
- `tests/integration/` - Tests with real SQLite database

**Naming:** `test_<function>_<scenario>_<expected>`

**Coverage:** 80% minimum, non-trivial functions must have tests

**Fixtures:**
- Define shared fixtures in `conftest.py`
- Use fixture scoping appropriately (function/module/session)

**Example:**
```python
def test_calculate_age_with_valid_birth_date_returns_years():
    """Test age calculation with valid birth date."""
    birth_date = date(2020, 1, 15)
    animal = Animal(id="A-001", birth_date=birth_date)
    assert animal.age_years == 6  # Computed property
```

### Error Handling

**Custom Exception Hierarchy:**
```python
MigrationError (base)
├── MigrationValidationError
│   ├── MigrationGapError
│   ├── MigrationDuplicateError
│   └── MigrationChecksumError
└── MigrationExecutionError
```

**Always chain exceptions:**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", error=str(e))
    raise DomainError("Friendly message") from e
```

## Architecture Principles

### Layered Architecture

```
Data Models (Pydantic)
    ↓
Repository Pattern (CRUD)
    ↓
SQLite (Schema + Migrations)
```

**Dependencies flow downward:**
- Models are pure data (no database knowledge)
- Repository knows about models and database
- Schema defined separately from models (loose coupling)

### Configuration Management

**pydantic-settings pattern:**
```python
from petbio.config import get_settings

settings = get_settings()
db_path = settings.database_path
```

**Environment variables:**
- Prefix: `PETBIO_`
- Source: `.env` file or environment
- Type validation via Pydantic

### Database Design

**Schema Characteristics:**
- Foreign keys enabled (`PRAGMA foreign_keys = ON`)
- Cascade deletes (delete animal → delete all related records)
- Indexes on lookup fields (`animal_id` in child tables)
- JSON fields stored as TEXT (Pydantic handles serialization)
- Timestamps in ISO format
- Boolean as INTEGER (SQLite convention)

**Sync Tracking:**
- `last_synced_at` on entity tables
- `sync_log` table tracks operations (full/incremental)

## Documentation Standards

### Google-Style Docstrings

Required for:
- All public functions
- Non-trivial private functions (>3 lines of logic)
- All classes

```python
def process_data(input_data: str, options: list[str]) -> str:
    """Process input data with the given options.

    Args:
        input_data: The raw input to process.
        options: Processing options to apply.

    Returns:
        The processed output string.

    Raises:
        ProcessingError: If processing fails.
    """
```

### Architecture Decision Records

**When to create ADR:**
- Technology choices (database, framework, library)
- Data schema design decisions
- Architectural pattern choices
- API design decisions

**Format:** See `docs/adr/000-template.md`

**Location:** `docs/adr/{number}-{slug}.md`

## Related Documentation

- [Architecture](docs/design/architecture.md) - System design overview
- [Phase 1 Design](docs/design/phase1-data-extraction.md) - Data extraction design
- [Development Standards](docs/design/development-standards.md) - Git, testing, quality
- [ADRs](docs/adr/) - Architecture decisions

## Subdirectory Context

No subdirectory CLAUDE.md files exist yet. Create when needed:
- `src/petbio/modules/db/CLAUDE.md` - Database layer specifics (if patterns become complex)
- `tests/CLAUDE.md` - Testing utilities and fixtures (if shared test code grows)
