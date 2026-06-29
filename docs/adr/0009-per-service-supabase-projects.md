# ADR 0009: Three Supabase projects, one per service, with session-pooler connections

- Status: proposed
- Date: 2026-06-28
- Deciders: project owner
- Pairs with: ADR 0004 (petdata Postgres + pgvector), ADR 0008 (all-Cloudflare hosting)

## Context

The early-days setup pointed `RETRIEVER_DATABASE_URL` and `PETDATA_DATABASE_URL` at a single shared Supabase database. retriever and petdata run independent Alembic histories against the default `public.alembic_version` table, so a shared database lets one service's `alembic upgrade head` clobber the other's revision.

Separately, the retriever migration failed against Supabase's transaction pooler (port 6543) with `asyncpg DuplicatePreparedStatementError`: transaction mode does not support prepared statements, which asyncpg uses.

Two product facts shape the topology:

- Evermore is single sign-on: one login, with module access gated by subscription (gating is future work).
- petdata grows multiple ETL modules, one per upstream source, each with its own source credentials (not user login).

ADR 0004 put petdata on Supabase Postgres + pgvector; ADR 0008 hosts all compute on Cloudflare with Supabase as the data and auth store fronted by Hyperdrive. Neither fixed the topology (how many Supabase projects, and where identity lives) or the connection-pooler choice. This ADR settles both.

## Decision

Run **three Supabase projects: identity stands alone, and each data service owns its own database.**

- **`evermore-auth`:** SSO identity only (Supabase Auth). The single login front door. stacker signs users in here; every module verifies the JWT it issues. Holds no application data and runs no Alembic history.
- **`evermore-core`:** retriever data + pgvector. retriever stores and queries its data here and verifies `evermore-auth` JWTs.
- **`evermore-petdata`:** petdata Animal Record data + pgvector. Its ETL upstream-source credentials are internal and unrelated to user login.

Identity is a separate project so that no single data module owns the platform's identity, and a data module added later inherits SSO by pointing at `evermore-auth` rather than reaching into another service's database. The code already separates `SUPABASE_URL` (auth) from `DATABASE_URL` (data), so this is a config-only topology, with no code change.

### Connection standard

All database URLs (migrations in CI and container runtime) use the **Supabase Session pooler** (`aws-<region>.pooler.supabase.com:5432`). It is IPv4-reachable (GitHub Actions runners are IPv4) and supports prepared statements (asyncpg works).

- The **transaction pooler (port 6543) is rejected**: it does not support prepared statements, which is the `asyncpg DuplicatePreparedStatementError` above.
- The **direct connection (IPv6-only) is unreachable** from CI.
- `evermore-auth` exposes no pooled database URL to our services: they reach it over HTTPS with its project URL plus anon/service_role keys, not a Postgres connection.

## Consequences

- retriever and petdata can no longer collide on `alembic_version`; each migrates its own project.
- Identity is decoupled from every data service. Adding the next module is a config change (point its `SUPABASE_URL` at `evermore-auth`), not a schema or data move.
- The session-pooler choice removes the asyncpg prepared-statement failure with no code change.
- Three projects fit on the Supabase Pro plan in use; pgvector is enabled on `evermore-core` and `evermore-petdata` only (`evermore-auth` needs no vector extension).

## Alternatives considered

- **One shared Supabase project for both data services.** Rejected: the two independent Alembic histories collide on `public.alembic_version`, and a shared database couples the services' schemas and credentials. The status quo this ADR replaces.
- **Co-locate identity inside a data service's project (e.g. `evermore-core`).** Rejected: it makes one data module own the platform's identity, and every other module would reach into that module's project for auth. A standalone identity project keeps SSO a config target, not a dependency on a sibling service.
- **Transaction pooler (port 6543) for the connection standard.** Rejected: no prepared-statement support, so asyncpg fails on migration. The direct (non-pooled) connection is IPv6-only and unreachable from IPv4 GitHub Actions runners, leaving the session pooler (port 5432) as the only option that is both IPv4-reachable and prepared-statement-capable.
