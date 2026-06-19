# CHANGELOG

<!-- version list -->

## [Unreleased] — Stack Migration

### Added
- **Phase 5 — LLM Gateway (Cloudflare AI Gateway)** (`backend/`)
  - `retriever.infrastructure.llm` — `OpenRouterProvider` routes all LLM calls through `settings.ai_gateway_base_url` (Cloudflare AI Gateway when configured, OpenRouter otherwise)
  - `FallbackLLMProvider` — model degradation fallback with automatic retry on primary failure
  - `LLMProvider` Protocol — swappable backends without changing business logic
  - `retriever.infrastructure.embeddings` — `OpenAIEmbeddingProvider` routes embedding calls through AI Gateway
  - `EmbeddingProvider` Protocol — pluggable embedding backends
  - Both providers include circuit breaker (`aiobreaker`) + retry (`tenacity`) resilience patterns
  - Config additions: `default_llm_model`, `default_embedding_model`, `llm_timeout_seconds`
  - `aiobreaker` mypy override added (`follow_imports = "skip"`, no upstream stubs)
  - 72 tests passing, 86% coverage
- **Phase 4 — Auth (JWKS-based JWT validation)** (`backend/`)
  - `retriever.modules.auth.JwksValidator` — RS256 JWT decode via Supabase JWKS endpoint (`PyJWT[crypto]`)
  - `require_auth` FastAPI dependency — validates Bearer token, returns `AuthUser` dataclass
  - `require_admin` FastAPI dependency — gates routes on `app_metadata.is_admin`
  - `AuthUser` frozen dataclass: `sub`, `email`, `is_admin`
  - `PyJWKClient` key caching (300 s TTL) without `lru_cache` — Supabase key rotations picked up without process restart
  - Missing `sub` claim raises 401 (not unhandled 500)
  - 8 unit tests (no live Supabase required): valid/expired/bad-sig tokens, missing auth 401, non-admin 403, admin 200
- **Phase 3 — Database layer** (`backend/`)
  - SQLAlchemy 2.0 async models: `User`, `Message`, `Document` with `tenant_id` on all tables
  - `PgVectorStore` — HNSW cosine search + GIN full-text index via pgvector 0.4
  - `PgSemanticCache` — similarity-threshold cache backed by pgvector
  - FastAPI session DI (`get_session`) with auto-commit/rollback
  - 4 Alembic migrations: initial schema → vector storage → semantic cache → `updated_at` trigger
  - 32 tests (22 unit + 9 integration + 1 edge case), 91% coverage
- `frontend/` — SvelteKit + Svelte 5 runes + Skeleton UI v3 + Tailwind 4 skeleton
  - Cloudflare Pages adapter (`@sveltejs/adapter-cloudflare`)
  - Skeleton UI `cerberus` theme with AppBar layout
  - Supabase client stub (`src/lib/supabase.ts`) wired to `PUBLIC_SUPABASE_*` env vars
  - `wrangler.toml` for Cloudflare Pages deploy
  - Playwright e2e smoke tests (AppBar title, page heading, screenshot baseline)
- `docker-compose.yml` — frontend service added (node:22-slim, port 5173)
- `backend/` — standalone uv Python project (`retriever` package, Python 3.13+)
- FastAPI app with `/health` endpoint, CORS middleware (explicit origins, no wildcards)
- pydantic-settings `Settings` with `SecretStr` for all secrets, wildcard-origin validator
- Cloudflare AI Gateway computed `ai_gateway_base_url` field
- structlog JSON logging + OpenTelemetry tracing bootstrap (console exporter in dev)
- `docker-compose.yml` — backend + pgvector/pg17 Postgres
- `docker-compose.test.yml` — ephemeral test Postgres (tmpfs, port 5433)
- `.env.example` updated to new stack schema

## v1.1.0 (2025-12-27)

### Bug Fixes

- Add missing documents module to git ([#16](https://github.com/ckrough/retriever/pull/16),
  [`b38b865`](https://github.com/ckrough/retriever/commit/b38b8655aef3c03ae7fcbb1742fb71dc8714d11e))

### Features

- Add document management via admin web interface
  ([#16](https://github.com/ckrough/retriever/pull/16),
  [`b38b865`](https://github.com/ckrough/retriever/commit/b38b8655aef3c03ae7fcbb1742fb71dc8714d11e))

### Testing

- Add comprehensive tests for documents module ([#16](https://github.com/ckrough/retriever/pull/16),
  [`b38b865`](https://github.com/ckrough/retriever/commit/b38b8655aef3c03ae7fcbb1742fb71dc8714d11e))


## v1.0.0 (2025-12-27)

- Initial Release
