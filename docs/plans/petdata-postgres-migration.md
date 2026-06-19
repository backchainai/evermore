# Plan: petdata SQLite to Supabase Postgres + pgvector

Status: ready to execute, 2026-06-19. Implements [issue #9](https://github.com/backchainai/evermore/issues/9) under `../adr/0004-petdata-postgres-pgvector.md`. Companion to `repo-restructure-and-rename.md` Phase 5.

This is the "how" for #9. The decision is settled in ADR 0004; this plan resolves the four design calls the ADR left open, fixes the execution boundaries, and maps the work file-by-file against the proven template already in this repo. petdata is pre-production, so this is a clean cutover, not a data migration.

## Resolved decisions (Standard preset)

The brief at `agent_brief_petdata-postgres-migration_2026-06-19.html` carried these as decision cards; the recommended (Standard) path is now settled:

1. **Table namespacing:** `petdata_` table prefix in the shared Supabase Postgres. Avoids a `users`-style collision with retriever in one shared instance; no `search_path` juggling; matches retriever's flat-table convention. (Issue #9's acceptance criteria still say the stale `petbio_`; the renamed service uses `petdata_`.)
2. **Python runtime:** bump petdata to Python 3.14, per ADR 0004. retriever's matching bump is tracked under its own conformance issue.
3. **pgvector scope:** enable the `vector` extension in the initial migration so the store is ready; add no embedding columns until behavior analysis (Phase 6) has a real consumer. Avoids speculative schema.
4. **RLS timing:** add a `tenant_id` column on every tenant-owned table and land inert RLS policies now. This satisfies #9's "RLS policies scope data access by user" criterion; the policies stay inert until #29 sets the JWT claim, so there is no second schema migration later.
5. **Execution:** split into #9a through #9d, green-gating each (see below).
6. **Artifact:** this plan doc, plus #9a-#9d filed as GitHub sub-issues under #9.

### Stale acceptance-criteria notes

Issue #9 was migrated verbatim from Beads and carries pre-rename language. Two lines need translation when implementing:

- "PetBio uses shared Supabase Postgres" and "petbio_ table prefix" -> the service is `petdata`; tables are prefixed `petdata_`.
- "Adalo sync writes to Postgres" -> the external sync path writes through the new async repository like every other writer; no Adalo-specific work beyond pointing it at the new repository.

## Scope guard

#9 is the store migration only. Supabase JWT auth ([#29](https://github.com/backchainai/evermore/issues/29)) and OTel/structlog ([#16](https://github.com/backchainai/evermore/issues/16)) are siblings under ADR 0004 with their own issues. #9 makes the schema RLS-*ready*; it does not wire the JWT that activates the policies. #9 gates [#54](https://github.com/backchainai/evermore/issues/54) (packages/schema).

## Current state vs target

retriever already runs the exact target stack, so most of the work is copy-and-adapt rather than greenfield.

| Concern | petdata today | Target (copy retriever) |
|---|---|---|
| Store | SQLite file via stdlib `sqlite3` (sync) | Supabase Postgres + `pgvector` extension |
| Data access | Hand-rolled `src/petdata/modules/db/repository.py` (745 lines, 28 methods); routes wrap calls in `asyncio.to_thread` | SQLAlchemy 2.0 async ORM over asyncpg; `AsyncSession` dependency (copy `services/retriever/src/retriever/infrastructure/database/session.py`) |
| Migrations | Custom `src/petdata/modules/db/migrate.py` + numbered SQL + checksums | Alembic async `env.py` (copy `services/retriever/alembic/env.py`) |
| Models | 7 Pydantic models in `src/petdata/modules/db/models.py` (domain + wire) | Pydantic stays the contract (becomes packages/schema source); add SQLAlchemy ORM models as the persistence layer (copy `services/retriever/src/retriever/models/base.py`) |
| Tests | ~248 tests on in-process temp SQLite | Integration on real Postgres via `docker-compose.test.yml` (pgvector image); `pytest-asyncio` auto mode; skip-if-unavailable fixture (copy `services/retriever/tests/conftest.py`) |
| CI | petdata job runs ruff/mypy/bandit/pytest inline, no DB service | Add a `pgvector/pgvector:pg17` service + `alembic upgrade head` to the petdata job in `.github/workflows/ci.yml` |

## The 7 tables

`animals`, `kennel_cards`, `volunteer_notes`, `staff_assessments`, `walk_records`, `animal_images`, `sync_log`. Each tenant-owned table gains `tenant_id`. The two decay-critical indexes on `volunteer_notes` (`idx_volunteer_notes_animal_date`, `idx_volunteer_notes_date`) must survive the translation: the future time-decay behavioral analysis depends on them.

## Sub-issue breakdown

The split keeps each landable piece green-gateable on its own. #9a and #9c are mechanical and daedalus-sized; #9b is the behavioral cutover and benefits from interactive review.

### #9a: dependencies, infra, ORM models, Alembic (additive, no behavior change)

1. **Deps + runtime.** `pyproject.toml`: add `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `alembic>=1.14`, `pgvector>=0.3`; dev-add `pytest-asyncio`; register the `sqlalchemy.ext.mypy.plugin`; bump `requires-python` to `>=3.14`; run `uv lock`. No behavior change.
2. **Engine/session infra.** Create `src/petdata/models/base.py` and `src/petdata/infrastructure/database/session.py` from retriever's equivalents (the `Base(DeclarativeBase)`, the `postgres://` -> `postgresql+asyncpg://` URL coercion, `async_sessionmaker(engine, expire_on_commit=False)`, and the commit/rollback `get_session` dependency). Add `database_url` and `database_require_ssl` to `src/petdata/config.py`, keeping the `PETDATA_` env prefix.
3. **ORM models.** Translate the 7 tables to SQLAlchemy 2.0 mapped classes: `petdata_` table prefix, `timestamptz` for the ISO-string timestamp columns, `JSONB` for the tag/list fields, real `Boolean` columns, foreign keys with `ON DELETE CASCADE`, and a `tenant_id` column on each tenant-owned table. Pydantic models stay the wire/domain contract; add thin to/from mapping between the Pydantic contract and the ORM rows, preserving the validate-on-assignment mutability pattern at the Pydantic layer.
4. **Alembic.** Scaffold `alembic.ini` and an async `env.py` (copy retriever's `_async_db_url()` + `run_async_migrations`); autogenerate `001_initial_schema`, then hand-tune it: `CREATE EXTENSION IF NOT EXISTS vector`, all 11 indexes (keep both decay-critical `volunteer_notes` indexes), and `ENABLE ROW LEVEL SECURITY` plus the inert `tenant_id` policies on each tenant-owned table.

### #9b: async repository + FastAPI route cutover (behavioral)

5. **Async repository rewrite.** Convert all 28 methods of the `Database` class to async SQLAlchemy `select`/`insert`/`update`/`delete`. Preserve the mutable-Pydantic partial-update semantics and the upsert behavior. Drop the hand-built SQL strings and the `# nosec` markers that guarded them.
6. **FastAPI wiring.** Move the engine into a `lifespan` handler; routes depend on `get_session` plus the repository instead of `app.state.db`; delete the `asyncio.to_thread` wrappers in the route layer; remove the `init_database` / `migrate` calls from `create_app` (Alembic owns schema creation now).

### #9c: test suite on Postgres + CI service (mechanical)

7. **Tests.** Add `docker-compose.test.yml` (the `pgvector/pgvector:pg17` image on a dedicated port) and an async `conftest.py` modeled on retriever's: a `TEST_DATABASE_URL`, a `db_engine` fixture doing `create_all`/`drop_all` plus `CREATE EXTENSION IF NOT EXISTS vector`, skip-if-unavailable so the suite degrades gracefully when no Postgres is up, and `asyncio_mode = "auto"`. Rewrite the integration repository tests to async. Delete the tests that test the retired machinery (`test_migrate`, `test_migrations`, `test_schema`, `test_repository_helpers`). Add an Alembic upgrade/downgrade smoke test. Keep the Pydantic validator unit tests as-is.
8. **CI.** Add the `pgvector/pgvector:pg17` service container, the `TEST_DATABASE_URL` env, and an `alembic upgrade head` step to the petdata job in `.github/workflows/ci.yml` (the same Postgres dependency that deferred retriever's integration tests in Phase 4 CI).

### #9d: docs

9. **Docs.** Update the petdata `CLAUDE.md`, `README`, and `.env.example` (add `PETDATA_DATABASE_URL`); remove the SQLite and `migrate.py` sections. Note the new one-command local Postgres workflow.

## File-by-file map (retriever is the template)

| New/changed in petdata | Source in retriever |
|---|---|
| `src/petdata/models/base.py` | `src/retriever/models/base.py` (`Base`, `create_engine`, `create_session_factory`) |
| `src/petdata/infrastructure/database/session.py` | `src/retriever/infrastructure/database/session.py` (`get_session` commit/rollback dep) |
| `alembic/env.py`, `alembic.ini` | `services/retriever/alembic/env.py` (async `run_async_migrations`) |
| `tests/conftest.py` (async, skip-if-unavailable) | `services/retriever/tests/conftest.py` |
| `docker-compose.test.yml` | `services/retriever/docker-compose.test.yml` (`pgvector/pgvector:pg17`) |
| pyproject deps + mypy plugin | retriever's `pyproject.toml` data-layer block |

The pgvector store pattern (`src/retriever/infrastructure/vectordb/pgvector_store.py`, `Vector(1536)` + HNSW `vector_cosine_ops`) is the reference for the eventual embedding columns, but is **not** built in #9 (extension only, per decision 3).

## Top risks

- **Timestamp semantics.** The current store keeps ISO strings; the future decay algorithm reads them as ordered timestamps. Translate the timestamp columns to `timestamptz` and verify ordering/comparison behavior, especially on the two `volunteer_notes` indexes.
- **CI wall-clock.** Adding a Postgres service container lengthens the petdata job, the same dependency that deferred retriever's integration tests in Phase 4. Confirm the `ci-success` gate still completes in acceptable time.
- **Cutover test gate in flux.** The test suite is itself being rewritten during #9b/#9c. This is the reason the work is split rather than dispatched as one unattended pipeline run: keep the gate stable per sub-issue.

## Consuming this plan

The plan is shaped for `/daedalus:run-pipeline plan <path>` on the daedalus-sized sub-issues (#9a, #9c). #9b is recommended for an interactive worktree + PR. Do not begin the code migration until the plan and sub-issues are approved.
