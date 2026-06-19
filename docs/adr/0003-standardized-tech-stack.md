# ADR 0003: Aggressively standardize all modules on the platform tech stack

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner

## Context

The four modules grew independently and diverge from the platform technology standard at `~/.claude/standards/tech-stack-standard.md`. `petbio` uses SQLite with a hand-rolled migration engine and targets Python 3.13; `retriever` chose GCP-native observability (its ADR 018) and Langfuse v3; versions trail the standard's floors in several places.

The operator's directive: **aggressively refactor all modules to the standard. Nothing is sacred at this stage; any prior choice can be reconsidered.** Rationale:

- **On-distribution code.** The standard's languages and frameworks are well represented in training data, so LLMs develop and maintain them more reliably.
- **Consistency** across the platform lowers cognitive load and lets shared packages exist.
- **Contributor familiarity** and established best practices, supporting the open-source goal.

## Decision

Adopt the platform tech standard as the **single stack for every module**. Conformance is mandatory, not best-effort. Module-level decisions that conflict with the standard are **superseded** by it; we refactor rather than grandfather. Any future deviation requires its own ADR (per the standard's own rule).

Binding choices (see the standard for version floors):

- **Language/runtime:** Python 3.14+, `uv`, `mypy --strict`. TypeScript 6 strict (shared `tsconfig` base).
- **Backend:** FastAPI, async SQLAlchemy 2.0, Alembic migrations, Pydantic models on every endpoint, OpenAPI 3.1 auto-generated.
- **Database:** Supabase Postgres + pgvector only. **No SQLite as a primary store.**
- **Auth:** Supabase Auth + RLS; JWT/JWKS; per-tool entitlements via a `subscribed_tools` access-token claim enforced in RLS.
- **Frontend:** SvelteKit + Svelte 5 runes + Skeleton UI v4 + Tailwind v4.
- **LLM gateway:** Cloudflare AI Gateway for all LLM and embedding traffic.
- **Observability:** OpenTelemetry API only in application code; backend wired through the OTel Collector to Datadog; structlog JSON; Sentry for errors; Langfuse v4 for LLM observability.
- **Quality/CI:** Promptfoo evals in CI from day one; Schemathesis fuzz; Hurl smoke; Playwright e2e; pytest + httpx + respx.
- **CI/CD & deploy:** GitHub Actions; Workload Identity Federation (`google-github-actions/auth@v3`, no long-lived keys); Cloud Run (`gcloud run deploy --source .`) for services; Cloudflare Pages for stacker; Dev Containers + `docker compose` for one-command local dev.
- **LLM ergonomics:** `/llms.txt` via `fast-llms-txt`; `openapi-llm` for tool-use schemas.
- **Object storage:** Cloudflare R2 (not Supabase Storage unless auth-gated uploads require it).

## Per-module conformance

| Module | Status today | Refactor obligation |
|---|---|---|
| **stacker** | largely conformant | TS 6 strict + shared `tsconfig`; entitlements via `+layout.server.ts`; extract shared `packages/ui` |
| **retriever** | mostly conformant | Python 3.14; default LLM traffic via Cloudflare AI Gateway; Langfuse v3 → v4; observability backend → Datadog via OTel Collector (supersedes its ADR 018, low app-code cost because app code is OTel-API-only); add Sentry, Promptfoo, Schemathesis |
| **petdata** (petbio) | major divergence | **SQLite → Supabase Postgres + pgvector**; hand-rolled migrations → SQLAlchemy 2.0 async + Alembic; add Supabase JWT auth, OTel, structlog, Sentry; Python 3.14. This is the heavy lift and it gates the shared schema work. |
| **biowriter** | greenfield | build to the standard from day one |

## Consequences

- Short-term refactor cost (petdata's database migration is the largest) is paid for long-term development velocity, contributor onboarding, and the ability to share `packages/`.
- The shared Animal Record / Package / Composition contracts use Pydantic as the source of truth, with TypeScript types generated from the OpenAPI specs (one schema, two languages).
- Retriever's GCP-native observability ADR is formally superseded here; a short superseding ADR lands in the retriever service docs during the refactor.
