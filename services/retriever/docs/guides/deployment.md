# Deployment Guide

How to deploy Retriever to production on Cloudflare (ADR 0008).

## Architecture

The retriever backend runs as its existing Docker image on Cloudflare
Containers, fronted by a thin Cloudflare Worker. Application code references no
Cloudflare primitives: all Cloudflare concerns live at the deployment boundary
(`worker/index.ts`, `wrangler.jsonc`). The frontend is the separate stacker
portal, deployed from [`apps/stacker`](../../../../apps/stacker/) to Cloudflare
Pages.

| Component | Platform | Method |
|-----------|----------|--------|
| Backend (this service) | Cloudflare Containers (Worker-fronted) | Container image + Worker router, deployed with Wrangler |
| Frontend | Cloudflare Pages | Deployed from the stacker portal (`apps/stacker`) |
| Database | Supabase | Managed Postgres + pgvector, reached over the Postgres wire |
| Auth | Supabase Auth | Managed, JWKS endpoint for JWT verification |
| LLM Gateway | Cloudflare AI Gateway | Routes chat, embedding, and moderation traffic; BYOK provider keys held in the gateway |
| CI/CD | GitHub Actions | Deploy on merge to main, per-PR preview deploys (`.github/workflows/deploy.yml`) |

For the hands-on container build, the Worker router, local `wrangler dev`, and
secret injection, see the [Cloudflare Containers Deployment](./cloudflare-containers.md)
guide. This guide covers the production topology, the Wrangler config, secrets,
and the CD pipeline end to end.

## Prerequisites

- Cloudflare account with the container platform enabled.
- A modern Wrangler (the Worker project under `worker/` pins it; CD pins
  `4.105.0`). Wrangler 3.90 and older predate `wrangler.jsonc` container config.
- Supabase project created (Postgres + pgvector).
- LLM gateway ready:
  - Cloudflare AI Gateway configured with BYOK provider keys (OpenAI, Anthropic)
    stored in the gateway.
  - Cloudflare account ID and gateway ID, plus the gateway BYOK token
    (`LLM_GATEWAY_TOKEN`).

---

## Backend: Cloudflare Containers

The retriever ships as the multi-stage image built from `Dockerfile`
(`entrypoint.sh` runs `uvicorn` on `0.0.0.0:${PORT:-8000}`). A thin Worker
(`worker/index.ts`) forwards every inbound request to a single container
instance. The full hands-on flow (local image build, `wrangler dev`, secret
injection) lives in [Cloudflare Containers Deployment](./cloudflare-containers.md).

### Wrangler config (`wrangler.jsonc`)

The Worker and container are declared in `services/retriever/wrangler.jsonc`:

- `name`: `retriever`; `main`: `worker/index.ts`.
- `containers`: one `RetrieverContainer`, image `./Dockerfile`,
  `max_instances: 3`, `instance_type: standard`. The build context is the
  service root, so the Dockerfile's `COPY` paths resolve unchanged.
- `durable_objects`: binds `RETRIEVER_CONTAINER` to the container class.
  Cloudflare Containers are backed by a Durable Object, registered as a new
  SQLite-backed class in `migrations` (`tag: v1`). Both bindings are required.
- `vars`: non-secret config only (`PORT: "8000"`). Secrets are never committed
  here; they are injected separately (see Secrets below).

### Hyperdrive

No Hyperdrive binding is configured. The container connects directly to the
Supabase connection pooler via `DATABASE_URL`. Cloudflare Hyperdrive in front of
Supabase is deferred to issue #109; when it lands, only the connection string
behind `DATABASE_URL` changes and a Hyperdrive binding is added to
`wrangler.jsonc`.

### Object storage (R2)

No R2 binding is configured. ADR 0008 targets Cloudflare R2 for object storage
(Composition export), accessed through a storage interface, but the retriever
uses an ephemeral, process-and-discard upload path today (it embeds content into
pgvector and discards the raw file), so no bucket is bound yet. R2 is wired in
when the storage interface lands.

### Manual deploy

CD handles production (below). For a one-off manual deploy from an operator
machine with Cloudflare access:

```bash
cd services/retriever/worker
npm install
npm run deploy   # wrangler deploy --config ../wrangler.jsonc
```

---

## Secrets

Secrets are split by where they are consumed: the container runtime reads its
secrets from Wrangler secret bindings; the CD workflow reads its secrets from
GitHub Actions.

### Container runtime: Wrangler secret bindings

Non-secret config (`PORT`) is set via `vars` in `wrangler.jsonc`. Runtime
secrets are NOT committed; inject them once per environment with
`wrangler secret put`. The Worker forwards them into the container as
environment variables (`worker/index.ts`), where the Python app reads them via
pydantic-settings:

```bash
cd services/retriever/worker
npx wrangler secret put DATABASE_URL --config ../wrangler.jsonc
npx wrangler secret put LLM_GATEWAY_TOKEN --config ../wrangler.jsonc
npx wrangler secret put SUPABASE_URL --config ../wrangler.jsonc
```

These secret bindings persist on the deployed Worker; the CD workflow does not
set them. An operator configures them once (and updates them with the same
command).

### CI/CD: GitHub Actions secrets

The deploy workflow authenticates to Cloudflare and runs the gated migration
using repository Actions secrets:

| Secret | Used for |
|--------|----------|
| `CLOUDFLARE_API_TOKEN` | Scoped token: Pages + Workers + Containers deploy |
| `CLOUDFLARE_ACCOUNT_ID` | Target Cloudflare account |
| `RETRIEVER_DATABASE_URL` | Supabase pooler URL for the gated Alembic migration |

Until an operator sets `CLOUDFLARE_API_TOKEN`, the workflow's preflight job
reports it absent and every deploy job is skipped (not failed). Fork PRs, which
do not receive repository secrets, skip the same way.

---

## CD pipeline (`.github/workflows/deploy.yml`)

Continuous deployment runs on merge to main and on pull requests (ADR 0008,
issue #111).

- **Path filtering.** A `changes` job (`dorny/paths-filter`) runs the retriever
  deploy only when `services/retriever/**` or the workflow file changed.
- **Preflight gate.** Secrets cannot be read in a job-level `if`, so a
  `preflight` job detects `CLOUDFLARE_API_TOKEN` and exposes the result. When
  absent, all deploy jobs skip.
- **Production cutover (push to main).** The `deploy-retriever` job runs
  `uv sync`, then a **gated Alembic migration** against Supabase
  (`uv run alembic upgrade head`, using `RETRIEVER_DATABASE_URL`). The migration
  must succeed before the new revision takes traffic: a failure fails the job,
  so the `wrangler deploy` step never runs and production keeps the old
  revision. On success, `cloudflare/wrangler-action` runs `deploy`, building the
  container image and shifting traffic.
- **Preview (pull request).** The job runs `wrangler versions upload`, which
  uploads a new version (with its container image) that gets a preview URL and
  takes no production traffic. No migration runs against the production database
  for previews.
- **Concurrency.** A production deploy is never cancelled mid-migration or
  mid-cutover; PR previews are left running.
- **Wrangler pin.** Every deploy step pins `WRANGLER_VERSION` (`4.105.0`);
  `wrangler-action`'s old default (3.90) cannot read `wrangler.jsonc` container
  config.

---

## Database: Supabase

### Setup

1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Enable pgvector: SQL Editor > `CREATE EXTENSION IF NOT EXISTS vector;`
3. Apply Alembic migrations. In production this is the gated CD step; to run it
   by hand against Supabase:
   ```bash
   cd services/retriever
   DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres" \
       uv run alembic upgrade head
   ```
4. Configure RLS policies for the `messages`, `documents`, and `users` tables.

### Connection String

Use the Supabase **session** pooler URL (port 5432) for `DATABASE_URL`. The
transaction pooler (port 6543) does not support prepared statements and breaks
asyncpg migrations; see ADR 0009 (`docs/adr/0009-per-service-supabase-projects.md`).

```
postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase Postgres connection string (asyncpg) |
| `LLM_GATEWAY_TOKEN` | Yes | BYOK token for the LLM gateway; provider keys live in the gateway |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Yes | Supabase publishable key (`sb_publishable_…`) |
| `CLOUDFLARE_ACCOUNT_ID` | Yes¹ | Cloudflare account ID; derives the AI Gateway compat URL |
| `CLOUDFLARE_GATEWAY_ID` | Yes¹ | Cloudflare gateway ID; derives the AI Gateway compat URL |
| `LLM_GATEWAY_URL` | No | Override to point at any OpenAI-compatible gateway (replaces the two Cloudflare IDs) |
| `LLM_GATEWAY_AUTH_HEADER` | No | Header carrying `LLM_GATEWAY_TOKEN` (default `cf-aig-authorization`) |
| `PORT` | No | Container listen port (default `8000`; set via `wrangler.jsonc` `vars`) |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key (LLM observability) |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key |
| `LANGFUSE_HOST` | No | Langfuse host URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP traces endpoint (e.g. Jaeger) |
| `ENVIRONMENT` | No | `development` or `production` |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

¹ The LLM gateway is required (the app fails fast at startup when none is
configured). Configure it with either `CLOUDFLARE_ACCOUNT_ID` +
`CLOUDFLARE_GATEWAY_ID` (Cloudflare AI Gateway) or `LLM_GATEWAY_URL` (any
OpenAI-compatible gateway).

---

## Production Checklist

- [ ] Supabase project created with pgvector extension enabled
- [ ] Alembic migrations applied (gated CD step, or run by hand)
- [ ] RLS policies configured for all tables
- [ ] Cloudflare account with the container platform enabled
- [ ] Container runtime secrets set via `wrangler secret put` (`DATABASE_URL`, `LLM_GATEWAY_TOKEN`, `SUPABASE_URL`)
- [ ] Cloudflare AI Gateway configured (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_GATEWAY_ID`)
- [ ] GitHub Actions secrets set (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `RETRIEVER_DATABASE_URL`)
- [ ] Worker + container deployed (CD on merge to main, or `npm run deploy`)
- [ ] Health check responds: `GET /health`
- [ ] Admin user created in Supabase Auth dashboard (`is_admin: true` in `app_metadata`)
- [ ] Frontend deployed from the stacker portal (Cloudflare Pages)
- [ ] Can log in and ask a question

---

## Monitoring

### Health Checks

```
GET /health    → Liveness + DB + pgvector checks
```

The container also declares a Docker `HEALTHCHECK` against `/health`.

### Logs

```bash
# Stream Worker + container logs
cd services/retriever/worker
npx wrangler tail --config ../wrangler.jsonc
```

### Observability

- **Structured logs:** JSON via structlog, one object per line, on the
  container's stdout/stderr.
- **Distributed tracing:** OpenTelemetry, exporting OTLP to a platform-supplied
  endpoint (locally, Jaeger via `OTEL_EXPORTER_OTLP_ENDPOINT`).
- **LLM observability:** Langfuse (if credentials configured).

---

## Scaling

Cloudflare Containers scale within `wrangler.jsonc`: `max_instances: 3`,
`instance_type: standard`. The container class sets `sleepAfter = "10m"`, so
compute is released after inactivity and spins back up on the next request. For
MVP scale (50-100 volunteers), the defaults are sufficient.

If needed:
1. Raise `max_instances` (and revisit `instance_type`) in `wrangler.jsonc`.
2. Enable Supabase connection pooling tuning if connection limits are hit.

---

## Rollback

**Backend (Cloudflare):**
```bash
cd services/retriever/worker
npx wrangler deployments list --config ../wrangler.jsonc
```

Roll back to a previous Worker version from the Cloudflare dashboard
(Workers & Pages > retriever > Deployments), or redeploy a known-good revision.
The container image rolls with the Worker version.

**Frontend (Cloudflare Pages):**
Roll back from the Cloudflare Pages dashboard (Deployments > select a previous
deployment > "Rollback to this deploy"). The frontend is the stacker portal.
