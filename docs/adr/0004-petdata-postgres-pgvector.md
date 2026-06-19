# ADR 0004: petdata moves from SQLite to Supabase Postgres + pgvector

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner

## Context

ADR 0003 mandates Supabase Postgres + pgvector as the single primary store for every module and forbids SQLite as a primary store. `petdata` (the renamed `petbio`) is the largest divergence from that standard:

- Primary store is SQLite, accessed through a hand-rolled `Database` repository class and a custom migration engine (`migrate.py`) with numbered SQL files, checksum verification, and version tracking.
- Seven Pydantic models carry the domain data; persistence is plain `sqlite3` with parameterized SQL.
- It targets Python 3.13 and has no Supabase auth, no async data layer, and no vector storage.

Three forces make this the gating refactor for Phase 5:

- **Shared schema (packages/schema) depends on it.** The Animal Record, Package, and Composition contracts (issue #54) are sourced from petdata's Pydantic models; they cannot stabilize on a store that the rest of the platform does not share.
- **Supabase Auth + RLS requires Postgres.** Per-shelter (tenant) isolation and the `subscribed_tools` entitlement model (ADR 0003, packages/auth) are enforced in Postgres RLS. SQLite cannot host that.
- **Behavior analysis needs vectors.** The planned time-decay behavioral analysis and future semantic features want embeddings co-located with the animal data. pgvector keeps that in one store rather than bolting on a second.

petdata is pre-production: there is no live shelter data to migrate. This is a clean cutover, not a data migration.

## Decision

Move petdata to the platform data stack:

- **Primary store:** Supabase Postgres with the `pgvector` extension enabled. No SQLite as a primary store; SQLite may remain only for throwaway unit-test fixtures where a real Postgres is unavailable, never as an application path.
- **Data access:** SQLAlchemy 2.0 async ORM over `asyncpg`. Retire the hand-rolled `Database` repository and the `migrate.py` engine.
- **Migrations:** Alembic. The numbered SQL files and the checksum/version machinery are removed; Alembic owns schema history.
- **Schema source of truth:** Pydantic models remain the wire/domain contract (and become the packages/schema source). SQLAlchemy models are the persistence layer, mapped to and from the Pydantic contract. One contract, two layers; the mutability pattern petdata documented for the repository flow (validate-on-assignment) is preserved at the Pydantic layer.
- **Multi-tenant ready:** tables carry a tenant (shelter) scoping column so Supabase RLS can isolate rows once auth lands (issue #29).
- **Runtime:** Python 3.14, aligning with ADR 0003.

This work is tracked by issues #9 (SQLite to Postgres, SQLAlchemy 2.0 async, Alembic), #29 (Supabase JWT auth), and #16 (OTel/structlog), and it gates #54 (packages/schema).

## Consequences

- This is the heaviest Phase 5 lift. The seven models, all CRUD, and the ~248 tests are rewritten against Postgres. Integration tests move from in-process SQLite to a real Postgres (testcontainers or `supabase start`), and CI gains a Postgres service step (the same dependency that deferred retriever's integration tests in Phase 4 CI).
- Local development runs Postgres + pgvector via the one-command docker stack rather than a file on disk.
- The custom migration engine and its safety features (checksums, gap detection) are dropped in favor of Alembic's revision graph. This is a net simplification: Alembic is on-distribution and contributor-familiar.
- pgvector lets behavior-analysis embeddings live beside the animal records, avoiding a second datastore.
- petdata can finally share `packages/schema` and `packages/auth` with the rest of the platform instead of carrying private equivalents.

## Alternatives considered

- **Keep SQLite, add a vector extension (sqlite-vss/sqlite-vec).** Rejected: violates ADR 0003's no-SQLite-primary-store rule, cannot host Supabase Auth/RLS, and keeps petdata off the shared schema and auth packages.
- **Postgres via plain psycopg and hand-written SQL.** Rejected: ADR 0003 mandates SQLAlchemy 2.0 async + Alembic, and the ORM lets petdata share data-layer patterns with retriever rather than reinventing them.
- **Defer the database change and do auth/observability first.** Rejected: auth (RLS) and the shared schema both depend on Postgres, so the store change has to come first. It gates the rest of petdata's Phase 5 work.
