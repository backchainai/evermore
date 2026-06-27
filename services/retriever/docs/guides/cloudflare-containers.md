# Cloudflare Containers Deployment

How the retriever FastAPI backend runs on Cloudflare Containers behind a Worker
router (ADR 0008).

## Architecture

The retriever ships as its existing Docker image. A thin Cloudflare Worker
fronts the container and forwards every inbound request to a container instance.
Application code references no Cloudflare primitives: all Cloudflare concerns
live at the deployment boundary (`worker/index.ts`, `wrangler.jsonc`).

| Component | Where |
|-----------|-------|
| Container image | `Dockerfile` + `entrypoint.sh` (uvicorn on `0.0.0.0:${PORT:-8000}`) |
| Worker router | `worker/index.ts` (`Container` subclass + `fetch` handler) |
| Wrangler config | `wrangler.jsonc` |
| Worker TS project | `worker/package.json`, `worker/tsconfig.json` |

The container connects directly to the Supabase pooler via `DATABASE_URL`.
Cloudflare Hyperdrive in front of Supabase is deferred to issue #109, so no
Hyperdrive binding is configured.

## Prerequisites

- Docker (to build and run the container image locally).
- Node.js and npm (for the Worker TS project under `worker/`).
- A Cloudflare account with the container platform enabled (deployment only).

## Local container image build

Run from the repository root. The build context is the service root so the
Dockerfile's `COPY` paths resolve unchanged:

```bash
docker build -t retriever services/retriever
```

You can run the image directly to smoke-test the API without Wrangler:

```bash
docker run --rm -p 8000:8000 --env-file services/retriever/.env retriever
```

## Local Worker plus container (wrangler dev)

Install the Worker dependencies once, then start Wrangler. `wrangler dev` builds
the container image from the Dockerfile and brings the Worker plus container up
together:

```bash
cd services/retriever/worker
npm install
npm run dev
```

`npm run dev` calls `wrangler dev --config ../wrangler.jsonc`. Requests to the
local Worker URL are routed to the container, which serves the FastAPI app
(health check at `/health`).

## Secrets

Non-secret config (`PORT`) is set via `vars` in `wrangler.jsonc`. Secrets
(`DATABASE_URL`, `LLM_GATEWAY_TOKEN`, `SUPABASE_URL`, etc.) are NOT committed.
Inject them per environment with Wrangler secret bindings:

```bash
cd services/retriever/worker
npx wrangler secret put DATABASE_URL --config ../wrangler.jsonc
npx wrangler secret put LLM_GATEWAY_TOKEN --config ../wrangler.jsonc
```

The Worker forwards these bindings into the container as environment variables
(`worker/index.ts`), where the Python app reads them via pydantic-settings.

## Deployment

Live Cloudflare deployment is operator-gated: it requires Cloudflare account
access and container-platform enablement, so it is not run from this guide.
Continuous deployment (deploy on merge with the Cloudflare API token in CI) is
deferred to issue #111. The manual command, for reference, is:

```bash
cd services/retriever/worker
npm run deploy
```
