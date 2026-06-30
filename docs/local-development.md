# Local development

This guide brings up the Evermore portal (stacker) on your machine. There are
two paths:

- **`make dev`** runs the portal with the Retriever module against a real LLM
  gateway. The other modules are disabled and appear greyed as "In development".
- **`make dev-full`** runs the whole stack locally with **no paid credentials**:
  Supabase, both service databases, an offline LLM stub, Retriever, Pet Data, and
  the portal. Use this for rapid full-stack development. Answers are fake (the
  stub returns canned text and deterministic embeddings), but every screen
  renders and the request paths exercise end to end.

## What runs where

| Component | Where it runs | URL / port | Stack |
|---|---|---|---|
| Supabase auth (GoTrue) | Supabase CLI (Docker) | http://localhost:54321 | both |
| Retriever database (pgvector) | Docker Compose | localhost:5433 | both |
| Pet Data database (pgvector) | Docker Compose | localhost:5434 | dev-full |
| LLM stub gateway | native (python3) | http://localhost:8099 | dev-full |
| Retriever API | native (uvicorn) | http://localhost:8001 | both |
| Pet Data API | native (uvicorn) | http://localhost:8002 | dev-full |
| Stacker portal | native (vite) | http://localhost:5173 | both |

Supabase provides authentication only. Each service stores its documents and
vectors in its own pgvector container (Retriever on 5433, Pet Data on 5434), not
in Supabase's bundled database. Services and stacker run natively for fast
reload; only the datastores (and, under `make dev`, nothing else) run in Docker.

## Prerequisites

- Docker (running)
- [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started)
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- Python 3 on `PATH` (for the offline LLM stub used by `make dev-full`; standard library only, no venv)
- An LLM gateway, **only for `make dev`**: chat, embeddings, and moderation route through one OpenAI-compatible gateway (Cloudflare AI Gateway by default). Set `LLM_GATEWAY_TOKEN` (the single BYOK secret) plus `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_GATEWAY_ID` (or `LLM_GATEWAY_URL` for another gateway). Under `make dev` the gateway is required; without it the Retriever API fails fast on startup. `make dev-full` does not need this: it runs the in-repo stub instead. To stand up a real gateway, see `docs/cloudflare-ai-gateway-setup.md`.

## Fully local stack (no credentials)

The fastest path to the whole app on your machine, with no LLM gateway, no
accounts, and no secrets:

```
make env        # create the three .env files from the examples
make dev-full   # Supabase + both databases + LLM stub + Retriever + Pet Data + portal
```

`make dev-full` brings up Supabase, both pgvector databases, the offline LLM
stub, Retriever and Pet Data (in the background), then stacker in the
foreground. It points the Retriever's `LLM_GATEWAY_URL` at the stub and enables
both modules (`PUBLIC_ENABLED_MODULES=retriever,petdata`) for this run only, so
nothing in your `.env` files changes.

After step 1 (`make env`), copy the Supabase publishable key into
`apps/stacker/.env` as shown in [step 4](#4-copy-the-supabase-anon-key-into-the-portal)
(login needs it). The first `make dev-full` run pulls Docker images and can take
a few minutes.

Open http://localhost:5173/login, sign in, and you land on the portal with both
Retriever and Pet Data available. Chat returns a clearly-labeled stub answer.
Stop stacker with Ctrl-C, then `make down`.

The offline LLM stub (`tools/llm-stub/llm_stub.py`) is a dependency-light,
OpenAI-compatible server: canned chat replies, deterministic unit-normalized
1536-dim embeddings (matching the Retriever's pinned embedding dimension), and
always-safe moderation. Run it on its own with `make llm-stub` (logs to
`.dev/llm-stub.log`).

The rest of this guide covers the `make dev` path (real gateway, Retriever
only).

## Quick start

Run these in order. The Supabase anon key (step 4) only exists once Supabase is
running (step 3), so the steps are sequenced around that.

### 1. Create the `.env` files

```
make env
```

Creates the `.env` files from the examples and prints each path:

- `services/retriever/.env` (Retriever service config)
- `apps/stacker/.env` (portal config)
- `services/petdata/.env` (Pet Data service config)

`make env` also warns if an existing `.env` still sets a variable name that has
been retired from the template (for example `OPENROUTER_API_KEY` or
`SUPABASE_ANON_KEY`); those are silently ignored at runtime, so refresh the file
from its `.env.example` if you see the warning.

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

`apps/stacker/.env` ships a `PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key`
placeholder. Replace it with the real key:

```
cd apps/stacker && supabase status -o json
```

Copy the `ANON_KEY` value into `PUBLIC_SUPABASE_PUBLISHABLE_KEY`. Login fails while the
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
make supabase-keys  # generate the local ES256 JWT signing key if absent
make supabase-up    # cd apps/stacker && supabase start  (runs supabase-keys first)
make db-up          # cd apps/stacker && docker compose up -d   (Retriever pgvector on 5433)
make db-migrate     # cd services/retriever && uv run alembic upgrade head
make retriever-up   # cd services/retriever && uvicorn retriever.main:app --port 8001 --reload
make stacker-up     # cd apps/stacker && npm install && npm run dev
```

The `make dev-full` stack adds these:

```
make llm-stub       # offline OpenAI-compatible LLM stub on :8099 (background)
make petdata-db-up  # cd services/petdata && docker compose up -d   (Pet Data pgvector on 5434)
make petdata-migrate# cd services/petdata && uv run alembic upgrade head
make petdata-bg     # cd services/petdata && uvicorn petdata.main:app --port 8002 --reload (background)
```

Running Retriever by hand against the stub: export
`LLM_GATEWAY_URL=http://localhost:8099/v1` before `make retriever-up` (an
environment variable overrides the `.env` value).

Confirm the Supabase keys after `supabase start`:

```
cd apps/stacker && supabase status -o json
```

Copy `ANON_KEY` into `apps/stacker/.env` (`PUBLIC_SUPABASE_PUBLISHABLE_KEY`).

## Module feature flags

`apps/stacker/.env` carries `PUBLIC_ENABLED_MODULES`, a comma-separated
allow-list of module ids. The default is `retriever`. Modules left out render
greyed as "In development" and their `/app/<id>/*` routes return 404. Unset or
empty enables every registered module. `make dev-full` sets this to
`retriever,petdata` for its run, so Pet Data appears without editing `.env`.

## Auth note (asymmetric JWT signing)

Retriever validates user tokens against Supabase's JWKS endpoint
(`<SUPABASE_URL>/auth/v1/.well-known/jwks.json`) and accepts asymmetric
(RS256/ES256) signatures only. Local Supabase's default symmetric HS256 tokens
would be rejected on protected routes (chat), so local signing is configured to
be asymmetric: `apps/stacker/supabase/config.toml` sets `signing_keys_path`, and
`make supabase-keys` (run automatically by `make supabase-up`) generates an
ES256 key at `apps/stacker/supabase/signing_keys.json`. That file is a local
secret and is gitignored; each checkout regenerates it on first start. With it
in place, GoTrue issues ES256 tokens that Retriever validates via JWKS, so
authenticated chat works locally end to end.

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
