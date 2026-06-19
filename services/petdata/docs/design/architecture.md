---
name: architecture
description: Read when onboarding or making architectural decisions. Covers style, tech stack, structure.
category: reference
when_to_use:
- Starting work on a new feature
- Onboarding to the codebase
- Making architectural decisions
- Understanding how components fit together
dependencies:
- development-standards.md
- decisions/
---
# petdata Architecture

Automated adoption profile generator for animal shelters

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: DATA LAYER (✓ Complete)            │
│                                                                  │
│  [Adalo API] → [Extraction] → [SQLite] → [Repository Pattern]  │
│                                    ↓                             │
│              [7 Pydantic Models + Computed Properties]          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: BEHAVIORAL ANALYSIS (Planned)             │
│                                                                  │
│  [Volunteer Ratings] → [Time-Decay Algorithm] → [Trends]       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 3: PROFILE GENERATION (Planned)                │
│                                                                  │
│  [Animal Data + Analysis] → [LLM] → [Adoption Profiles]        │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Style: Layered Architecture

**Current Implementation (Phase 1):**

```
┌──────────────────────────────────────┐
│   Pydantic Models (Data Layer)      │  ← Animal, VolunteerNote, etc.
│   - Validation and computed props   │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│   Repository Pattern (Access Layer) │  ← Database class with CRUD
│   - Context managers for txns       │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│   SQLite Storage (Persistence)      │  ← Schema + Migrations
│   - Foreign keys, indexes           │
└──────────────────────────────────────┘
```

**Why this approach:**
- Clear separation: data models ≠ database schema (loose coupling)
- Repository encapsulates all SQL (models stay pure)
- Migration system enables safe schema evolution
- Testable: models validate in-memory, repository tested with real DB
- Dependencies flow downward: Models don't know about database

## Tech Stack

### Backend (Python 3.13)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Data Models | Pydantic 2.9+ | Type-safe validation, JSON serialization, computed properties |
| Configuration | pydantic-settings | Environment-based config with type validation |
| Database | SQLite | Simple, file-based, sufficient for Phase 1 (migrate to Postgres later if needed) |
| Package Manager | uv | Fast, modern, deterministic dependency resolution |
| Testing | pytest + pytest-cov | Industry standard, excellent fixture system, coverage tracking |
| Linting | ruff | Fast, modern, replaces 10+ tools (black, isort, flake8, etc.) |
| Type Checking | mypy --strict | Catch type errors at dev time, strict mode enforced |
| Security | bandit | Static security analysis for Python code |

**No web framework yet:** Phase 1 is data layer only. API layer comes in Phase 2/3 if needed.



## Project Structure

```
petdata/
├── src/
│   └── petdata/
│       ├── __init__.py
│       ├── config.py                 # pydantic-settings configuration
│       │
│       └── modules/
│           └── db/                   # Phase 1: Database layer
│               ├── __init__.py
│               ├── models.py         # 7 Pydantic models
│               ├── schema.py         # SQLite table definitions
│               ├── migrate.py        # Migration engine
│               ├── repository.py     # Database class (CRUD)
│               └── migrations/       # Numbered SQL files
│                   └── 001_initial_schema.sql
│
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/                         # Fast, isolated tests
│   │   └── db/
│   │       ├── test_models.py        # Model validation, computed props
│   │       ├── test_migrate.py       # Migration engine logic
│   │       ├── test_migrations.py    # SQL migration file validation
│   │       ├── test_repository_helpers.py
│   │       └── test_schema.py        # Schema SQL parsing
│   └── integration/                  # Tests with real database
│       └── db/
│           ├── test_repository.py    # Full CRUD with SQLite
│           └── test_migration_flow.py # End-to-end migration
│
├── docs/
│   ├── adr/                          # Architecture Decision Records
│   │   ├── 000-template.md
│   │   ├── 001-example.md
│   │   └── 002-mutable-pydantic-models.md
│   └── design/
│       ├── architecture.md           # This file
│       ├── concept.md                # Original project brief
│       ├── phase1-data-extraction.md # Phase 1 design doc
│       └── development-standards.md  # Git, testing, quality standards
│
├── pyproject.toml                    # Project metadata, tool config
├── uv.lock                           # Locked dependencies
├── README.md                         # Project overview
├── CLAUDE.md                         # AI assistant guide
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # MIT license
├── CHANGELOG.md                      # Release history
└── TODO.md                           # Future work roadmap
```

## Key Design Patterns

### Repository Pattern

All database access goes through `Database` class:

```python
from petdata.modules.db import Database, Animal
from pathlib import Path

db = Database(Path("data/petdata.db"))

# Create
animal = Animal(id="A-12345", name="Buddy")
db.insert_animal(animal)

# Read
animal = db.get_animal("A-12345")

# Update (mutable pattern)
animal.weight_lbs = 70.0
db.update_animal(animal)

# Delete
db.delete_animal("A-12345")
```

**Benefits:**
- Encapsulates SQL (models stay clean)
- Transaction management via context managers
- Easy to mock for unit tests
- Single place to optimize queries

### Mutable Pydantic Models (ADR-002)

Models use `validate_assignment=True` for ergonomic updates:

```python
# Fetch
animal = db.get_animal("A-12345")

# Modify (validators run on assignment)
animal.weight_lbs = 70.0

# Persist (only sends changed fields)
db.update_animal(animal)
```

**Why mutable?**
- Validators run on field assignment (e.g., JSON parsing for tags)
- `exclude_unset=True` tracks partial updates
- Matches repository pattern (fetch-modify-persist)

**Trade-off:** Not hashable (can't use as dict keys). Acceptable because models are internal-only, no concurrency requirement.

### Migration-Based Schema Evolution

Numbered SQL files applied in sequence:

```sql
-- migrations/001_create_tables.sql
CREATE TABLE IF NOT EXISTS animals (...);

-- migrations/002_add_indexes.sql
CREATE INDEX IF NOT EXISTS idx_animal_id ON volunteer_notes(animal_id);
```

**Features:**
- Version tracking in `migration_history` table
- Checksum verification prevents tampering
- Gap detection (can't skip migrations)
- Duplicate detection (can't run same migration twice)
- Idempotent SQL (safe to re-run)

**Commands:**
```python
from petdata.modules.db import init_database, migrate

init_database(db_path)  # One-time setup
migrate(db_path)        # Apply pending migrations
get_current_version(db_path)  # Check version
```

### Configuration via pydantic-settings

Environment variables override defaults:

```python
# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PETDATA_")

    database_path: Path = Path("data/petdata.db")
    request_delay_ms: int = 500

# Usage
from petdata.config import get_settings
settings = get_settings()
```

**Environment:**
```bash
export PETDATA_DATABASE_PATH=/custom/path/db.sqlite
export PETDATA_REQUEST_DELAY_MS=1000
```

## Data Model Design

### 7 Pydantic Models

**Core Entities:**
1. **Animal** - Dog/cat record with basic info, computed properties
2. **KennelCard** - Structured bio (compatibility, commands, preferences)
3. **VolunteerNote** - Observations with 4 behavioral ratings (0-5 scale)
4. **StaffAssessment** - Professional evaluations with structured tags
5. **WalkRecord** - Walk check-in/out timestamps
6. **AnimalImage** - Photo URLs with display order
7. **SyncLog** - Extraction operation tracking

**Model Features:**
- Type-safe field validation with Pydantic Field constraints
- Computed properties (`age_years`, `days_in_shelter`, `is_adoptable`)
- JSON field handling (tags stored as TEXT, parsed to `list[str]`)
- SQLite boolean conversion (0/1 → False/True)
- Partial update tracking via `exclude_unset=True`

### SQLite Schema

**Characteristics:**
- Foreign keys enabled (`PRAGMA foreign_keys = ON`)
- Cascade deletes (delete animal → delete all related records)
- Indexes on lookup fields (`animal_id` in child tables)
- JSON fields as TEXT (Pydantic handles serialization)
- Timestamps in ISO format
- Boolean as INTEGER (SQLite convention)

**Relationships:**
```
animals (1) ──→ (N) volunteer_notes
            ──→ (N) walk_records
            ──→ (N) staff_assessments
            ──→ (1) kennel_cards
            ──→ (N) animal_images
```

### Design Decisions (ADRs)

**ADR-002: Keep Pydantic Models Mutable**
- Decision: Use `validate_assignment=True`, not `frozen=True`
- Rationale: Validators need to run on assignment, repository pattern relies on mutability
- Trade-off: Not hashable, but acceptable (internal use only)

## Testing Strategy

### Test Structure

**Unit Tests** (`tests/unit/`):
- Fast, isolated, no real database
- Test model validation, computed properties
- Test migration engine logic
- Test SQL parsing and helper functions

**Integration Tests** (`tests/integration/`):
- Test with real SQLite database
- Test full CRUD operations
- Test end-to-end migration flow
- Test foreign key constraints, cascades

**Coverage:** 187 tests, 80%+ coverage on business logic

### Test Database Management

Integration tests use temporary databases:

```python
@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        migrate(db_path)
        yield Database(db_path)
```

## Quality Gates

All must pass before commit (enforced by CI):

```bash
uv run ruff format src/ tests/        # Auto-format
uv run ruff check src/ tests/         # Lint
uv run bandit -r src/                 # Security scan
uv run mypy src/ --strict             # Type check
uv run pytest --cov=src --cov-fail-under=80  # Tests + coverage
```

## Future Architecture (Planned)

### Phase 2: Behavioral Analysis Module

```
modules/
└── analysis/
    ├── decay.py       # Time-decay algorithm (exponential)
    ├── trends.py      # Behavioral trend detection
    └── scoring.py     # Aggregate scoring system
```

**Inputs:** VolunteerNote history (ratings + timestamps)
**Outputs:** Time-weighted behavioral scores, trend indicators

### Phase 3: Profile Generation Module

```
modules/
└── profiles/
    ├── generator.py   # LLM integration (Claude/GPT)
    ├── templates.py   # Profile structure templates
    └── evidence.py    # Evidence collection from data
```

**Inputs:** Animal data + behavioral analysis
**Outputs:** Human-readable adoption profiles

**Web Layer (Optional):**
If API needed:
- FastAPI for REST API
- Pydantic for request/response schemas
- Depends() for dependency injection

## Related Documents

- [Phase 1 Design](phase1-data-extraction.md) - Detailed Phase 1 design
- [Development Standards](development-standards.md) - Git, testing, quality
- [ADR-002: Mutable Models](../adr/002-mutable-pydantic-models.md)
- [TODO](../../TODO.md) - Future work roadmap
