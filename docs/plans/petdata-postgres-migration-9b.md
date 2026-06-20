# Plan: #9b petdata async repository + FastAPI route cutover

Status: ready to execute, 2026-06-19. Sub-issue [#69](https://github.com/backchainai/evermore/issues/69) of [#9](https://github.com/backchainai/evermore/issues/9), under `petdata-postgres-migration.md` (steps 5-6) and ADR 0004. Depends on #9a (#68, merged: ORM models, `get_session`, Alembic are on `main`). This is the behavioral cutover: sync sqlite3 to async SQLAlchemy 2.0. Recommended as an interactive worktree + PR, not an unattended pipeline run.

## Decision: how #9b stays green (chosen: Defer)

`tests/integration/db/test_repository.py` exercises the sync `Database` against temp SQLite and cannot survive the rewrite. The async repository tests and the CI Postgres service are slated for #9c. The chosen strategy is **Defer**: delete the breaking sqlite tests in #9b; the async repository merges to `main` with no integration coverage until #9c adds the Postgres-backed async suite plus the CI service. This is the smallest #9b diff and strictly matches the plan's sub-issue split. CI enforces no coverage floor (`pytest --cov` with no `--cov-fail-under`), so the gate passes with the integration suite removed.

Rejected alternatives: Hybrid (async tests now with skip-if-unavailable; #9c flips skips on) and Collapse (fold all of #9c into #9b).

## Cutover surface (verified)

- Routes are two GETs only: `/animals`, `/animals/{id}`. All 24 write/upsert/delete methods on `Database` are exercised only by `test_repository.py` and the future Adalo sync path (not yet wired in this service). Runtime blast radius is small; test blast radius is the integration suite.
- `get_session` already exists from #9a (`src/petdata/infrastructure/database/session.py`): request-scoped, commit on success, rollback on error. The plan says routes depend on it.
- CI petdata job: `uv sync --extra dev` then `ruff format --check`, `ruff check`, `mypy src/`, `uvx bandit -r src/ -q`, `pytest --cov`. No Postgres service, no `alembic upgrade`, no coverage floor. All of those are #9c.

## Steps

### 0. Setup
- Fresh worktree `issue-69` -> branch `issue/69` off updated `origin/main`. Verify `src/petdata/models/{base,tables,mappers}.py` are present on `main` before starting.
- Claim #69.
- Copy this plan into the issue-69 branch (it is not yet on `main`).

### 1. Rewrite `src/petdata/modules/db/repository.py` (the `Database` class to async)
- `Database.__init__(self, session: AsyncSession)` instead of `(self, db_path: Path)`. Drop `sqlite3`, `connection()`, `transaction()`.
- Convert all 28 methods to async SQLAlchemy `select` / `insert` / `update` / `delete` over the ORM models, round-tripping through `petdata.models.mappers.*` so callers and routes still see Pydantic contracts.
- Delete `_build_insert_sql` / `_build_update_sql` / `_build_upsert_sql` and every `# nosec B608`. Remove `[tool.bandit] skips = ["B608"]` from `pyproject.toml`.
- Preserve partial-update semantics: update methods compute changed columns via `model.model_dump(exclude_unset=True)` (minus id) and apply with `update().values(**changed)`. Same "only set fields are written" behavior, no hand SQL.
- Preserve upsert: `upsert_kennel_card` uses `sqlalchemy.dialects.postgresql.insert(...).on_conflict_do_update(index_elements=["animal_id"], set_=...)`.
- Timestamps: rely on the #9a server defaults (created_at / updated_at), not the old `_add_timestamps()`. The decay ordering on `volunteer_notes` now rides real `timestamptz` columns.
- Keep the class name `Database` (plan fidelity, smallest diff across `db/__init__`, dependencies, routes).

### 2. FastAPI wiring
- `src/petdata/main.py`: add an `asynccontextmanager` `lifespan`; delete `init_database`, `migrate`, and `app.state.db` (Alembic owns schema now). Rewrite `/health` to open a session and run `SELECT 1` (optionally the pgvector extension check), mirroring `services/retriever/src/retriever/main.py`.
- `src/petdata/modules/web/dependencies.py`: replace `get_db(request)` with `get_repository(session: AsyncSession = Depends(get_session)) -> Database`.
- `src/petdata/modules/web/routes.py`: drop `asyncio.to_thread` and `asyncio.gather`; routes take `repo: Database = Depends(get_repository)` and `await repo.get_animal(...)`. The three detail-page fetches go sequential on one session (fine for two GETs).

### 3. Tests (Defer) and exports
- Delete `tests/integration/db/test_repository.py`.
- Leave `test_migrate`, `test_schema`, `test_migration_flow` untouched IF they only exercise the still-present `migrate.py` / `schema.py`. If any constructs the sync `Database(path)`, delete it too (resolve by reading the files at implementation time).
- `src/petdata/modules/db/__init__.py` keeps its current exports (`init_database`, `migrate`, `create_tables`, `drop_tables`) so surviving migration tests still import cleanly.

### Gate after the rewrite (must pass with no Postgres, matching CI)
`uv run ruff format --check src/ tests/` then `ruff check`, `mypy src/` (local: `uv run python -m mypy src/`), `bandit -r src/` (B608 skip removed), `pytest --cov` (integration repo suite gone; unit/model + #9a tests remain).

## Resolved without asking (plan-dictated, flagged for visibility)
- Session ownership: request-scoped `AsyncSession` via `get_session`, not retriever's `session_factory`-in-repo idiom.
- Class name stays `Database`.
- Dead modules (`migrate.py`, `schema.py`, `migrations/`) and the now-unused `config.database_path` are left for #9c / #9d cleanup, not deleted here.

## Out of scope (later sub-issues)
- #9c (#70): async test suite on real Postgres, `docker-compose.test.yml`, CI `pgvector/pgvector:pg17` service + `alembic upgrade head` step, delete retired-machinery tests, Alembic upgrade/downgrade smoke test.
- #9d (#71): docs (petdata `CLAUDE.md`, `README`, `.env.example` with `PETDATA_DATABASE_URL`); remove SQLite / `migrate.py` sections.

## Git protocol
Per the git invariant, get user approval before any `git add` or commit. #9b is the interactive, human-reviewed PR: stop before staging and surface the diff for review.
