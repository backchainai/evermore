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

Run these in order. The Supabase anon key (step 4) only exists once Supabase is
running (step 3), so the steps are sequenced around that.

### 1. Create the `.env` files

```
make env
```

Creates two `.env` files from the examples and prints each path:

- `services/retriever/.env` (Retriever service config)
- `apps/stacker/.env` (portal config)

### 2. Add your LLM gateway config

In `services/retriever/.env`:

```
LLM_GATEWAY_TOKEN=...        # single BYOK token; provider keys live in the gateway
CLOUDFLARE_ACCOUNT_ID=...    # with CLOUDFLARE_GATEWAY_ID, derives the gateway URL
CLOUDFLARE_GATEWAY_ID=...    # (or set LLM_GATEWAY_URL for another OpenAI-compatible gateway)
```

Without a gateway configured, the Retriever API fails fast on startup, so chat
cannot return answers (the portal and navigation still work).

The gateway also needs working provider access, which is separate from the
token. `LLM_GATEWAY_TOKEN` only authenticates you to the gateway; the gateway
itself must be able to reach the model providers, either through a BYOK provider
key configured in the gateway (the defaults are `anthropic/claude-sonnet-4-6`
for chat and `openai/text-embedding-3-small` for embeddings) or, on Cloudflare,
through available account credits. Without provider access the app still starts
and login works, but a chat question fails: the embeddings or chat call returns
an error (commonly `402 Payment Required` from Cloudflare for missing credits).
See [Troubleshooting](#troubleshooting).

### 3. Start Supabase

```
make supabase-up
```

The first run pulls Docker images and can take a few minutes.

### 4. Copy the Supabase anon key into the portal

`apps/stacker/.env` ships a `PUBLIC_SUPABASE_ANON_KEY=your-anon-key`
placeholder. Replace it with the real key:

```
cd apps/stacker && supabase status -o json
```

Copy the `ANON_KEY` value into `PUBLIC_SUPABASE_ANON_KEY`. Login fails while the
placeholder is in place.

### 5. Start everything else

```
make dev
```

Brings up the pgvector container, runs the Retriever migrations, starts
Retriever in the background, then runs stacker in the foreground. Supabase is
already up from step 3; `make dev` re-runs `supabase start`, which is a no-op
when Supabase is already running.

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

## Troubleshooting

### Chat shows "Load failed" or an error

The Retriever runs in the background under `make dev`, so its errors do not
appear in the foreground terminal (which is running stacker). Read its log:

```
tail -f .dev/retriever.log
```

A failed chat question is usually an LLM-gateway error on `POST /api/v1/ask`:

- `402 Payment Required` ("Insufficient wholesale credits"): the gateway has no
  provider access. Add a BYOK provider key to the gateway, or add credits in the
  Cloudflare dashboard. See step 2 above.
- `400 Bad Request` ("Compatibility endpoint: moderations is not supported"):
  Cloudflare AI Gateway does not proxy the moderations endpoint. This is logged
  and non-fatal; it does not by itself stop a chat answer.
- `model ... was not found`: a model pin uses the wrong id. Anthropic ids use
  dashes, not dots (`claude-sonnet-4-6`, not `claude-sonnet-4.6`).

An unhandled server error currently reaches the browser as a generic "Load
failed" with no detail, because the 500 response omits CORS headers; the real
cause is in `.dev/retriever.log`. Tracked in issue #97.

### Retriever did not start

`make dev` aborts or chat returns nothing because the background Retriever
exited. Check `.dev/retriever.log` for `Address already in use`: a previous run
may have left a uvicorn bound to 8001.

```
lsof -nP -iTCP:8001 -sTCP:LISTEN
```

Run `make down` before `make dev`, or kill the stale process, then retry.

## Do not run two databases on 5432

The pgvector container is published on 5433 specifically to avoid colliding
with a host Postgres or Supabase's bundled database. Do not remap it to 5432.
