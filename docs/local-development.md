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
- LLM API keys for chat answers: an OpenRouter key and an OpenAI key

## Quick start

```
make env
```

Creates `.env` files from the examples. Then add your keys to
`services/retriever/.env`:

```
OPENROUTER_API_KEY=...   # chat model (default anthropic/claude-sonnet-4)
OPENAI_API_KEY=...       # embeddings + moderation
```

Without these, the portal and navigation work but chat cannot return answers.

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
