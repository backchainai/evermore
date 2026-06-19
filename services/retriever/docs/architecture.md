# Retriever Architecture

AI-powered Q&A system for shelter volunteers, using RAG to answer questions from policy/procedure documents.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENT PIPELINE                          │
│  [Word/MD/Text] → [Loaders] → [Chunker] → [Embeddings] → [DB] │
└─────────────────────────────────────────────────────────────────┘
                                                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                        QUERY FLOW                               │
│  [User Question] → [Embed] → [Retrieve] → [Claude] → [Answer]  │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                      WEB APPLICATION                            │
│  [SvelteKit Frontend] ←→ [FastAPI Backend] ←→ [Supabase Auth]  │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Style: Cloud-Native Microservices

Separate backend and frontend deployables with managed infrastructure. See [ADR-003](decisions/003-system-architecture.md).

**Why this approach:**
- Independent deployment of backend (Cloud Run) and frontend (Cloudflare Pages)
- Managed database (Supabase) eliminates operational burden
- API-first: frontend is a typed API consumer via `RetrieverApi` client
- Dependencies point inward (business logic doesn't know about FastAPI)

```
┌──────────────────────────────┐    ┌──────────────────────────┐
│     SvelteKit Frontend       │    │   Supabase               │
│   (Cloudflare Pages)         │    │   (Managed Postgres +    │
│                              │───▶│    pgvector + Auth)       │
│  Auth state, Chat UI,        │    │                          │
│  Admin (doc upload/manage)   │    └──────────────────────────┘
└──────────────┬───────────────┘                 ▲
               │ REST/JSON API (v1)              │
               ▼                                 │
┌──────────────────────────────┐                 │
│      FastAPI Backend         │─────────────────┘
│      (Cloud Run)             │
│                              │───▶ Cloudflare AI Gateway
│  Auth, RAG, Documents,       │       → OpenRouter (LLM)
│  Messages, Observability     │       → OpenAI (Embeddings)
└──────────────────────────────┘
```

## Tech Stack

### Backend (Python 3.13+)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | FastAPI + Pydantic 2.x | Async, modern, auto-generated OpenAPI |
| ORM | SQLAlchemy 2.0 async + asyncpg | Async Postgres, Alembic migrations |
| LLM | OpenRouter via Cloudflare AI Gateway | Multi-model, OpenAI-compatible API |
| LLM Abstraction | Protocol-based provider interface | Swap providers without code changes |
| Embeddings | OpenAI `text-embedding-3-small` via AI Gateway | Cost-effective, high quality |
| Vector DB | Supabase Postgres + pgvector | HNSW cosine + GIN full-text, managed |
| Auth | Supabase Auth / JWKS (RS256 JWT) via PyJWT | Server-verified tokens, RLS |
| Observability | structlog (JSON) + OpenTelemetry + Langfuse | GCP Cloud Trace / Jaeger / console |
| Resilience | tenacity + aiobreaker | Retries, circuit breakers |

### Frontend (SvelteKit)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | SvelteKit + Svelte 5 runes | SSR, file-based routing, modern reactivity |
| UI Library | Skeleton UI v4 | Tailwind-based, accessible components |
| Styling | Tailwind CSS v4 | Utility-first, cerberus theme |
| Auth | Supabase SSR (`@supabase/ssr`) | Server-verified auth, cookie-based sessions |
| API Client | Typed `RetrieverApi` class | Mirrors backend Pydantic schemas |

### Infrastructure

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend Hosting | Google Cloud Run | Serverless, auto-scaling, `gcloud run deploy --source` |
| Frontend Hosting | Cloudflare Pages | Global CDN, SvelteKit adapter |
| Database | Supabase Postgres + pgvector | Managed, includes Auth + RLS |
| LLM Gateway | Cloudflare AI Gateway | Rate limiting, caching, logging |
| Observability | GCP Cloud Trace + Langfuse | Distributed tracing + LLM observability |
| Secrets | Environment variables + GCP Secret Manager | Standard practice |
| CI/CD | GitHub Actions | Path-filtered backend/frontend jobs |

## Project Structure

### Monorepo Layout

```
retriever/
├── .github/workflows/      # CI/CD: ci.yml, claude.yml, release.yml
├── backend/                 # Python backend
│   ├── src/retriever/       # Application source
│   ├── tests/               # Backend tests
│   └── pyproject.toml       # uv-managed dependencies
├── frontend/                # SvelteKit frontend
│   ├── src/                 # SvelteKit source
│   └── package.json
└── docs/                    # Architecture docs and ADRs
```

### Backend Structure (`backend/src/retriever/`)

```
retriever/
├── config.py               # pydantic-settings; ai_gateway_base_url computed field
├── main.py                 # FastAPI app, /health (DB+pgvector checks), CORS
├── models/                 # SQLAlchemy 2.0 async: User, Message, Document
├── infrastructure/
│   ├── cache/              # PgSemanticCache (pgvector cosine similarity)
│   ├── database/           # async session factory (asyncpg)
│   ├── embeddings/         # OpenAIEmbeddingProvider (via AI Gateway)
│   ├── llm/                # OpenRouterProvider + FallbackLLMProvider (via AI Gateway)
│   ├── observability/      # structlog JSON + OTel (GCP/OTLP/console) + Langfuse + RequestIdMiddleware
│   └── vectordb/           # PgVectorStore (HNSW cosine + GIN full-text)
└── modules/
    ├── auth/               # JwksValidator, require_auth, require_admin
    ├── documents/          # upload/list/delete with /api/v1/documents endpoints
    ├── messages/           # conversation history with /api/v1/history endpoints
    └── rag/                # chunker, loader, prompts, hybrid retriever, RAG service, /api/v1/ask
```

### Frontend Structure (`frontend/src/`)

```
src/
├── hooks.server.ts                 # Supabase SSR auth + route guards
├── app.d.ts                        # App.Locals, App.PageData type augmentation
├── app.css                         # Tailwind v4 + Skeleton cerberus theme
├── lib/
│   ├── supabase.ts                 # createBrowserClient factory
│   ├── server/supabase.ts          # createSupabaseServerClient factory
│   ├── api/
│   │   ├── types.ts                # TypeScript interfaces (mirrors backend Pydantic)
│   │   └── client.ts               # RetrieverApi class (typed HTTP client)
│   └── components/
│       ├── ChatMessage.svelte      # Message bubble (user/assistant)
│       ├── ChatInput.svelte        # Textarea + send (Enter/Shift+Enter)
│       ├── ConfidenceBadge.svelte  # RAG confidence pill (high/medium/low)
│       ├── SourceCitation.svelte   # Expandable source chunks
│       ├── ClearHistoryButton.svelte # Clear with confirmation
│       ├── DocumentList.svelte     # Table (desktop) / cards (mobile)
│       ├── DocumentUpload.svelte   # File input + validation
│       └── ErrorAlert.svelte       # Reusable error display
├── routes/
│   ├── +layout.svelte              # AppBar, nav, auth state listener
│   ├── +layout.server.ts           # Pass session/user/cookies to client
│   ├── +layout.ts                  # Browser/server Supabase client
│   ├── +page.svelte                # Landing (redirect to /chat if authed)
│   ├── +error.svelte               # Global error page
│   ├── login/                      # Email+password form action
│   ├── logout/                     # POST → signOut + redirect
│   ├── chat/                       # RAG Q&A + history + citations
│   └── admin/                      # Document upload/list/delete (admin only)
└── tests/e2e/                      # Playwright tests
```

## Key Design Patterns

### LLM Provider Abstraction

Protocol-based interface for swappable LLM providers. Providers receive `base_url` at construction time from `settings.ai_gateway_base_url`:

```python
class LLMProvider(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None
    ) -> str: ...
```

Construction pattern:
```python
provider = OpenRouterProvider(
    api_key=settings.openrouter_api_key,
    base_url=settings.ai_gateway_base_url,  # routes via Cloudflare if configured
)
```

See [ADR-002](decisions/002-llm-provider-strategy.md).

### Module Structure

Each module in `backend/src/retriever/modules/` is self-contained:

```
module_name/
├── __init__.py
├── routes.py       # FastAPI routes
├── services.py     # Business logic
├── schemas.py      # Pydantic models (request/response)
└── repos.py        # Data access via SQLAlchemy async session
```

### Infrastructure Patterns

| Pattern | Implementation |
|---------|---------------|
| Database | Async session factory with asyncpg, Alembic migrations |
| Embeddings | OpenAI-compatible provider routed through AI Gateway |
| LLM Gateway | `ai_gateway_base_url` computed field: Cloudflare if configured, OpenRouter fallback |
| Observability | Auto-selected OTel exporter: GCP Cloud Trace → OTLP/gRPC (Jaeger) → Console → no-op |
| Vector DB | PgVectorStore with HNSW cosine index + GIN full-text for hybrid retrieval |
| Semantic Cache | PgSemanticCache using pgvector cosine similarity for query deduplication |
| Auth | RS256 JWKS validation via PyJWT; admin from `app_metadata.is_admin` |

### Configuration

Use `pydantic-settings` for all configuration. Environment variables override defaults. Computed fields derive values from primitives (e.g., `ai_gateway_base_url` from `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_GATEWAY_ID`).

## Related Documents

- [Implementation Roadmap](implementation-plan.md)
- [Development Standards](development-standards.md)
- [Architecture Decision Records](decisions/)
