# Module Template

Step-by-step checklist for adding a new FastAPI backend module to Evermore. Use `retriever/` as the canonical reference implementation throughout.

## Prerequisites

- A short, lowercase, ≤ 8-char module id (e.g. `howl`, `forge`)
- An entry decided on for `stacker/src/lib/portal/config.ts` MODULE_REGISTRY
- A Stripe Price with `metadata.module_id` set (for billing)

## 1. Backend repo scaffold

Create a new sibling repo under `evermore/`:

```
evermore/{module}/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
├── README.md
├── src/{module}/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── modules/
│       ├── auth/
│       │   ├── jwks.py
│       │   ├── dependencies.py
│       │   └── subscription.py
│       └── web/
│           └── routes.py
└── tests/
```

## 2. Required dependencies

```toml
[project]
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.34",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "structlog>=24.4",
  "pyjwt[crypto]>=2.10",
  "httpx>=0.28",
  "opentelemetry-api>=1.28",
  "opentelemetry-instrumentation-fastapi>=0.49b0",
  "fast-llms-txt>=0.3",
]
```

Pin actual versions per the tech stack standard.

## 3. Required endpoints

| Endpoint | Auth | Implementation |
|---|---|---|
| `GET /health` | None | Returns `{status, version, ...checks}` |
| `GET /openapi.json` | None | FastAPI auto-generated |
| `GET /llms.txt` | None | Mount via `fast-llms-txt` |
| `GET /manifest` | None | `{id, name, version, capabilities, openapi_url, llms_url}` |
| `/api/v1/*` | JWT + subscription | Module's actual functionality |

## 4. Auth wiring

Copy the JWKS validator and dependencies from `services/retriever/src/retriever/modules/auth/`. Apply as router-level dependencies:

```python
from fastapi import APIRouter, Depends
from .auth.dependencies import require_auth
from .auth.subscription import require_subscription

router = APIRouter(
    prefix="/api/v1",
    dependencies=[
        Depends(require_auth),
        Depends(require_subscription("{module_id}")),
    ],
)
```

## 5. Required env vars

```bash
# .env.example
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_JWKS_URL=https://xxx.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_PROJECT_ID=xxx
SUPABASE_SERVICE_KEY=xxx           # ONLY if backend writes; reads via user JWT preferred
DATABASE_URL=postgresql://...      # if module needs Postgres
OTEL_EXPORTER_OTLP_ENDPOINT=...    # observability target
LOG_LEVEL=INFO
```

Use the `{MODULE}_` prefix for module-specific vars.

## 6. Observability

```python
import structlog
from opentelemetry import trace

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

# In main.py:
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

## 7. Stacker registration

In `stacker/`:

1. Create `src/lib/modules/{id}/index.ts` exporting a `ModuleDefinition`:

   ```typescript
   import type { ModuleDefinition } from '$lib/portal/types';
   import { Activity } from 'lucide-svelte';

   export const HOWL_MODULE: ModuleDefinition = {
     id: 'howl',
     name: 'Howl',
     description: 'One-line description',
     icon: Activity,
     basePath: '/app/howl',
     navItems: [
       { label: 'Dashboard', href: '/app/howl', icon: Activity },
     ],
     status: 'locked',
   };
   ```

2. Create `src/lib/modules/{id}/api/client.ts` extending `BaseApiClient` from `src/lib/api/base-client.ts`.

3. Add to `MODULE_REGISTRY` in `src/lib/portal/config.ts`.

4. Add SvelteKit routes under `src/routes/app/{id}/`.

5. Add `PUBLIC_{ID_UPPER}_API_URL` to `.env.example`.

6. Run `npm run gen:types` to generate `src/lib/modules/{id}/api/types.generated.ts`.

## 8. Subscriptions

Add a row to the Stripe Price catalog with `metadata.module_id = '{id}'`. The Stripe webhook (`stacker/src/routes/api/webhooks/stripe/+server.ts`) handles the rest automatically.

## 9. Local dev

```yaml
# docker-compose.yml (per module)
services:
  {module}:
    build: .
    ports:
      - "8001:8000"   # use unique host port per module
    env_file: .env
    volumes:
      - ./src:/app/src
```

Stacker's `.env` should point each `PUBLIC_{ID}_API_URL` at the corresponding host port.

## 10. Deploy

```bash
gcloud run deploy {module} \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars-from-file .env.production.yaml
```

Workload Identity Federation in CI per the tech stack standard — no service account keys.

## 11. Verification checklist

- [ ] `GET /health` returns 200
- [ ] `GET /openapi.json` returns spec
- [ ] `GET /llms.txt` returns spec summary
- [ ] `GET /manifest` returns `{id, name, version, ...}`
- [ ] `/api/v1/*` returns 401 without JWT
- [ ] `/api/v1/*` returns 403 without subscription (with valid JWT)
- [ ] `/api/v1/*` returns 200 with valid JWT + subscription
- [ ] Module appears in stacker portal sidebar
- [ ] SubscriptionGate locks the module for unsubscribed users
- [ ] Stripe webhook flow grants/revokes correctly in dev
