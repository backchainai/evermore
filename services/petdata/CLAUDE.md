# petdata

## Repository Overview

petdata is an automated adoption profile generator for nonprofit animal shelters. It extracts animal data from a shelter's Shelter Management System (SMS), analyzes behavioral trends using time-decay algorithms, and generates evidence-based adoption profiles using LLMs.

**Current Phase:** Phase 1 complete (data extraction and storage on Supabase Postgres).
**Next Phase:** Time-decay behavioral analysis.

## Project Status

### Phase 1: Data Extraction (✓ Complete)

- 7 Pydantic domain models with computed properties and validation
- Supabase Postgres + pgvector accessed through async SQLAlchemy 2.0 (asyncpg)
- Alembic owns the schema (foreign keys, indexes, cascade deletes, a `tenant_id` column on every table for row-level security)
- Async repository pattern with full CRUD operations over a request-scoped session
- Unit suite plus a Postgres-backed integration suite
- Quality tooling: ruff, mypy (strict mode), bandit, pytest with coverage

### Phase 2: Behavioral Analysis (Next)

- Time-decay algorithm for volunteer ratings (exponential decay)
- Behavioral trend detection over the shelter stay
- Recent observations (last 3 months) weighted more heavily
- Aggregate scoring with confidence levels

### Phase 3: Profile Generation (Planned)

- LLM-generated adoption profiles
- Evidence-based behavioral descriptions from analysis
- Shelter-approved content guidelines and templates

## Tech Stack

**Core:**
- Python 3.14 (strict type checking with mypy)
- Pydantic 2.9+ and pydantic-settings (domain models, wire contracts, configuration)
- SQLAlchemy 2.0 async with asyncpg (ORM and engine)
- Alembic (schema migrations)
- Supabase Postgres with the pgvector extension

**Development:**
- uv (package manager: ALWAYS use the `uv run` prefix)
- Docker (local Postgres + pgvector via `docker-compose.test.yml`)
- pytest + pytest-asyncio + pytest-cov (testing)
- ruff (linting and formatting)
- mypy --strict (type checking)
- bandit (security scanning)
- pre-commit (git hooks)
- python-semantic-release (automated versioning)

## Project Structure

```
src/petdata/
├── config.py                      # Settings via pydantic-settings (PETDATA_ prefix)
├── main.py                        # FastAPI application factory (create_app)
├── models/                        # SQLAlchemy ORM layer
│   ├── base.py                    # Declarative Base + async engine/session factory
│   ├── tables.py                  # 7 ORM tables (petdata_ prefix, tenant_id column)
│   └── mappers.py                 # ORM row <-> Pydantic domain model mapping
├── infrastructure/
│   └── database/session.py        # FastAPI async session dependency (get_session)
└── modules/
    ├── db/
    │   ├── models.py              # 7 Pydantic domain models (Animal, VolunteerNote, ...)
    │   └── repository.py          # Async Database class with CRUD operations
    ├── api/                       # SMS extraction HTTP client
    └── web/                       # API routes, request/response schemas, dependencies

alembic/                           # Migration environment (schema source of truth)
alembic.ini
docker-compose.test.yml            # Local pgvector Postgres (port 5434)

tests/
├── unit/                          # Fast, isolated tests (no database)
└── integration/                   # Postgres-backed tests
    └── db/                        # Repository round-trips, Alembic upgrade/downgrade
```

## Build/Test Commands

**CRITICAL:** Always use the `uv run` prefix (enforced by the `pre_tool_use_uv.py` hook). Install dev tooling with `uv sync --extra dev`.

### Local database

The integration suite and a locally-run API both need Postgres. `docker-compose.test.yml` provides an ephemeral pgvector container on port 5434:

```bash
docker compose -f docker-compose.test.yml up -d   # start Postgres + pgvector
uv run alembic upgrade head                        # apply the schema
# ... run tests or the app ...
docker compose -f docker-compose.test.yml down     # stop and discard
```

### Tests

```bash
uv run pytest                                        # All tests
uv run pytest tests/unit/                            # Unit tests only (no DB)
uv run pytest tests/integration/                     # Integration tests (need Postgres)
uv run pytest --cov=src --cov-report=term-missing    # With coverage
```

Integration tests are marked `@pytest.mark.integration` and skip automatically when no Postgres is reachable. Override the connection string with `TEST_DATABASE_URL` (default `postgresql+asyncpg://postgres:postgres@localhost:5434/petdata_test`).

### Quality gates (must all pass before commit)

```bash
uv run ruff format src/ tests/                       # Auto-format
uv run ruff check src/ tests/                        # Lint
uv run bandit -r src/                                # Security scan
uv run python -m mypy src/                           # Type check (strict mode)
uv run pytest tests/ --cov=src --cov-report=term-missing
```

Note: locally, prefer `uv run python -m mypy src/` so the project's pinned mypy runs rather than a globally-installed one. CI uses `uv run mypy src/` on a clean runner.

## Coding Conventions

### Domain models (Pydantic) and ORM tables (SQLAlchemy)

The data layer keeps two representations, mapped by `models/mappers.py`:

- **Pydantic domain models** (`modules/db/models.py`): the wire/domain contract. Models use `validate_assignment=True` for the fetch/modify/persist pattern, so validators run on field assignment.
- **SQLAlchemy ORM tables** (`models/tables.py`): the persistence layer. Tables carry the `petdata_` prefix and a `tenant_id` column (default tenant `00000000-0000-0000-0000-000000000001`) for Postgres row-level security.

The repository converts between them via `to_row` / `from_row` in `mappers.py`; callers work in Pydantic models and never touch ORM rows directly.

**Model features:**
- Type-safe field validation with Pydantic `Field` constraints
- Computed properties (`age_years`, `days_in_shelter`, `is_adoptable`)
- List/JSON fields map to Postgres JSONB

### Repository pattern (async)

All database access goes through the async `Database` class, constructed with an `AsyncSession`:

- `insert_X(model)` - create a record
- `get_X(id)` - fetch a single record
- `update_X(model)` - update an existing record (raises `ValueError` if the model has no id)
- `delete_X(id)` - remove a record
- `list_Xs()` / `get_Xs_for_animal(animal_id)` - query multiple records

**Usage:**
```python
from sqlalchemy.ext.asyncio import AsyncSession

from petdata.modules.db import Animal, Database


async def example(session: AsyncSession) -> None:
    db = Database(session)

    # Create
    await db.insert_animal(Animal(id="A-12345", name="Buddy"))

    # Read
    animal = await db.get_animal("A-12345")

    # Update (mutable Pydantic pattern)
    if animal is not None:
        animal.weight_lbs = 70.0
        await db.update_animal(animal)

    # Delete (cascades to child rows)
    await db.delete_animal("A-12345")
```

In the FastAPI app, inject the session via the `get_session` dependency (`infrastructure/database/session.py`), which commits on success and rolls back on error. The async engine is built lazily on first request from `PETDATA_DATABASE_URL`, so importing the app needs no live database.

### Migrations (Alembic)

Alembic owns the schema; the application does not create tables at startup.

```bash
uv run alembic upgrade head            # apply all pending migrations
uv run alembic downgrade -1            # roll back one revision
uv run alembic revision --autogenerate -m "describe change"   # author a migration
```

`alembic/env.py` resolves the database URL at runtime from petdata settings (`PETDATA_DATABASE_URL`) and runs migrations through an async engine. The `sqlalchemy.url` in `alembic.ini` is an unused placeholder.

### Type hints

Required everywhere (mypy --strict enforced): typed signatures and return types (including `-> None`). Use `from __future__ import annotations` for forward references. SQLAlchemy resolves `Mapped[...]` annotations at runtime, so imports used only in mapped-class annotations stay at module scope (see the ruff `flake8-type-checking` config in `pyproject.toml`).

### Testing

- `tests/unit/` - fast, isolated tests with no database
- `tests/integration/` - Postgres-backed tests; `db_engine` / `session` fixtures (in `tests/conftest.py`) create the schema per test and skip when no DB is reachable

**Naming:** `test_<function>_<scenario>_<expected>`. **Coverage:** non-trivial functions must have tests.

### Error handling

Chain exceptions to preserve context:
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", error=str(e))
    raise DomainError("Friendly message") from e
```

## Architecture Principles

### Layered architecture

```
Pydantic domain models
    ↓ (mappers)
SQLAlchemy ORM tables
    ↓
Async repository (CRUD)
    ↓
Postgres (schema owned by Alembic)
```

Dependencies flow downward: domain models are pure data; the repository knows about models and sessions; the schema lives in Alembic migrations.

### Configuration management

```python
from petdata.config import get_settings

settings = get_settings()
url = settings.database_url.get_secret_value()
```

Environment variables use the `PETDATA_` prefix, loaded from `.env` or the environment. `PETDATA_DATABASE_URL` is the async connection URL (`postgres://` and `postgresql://` are normalized to `postgresql+asyncpg://`); `PETDATA_DATABASE_REQUIRE_SSL` enforces SSL in production. See `.env.example` for the full set.

### Database design

- Foreign keys with cascade deletes (delete an animal, delete its related records)
- Indexes on lookup fields (`animal_id` in child tables); both decay-critical volunteer-note indexes are in the initial migration
- `tenant_id` on every table for row-level security
- pgvector extension enabled for embedding columns
- List fields stored as JSONB; timestamps as timezone-aware columns
- `SyncLog` tracks extraction operations (full/incremental)

## Documentation Standards

### Google-style docstrings

Required for public functions, non-trivial private functions, and classes:
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

Create an ADR for technology choices, schema design decisions, architectural patterns, and API design decisions. The Postgres migration is recorded in the monorepo ADRs (`docs/adr/`, ADR 0003 tech stack and ADR 0004 petdata Postgres migration).
