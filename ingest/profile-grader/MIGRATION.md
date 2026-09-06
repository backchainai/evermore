# Migrating profile-grader into Evermore

profile-grader runs standalone today and is slated to become a module inside the
[Evermore](https://github.com/backchainai/evermore) platform: a monorepo of FastAPI
services under `services/`, SvelteKit apps under `apps/`, Supabase Postgres + pgvector,
and a shared design-system package. This doc records what ports as-is, what gets
swapped, and what conformance work integration adds. It is the handoff, not a promise of
timing.

## Data spine mapping

Evermore's spine is `Sources -> Animal Record -> Package -> Composition -> Export`.
profile-grader is a **read/scoring** consumer: it scores an **Animal Record** (Pet Data
owns the normalized record) and never mutates it. Scraping goes away; "extraction" in
Evermore means Pet Data pulling from the shelter system, not this tool crawling foha.org.

## Ports as-is

| Artifact | Becomes |
|---|---|
| `schema.py` (pydantic contract) | The module's response models; already surfaced at `/api/docs` (OpenAPI 3.1) |
| `parse` / `metrics` / `judge` / `score` / `record` | Domain logic, unchanged |
| `server.py` routes (`/api/index`, `/api/profile/{slug}`) | The module's FastAPI routes |
| `rubric.md` + `DIMENSION_HELP` + score bands | Scoring semantics; bands ship in `index.json`, not hardcoded in the view |

## Swaps at integration

- **`FileStore` -> a Supabase-backed `Store`.** The `Store` Protocol is the seam; the
  routes do not change. Cloud Run has an ephemeral filesystem, so records live in
  Postgres, not `data/results/`.
- **Scrape source.** Firecrawl over foha.org is replaced by reading Pet Data's Animal
  Record. The grader stops scraping and scores normalized records.
- **The view.** `dashboard/index.html` (a throwaway refinement surface) is rebuilt as a
  SvelteKit route in `apps/`, consuming `/api/*` and the shared design-system tokens.
- **Entrypoint.** `grade serve` (uvicorn) becomes the service app, deployed with
  `gcloud run deploy --source .`.

## Add at integration (tech-stack conformance, Evermore ADR 0024)

- **Auth:** Supabase Auth + RLS; scope records to the shelter/org.
- **Observability:** structlog JSON logging; OpenTelemetry API instrumentation.
- **Ops endpoints:** health check; `/llms.txt` via `fast-llms-txt`.
- **CORS:** tighten `allow_origins` from `*` to the app origin(s). The server takes
  `cors_origins` today; the default is permissive for local dev only.
- **LLM plumbing:** route the judge through Cloudflare AI Gateway; Promptfoo evals in CI.

## Pre-port cleanups (tracked, not blocking)

- Fold `DIMENSIONS` + `DIMENSION_HELP` into one dataclass registry before rubric v1.1,
  so adding a dimension is a one-place change (currently two parallel structures).
- `DATA` root re-anchoring is handled for now by `grade serve --data-dir`; the Supabase
  store makes the on-disk anchor moot.

## Outcome calibration (the payoff)

Records carry null outcome fields (`days_to_placement`, `adopted_at`, ...) keyed to the
animal. Once funnel/placement data is joined on animal ID, correlate the 0-100 raw score
against actual days-to-placement and re-weight the rubric: "graded against research"
becomes "graded against Evermore outcomes."
