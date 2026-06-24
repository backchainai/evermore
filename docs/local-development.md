# Local development

This guide brings up the Evermore portal (stacker) with one working module
(Retriever) on your machine. The other modules are disabled by default and
appear greyed as "In development".

## What runs where

| Component | Where it runs | URL / port |
|---|---|---|
| Supabase auth (GoTrue) | Supabase CLI (Docker) | http://localhost:54321 |
| App database (pgvector) | Docker Compose | localhost:5433 |
| Retriever API | native (uvicorn) | http://localhost:8001 |
| Stacker portal | native (vite) | http://localhost:5173 |

Supabase provides authentication only. The Retriever service stores its
documents and vectors in the separate pgvector container on 5433, not in
Supabase's bundled database. Retriever and stacker run natively for fast
reload; only the datastores run in Docker.

## Prerequisites

- Docker (running)
- [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started)
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- An LLM gateway for chat answers: chat, embeddings, and moderation route through one OpenAI-compatible gateway (Cloudflare AI Gateway by default). Set `LLM_GATEWAY_TOKEN` (the single BYOK secret) plus `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_GATEWAY_ID` (or `LLM_GATEWAY_URL` for another gateway). The gateway is required; without it the Retriever API fails fast on startup. To stand up a new gateway, see `docs/cloudflare-ai-gateway-setup.md`.

## Quick start

```
make env
```

Creates `.env` files from the examples. Then add your gateway config to
`services/retriever/.env`:

```
LLM_GATEWAY_TOKEN=...        # single BYOK token; provider keys live in the gateway
CLOUDFLARE_ACCOUNT_ID=...    # with CLOUDFLARE_GATEWAY_ID, derives the gateway URL
CLOUDFLARE_GATEWAY_ID=...    # (or set LLM_GATEWAY_URL for another OpenAI-compatible gateway)
```

Without a gateway configured, the Retriever API fails fast on startup, so chat
cannot return answers (the portal and navigation still work).

```
make dev
```

Brings up Supabase, the pgvector container, runs the Retriever migrations,
starts Retriever in the background, then runs stacker in the foreground. The
first run pulls Docker images and can take a few minutes.

Open http://localhost:5173/login, sign up (email confirmation is disabled, so
signup is instant), and you land on the Retriever chat. Ask a question to get
an answer.

Stop stacker with Ctrl-C, then:

```
make down
```

stops the background Retriever, the pgvector container, and Supabase.

## Persistent dev config (across worktrees)

`make env` copies the `.env.example` files into the current checkout with blank
secrets. A fresh worktree (for example a per-issue worktree) starts with no
`.env`, so this re-blanks your gateway token, account and gateway IDs, model
pins, and database and Supabase values every cycle.

`make link-env` keeps one persistent copy of your dev config outside any
worktree and symlinks each service's `.env` to it:

```
make link-env
```

On first run it stores your config under `~/.config/evermore/` (override with
`EVERMORE_DEV_HOME`), bootstrapping `retriever.env` and `stacker.env` from the
examples, or adopting an existing real `.env` if you already have one. It then
points `services/retriever/.env` and `apps/stacker/.env` at those store files.
Edit the values once in `~/.config/evermore/*.env`; because the store lives
outside the repo, the values survive worktree deletes and cannot be committed.
In any new worktree, run `make link-env` once and your config is present.

Keep model pins (`DEFAULT_LLM_MODEL`, `DEFAULT_EMBEDDING_MODEL`,
`FALLBACK_LLM_MODEL`) in the same store file to carry them across cycles. Use
`make env` instead if you prefer an independent `.env` per checkout.

## Manual steps

`make dev` is the sequence below; run the targets individually if you prefer
separate terminals.

```
make supabase-up    # cd apps/stacker && supabase start
make db-up          # cd apps/stacker && docker compose up -d   (pgvector on 5433)
make db-migrate     # cd services/retriever && uv run alembic upgrade head
make retriever-up   # cd services/retriever && uvicorn retriever.main:app --port 8001 --reload
make stacker-up     # cd apps/stacker && npm install && npm run dev
```

Confirm the Supabase keys after `supabase start`:

```
cd apps/stacker && supabase status -o json
```

Copy `ANON_KEY` into `apps/stacker/.env` (`PUBLIC_SUPABASE_ANON_KEY`).

## Module feature flags

`apps/stacker/.env` carries `PUBLIC_ENABLED_MODULES`, a comma-separated
allow-list of module ids. The default is `retriever`. Modules left out render
greyed as "In development" and their `/app/<id>/*` routes return 404. Unset or
empty enables every registered module.

## Auth note (JWKS vs HS256)

Retriever validates user tokens against Supabase's JWKS endpoint
(`<SUPABASE_URL>/auth/v1/.well-known/jwks.json`), expecting asymmetric
(RS256/ES256) signing keys. The portal login itself works regardless. If a
local Supabase instance issues legacy HS256 tokens, Retriever's protected
routes (chat) will reject them; resolving this is part of the Retriever
local-auth setup. See the Phase 1 issue for the current resolution.

## Do not run two databases on 5432

The pgvector container is published on 5433 specifically to avoid colliding
with a host Postgres or Supabase's bundled database. Do not remap it to 5432.
