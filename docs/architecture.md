# Evermore Architecture

Canonical reference for how the Evermore subscription portal is structured. Read this before making cross-repo changes.

## Topology

```
                ┌──────────────────────────────────┐
                │  Customer (browser)              │
                └──────────────┬───────────────────┘
                               │  Supabase Auth (JWT, RS256)
                ┌──────────────▼───────────────────┐
                │  stacker (SvelteKit @ CF Pages)  │
                │  ─ Module registry               │
                │  ─ Subscription gate (UI)        │
                │  ─ BaseApiClient forwards JWT    │
                └──┬───────────────────────────┬───┘
                   │ Authorization: Bearer     │ Authorization: Bearer
        ┌──────────▼──────────┐     ┌──────────▼──────────┐
        │  retriever          │     │  petbio             │
        │  (FastAPI @ Cloud   │     │  (FastAPI @ Cloud   │
        │   Run)              │     │   Run)              │
        │  ─ JWKS validation  │     │  ─ JWKS validation  │
        │  ─ Subscription gate│     │  ─ Subscription gate│
        │  ─ /openapi /health │     │  ─ /openapi /health │
        │  ─ /llms.txt        │     │  ─ /llms.txt        │
        └──────────┬──────────┘     └──────────┬──────────┘
                   │                           │
                   └─────────────┬─────────────┘
                                 ▼
                       ┌─────────────────────┐
                       │  Supabase           │
                       │  ─ Auth (JWKS)      │
                       │  ─ Postgres         │
                       │    · subscriptions  │
                       │    · pgvector       │
                       └─────────────────────┘
```

## Module backend contract

Every Evermore module backend MUST expose:

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | None | Liveness for Cloud Run + monitoring |
| `GET /openapi.json` | None | FastAPI auto-generated; consumed by stacker for type generation |
| `GET /llms.txt` | None | LLM-readable surface description (via `fast-llms-txt`) |
| `GET /manifest` | None | Self-description: `{id, name, version, capabilities[], openapi_url, llms_url}` (optional but recommended) |
| `*` (any other) | Required | Validate JWT via JWKS, then check subscription entitlement for this module |

Conventions:

- Routes prefixed `/api/v1/`
- Errors return JSON: `{error: <slug>, message: <human>}`
- 401 = bad/missing JWT; 403 = no subscription or wrong role
- Structured logs (JSON via structlog), OTel span per request

## Module shim contract (in stacker)

Each module contributes a frontend shim under `stacker/src/lib/modules/{id}/`:

```
stacker/src/lib/modules/{id}/
├── index.ts         # exports ModuleDefinition (id, name, basePath, navItems, icon)
├── api/
│   ├── client.ts    # extends BaseApiClient (src/lib/api/base-client.ts)
│   └── types.generated.ts  # generated from backend's /openapi.json
└── components/      # Svelte components used by /app/{id}/* routes
```

Plus:

- A SvelteKit route at `stacker/src/routes/app/{id}/` with subroutes per nav item
- Registration in `stacker/src/lib/portal/config.ts` `MODULE_REGISTRY`
- Env var `PUBLIC_{ID_UPPER}_API_URL` pointing at the backend

## Cross-cutting concerns

| Concern | Owner | Reference |
|---|---|---|
| Authentication | Supabase Auth, validated per-backend via JWKS | `auth-flow.md` |
| Authorization | Subscription table + per-module gate (UI + backend) | `subscriptions.md` |
| Observability | structlog JSON + OpenTelemetry API | tech-stack standard |
| LLM gateway | Cloudflare AI Gateway (retriever uses it; future modules should too) | tech-stack standard |
| Type contracts | OpenAPI 3.1 → TS via `openapi-typescript`, regenerated in stacker CI | `module-template.md` |

## What lives where

| Type of code/doc | Repo |
|---|---|
| Portal UI shell, routing, theme | `stacker/src/lib/portal/` |
| Module UI shim (per module) | `stacker/src/lib/modules/{id}/` |
| Module backend implementation | `{module}/` |
| Cross-cutting contracts | `platform/docs/` |
| Per-module conventions | `{module}/CLAUDE.md` |
| Cross-cutting decisions (ADRs) | `platform/docs/adr/` |
| Per-module decisions | `{module}/docs/decisions/` (e.g. retriever) |

## Adding a new module

See `module-template.md` for the step-by-step. Summary: scaffold a FastAPI service that meets the backend contract, add a shim in stacker, register, deploy.
