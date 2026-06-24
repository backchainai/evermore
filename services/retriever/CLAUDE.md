# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Context Loading:** Use the [Documentation Index](#documentation-index) below to find and load only relevant docs for your current task. Avoid loading all documentation at once.

## Project: Retriever

AI-powered Q&A system for shelter volunteers, using RAG to answer questions from policy/procedure documents.

## Issue Tracking

Evermore uses GitHub Issues for tracking (see ADR 0002 and the root `CLAUDE.md`). Beads is retired in this repo: do not run `bd init` here.

**Architecture:** Cloud-native microservices

### Stack (backend only — frontend lives in [`apps/stacker`](../../apps/stacker/))
- **Backend:** Python 3.13+, FastAPI, Pydantic 2.x, SQLAlchemy 2.0 async
- **Document Processing:** Docling (PDF, DOCX, PPTX, XLSX, HTML, images, MD, TXT) with HybridChunker
- **LLM:** One OpenAI-compatible LLM gateway (Cloudflare AI Gateway by default), `OpenAICompatProvider` for chat
- **Vector DB:** Supabase Postgres + pgvector (HNSW cosine + GIN full-text)
- **Auth:** Supabase Auth / JWKS (RS256 JWT), RLS
- **Observability:** structlog (JSON) + OpenTelemetry (GCP Cloud Trace / Jaeger) + Langfuse
- **Deploy:** Cloud Run

## Commands

### Backend (run from the service root `services/retriever/`)

```bash
# Install dependencies (dev)
uv sync --dev

# Run development server
uv run uvicorn retriever.main:app --reload --port 8000

# Linting and formatting
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/

# Type checking (strict mode required — use python -m mypy, NOT uv run mypy)
uv run python -m mypy src/ --strict

# Run tests with coverage (80% minimum)
uv run python -m pytest tests/ --cov=src/retriever --cov-report=term-missing --cov-fail-under=80

# Security audit
uv run pip-audit

# All quality checks (run before PR)
uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/ && uv run python -m mypy src/ --strict && uv run python -m pytest tests/ --cov=src/retriever --cov-fail-under=80
```

## Local Development

The dev workflow runs infrastructure in Docker + Supabase CLI, with the backend running natively for fast live reload. The frontend lives in the [`apps/stacker`](../../apps/stacker/) portal.

```bash
# 1. Start Supabase (auth, realtime, storage)
supabase start

# 2. Start infrastructure (pgvector postgres + jaeger)
docker compose up -d

# 3. Backend
cd services/retriever && uv sync --dev
uv run alembic upgrade head          # first time / after migrations
uv run uvicorn retriever.main:app --reload --port 8000

# 4. Stop everything
docker compose down && supabase stop
```

### Local dev: LLM gateway

Outbound model calls (chat, embeddings, moderation) route through one OpenAI-compatible LLM gateway (Cloudflare AI Gateway by default) via a single `AsyncOpenAI` client built by `build_gateway_client`. Chat uses `OpenAICompatProvider`. The gateway holds the provider keys (BYOK), so the only LLM secret needed to run against it is `LLM_GATEWAY_TOKEN` (sent on the `llm_gateway_auth_header`, default `cf-aig-authorization`), alongside `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_GATEWAY_ID`. Set `LLM_GATEWAY_URL` to swap to any other OpenAI-compatible gateway.

The gateway is required: there is no no-gateway path. When none is configured, `settings.llm_gateway_base_url` raises `ValueError` and the app fails fast with a clear error, so every environment that makes model calls (local dev, CI, production) configures a gateway. See ADR `docs/adr/0007-llm-gateway-consolidation.md`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup instructions including prerequisites and environment configuration.

## CI/CD

### Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| CI | `.github/workflows/ci.yml` | Push/PR to main |
| Claude Code | `.github/workflows/claude.yml` | `@claude` in PR/issue comments |
| Release | `.github/workflows/release.yml` | Semantic release |

### CI Path Filtering

CI uses `dorny/paths-filter` — only changed stacks run:

| Stack | Path Filter | Jobs |
|-------|-------------|------|
| Retriever | `services/retriever/**` | lint, typecheck, test |

The `all-checks` gate job requires all triggered jobs to pass (skipped jobs are OK).

> **Note:** Frontend CI jobs (`check`, `build`, `e2e`) should be removed — frontend now lives in stacker.

## Project Structure

### Repository Layout

```
services/retriever/
├── src/retriever/          # Application source
├── tests/                  # Tests
├── alembic/                # Database migrations
├── docs/                   # Architecture docs and ADRs
└── pyproject.toml          # uv-managed dependencies
```

> **Frontend** lives in the [`apps/stacker`](../../apps/stacker/) portal.

### Backend Structure (`src/retriever/`)

```
retriever/
├── config.py               # pydantic-settings; llm_gateway_base_url computed field
├── main.py                 # FastAPI app, /health, CORS
├── models/                 # SQLAlchemy 2.0 async: User, Message, Document
├── infrastructure/
│   ├── cache/              # PgSemanticCache (pgvector cosine similarity)
│   ├── database/           # async session factory
│   ├── embeddings/         # OpenAIEmbeddingProvider (via LLM gateway)
│   ├── llm/                # OpenAICompatProvider + FallbackLLMProvider (via LLM gateway)
│   ├── observability/      # structlog JSON + OTel (GCP/OTLP/console) + Langfuse + RequestIdMiddleware
│   ├── safety/             # PromptInjectionDetector, OpenAIModerator, HallucinationDetector, ConfidenceScorer, SafetyService
│   └── vectordb/           # PgVectorStore (HNSW cosine + GIN full-text)
└── modules/
    ├── auth/               # JwksValidator, require_auth, require_admin
    ├── documents/          # upload/list/delete with /api/v1/documents endpoints
    ├── messages/           # conversation history with /api/v1/history endpoints
    └── rag/                # Docling processor, hybrid retriever, RAG service, /api/v1/ask
        ├── docling_processor.py  # DoclingProcessor + FormatAwareProcessor (lazy Docling imports)
        ├── exceptions.py         # DocumentConversionError, UnsupportedFormatError
        ├── loader.py             # File validation, format-aware size limits
        ├── prompts.py            # RAG system prompt with heading/table instructions
        ├── retriever.py          # HybridRetriever (semantic + keyword search)
        ├── schemas.py            # DocumentProcessor protocol, ProcessingResult, Chunk, etc.
        └── service.py            # RAGService: index_document(bytes), ask()
```

## Backend Gotchas

These are non-obvious issues discovered during development:

**mypy invocation:** Always use `uv run python -m mypy`, not `uv run mypy`. The `mypy` binary is not on PATH in the uv venv; `python -m mypy` is the reliable path.

**aiobreaker mypy override:** `aiobreaker` has no type stubs. Using `ignore_missing_imports = true` alone is insufficient — set `follow_imports = "skip"` in the override block:
```toml
[[tool.mypy.overrides]]
module = "aiobreaker"
follow_imports = "skip"
```

**tenacity must NOT share the aiobreaker override:** `tenacity` ships `py.typed`. If you add it to the same override as aiobreaker, mypy silently drops type inference for `@retry` decorators, causing false-positive errors.

**LLM gateway routing:** `settings.llm_gateway_base_url` resolves the gateway base URL. `LLM_GATEWAY_URL` overrides it to any OpenAI-compatible gateway; otherwise `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_GATEWAY_ID` derive the Cloudflare AI Gateway URL; with neither set it raises `ValueError` (the gateway is required, there is no no-gateway path). All LLM and embedding providers must use this property, not hardcoded URLs.

**File upload:** Uses ephemeral FS (process-and-discard) — processes, chunks, and embeds content, stores in pgvector, discards raw file. If Supabase Storage is needed later, only the upload handler changes.

**Docling document processing:** Document processing uses Docling's `DocumentConverter` + `HybridChunker`. All Docling imports are lazy (inside methods) to avoid loading PyTorch at import time. `FormatAwareProcessor` routes `.md`/`.txt` through a lightweight `SimplePipeline` (no ML) and binary formats (PDF, DOCX, PPTX, XLSX, HTML, images) through the full ML pipeline. The `process()` method is sync; `RAGService.index_document()` wraps it with `asyncio.to_thread()`.

**Docling mypy override:** Docling ships `py.typed` but has complex internal types. Using `ignore_missing_imports = true` alone causes type-check failures — set `follow_imports = "skip"` in the override block (same pattern as aiobreaker).

**Docling OpenAITokenizer API:** `OpenAITokenizer` takes `tokenizer=tiktoken.encoding_for_model("text-embedding-3-small")` (a `tiktoken.Encoding` object), NOT `model_name="text-embedding-3-small"`. Online docs and context7 show the old API — always check the actual constructor signature.

**Environment files:** This service reads its own `.env` via pydantic-settings (do NOT add `extra="ignore"`: it hides typos). In production, the deploy target sets its env vars directly. See `.env.example`. The SvelteKit frontend is a separate app at [`apps/stacker`](../../apps/stacker/) with its own `.env` for `PUBLIC_*` vars; the two are not shared.

**OTel exporter selection:** `tracing.py` auto-selects exporter: GCP Cloud Trace (`gcp_project_id` set) → OTLP/gRPC (`OTEL_EXPORTER_OTLP_ENDPOINT` set, for Jaeger) → Console (debug) → no-op. GCP exporter gracefully falls through if credentials are unavailable (local dev without ADC).

**Langfuse @observe() is a no-op without credentials:** The decorator is always imported but only sends traces when `langfuse_secret_key`, `langfuse_public_key`, and `langfuse_host` are all set. Safe to ignore in local dev.

## Git Workflow: GitHub Flow

**Branch from main, PR back to main.**

```
main (protected) ← feature branches via PR
```

### Branch Naming
```
feature/add-user-auth
fix/chat-input-validation
docs/update-readme
refactor/simplify-rag-pipeline
test/add-rag-coverage
chore/update-dependencies
```

### Commit Messages (Conventional Commits)
```
feat: add volunteer login functionality
fix: resolve chat timeout on slow connections
docs: add API endpoint documentation
test: add coverage for RAG retrieval
refactor: extract LLM provider interface
chore: update dependencies
```

**Format:** `<type>: <description>` (lowercase, imperative mood, no period)

## Code Standards

### Type Hints (Required)
All function signatures must have type hints, including return types.

```python
# Good
async def ask_question(question: str, user_id: UUID) -> Answer:
    ...

# Bad - missing types
async def ask_question(question, user_id):
    ...
```

### Docstrings (Google Style)
Required for public APIs and non-trivial functions.

```python
def generate_answer(question: str, context: list[str]) -> str:
    """Generate an answer using retrieved context.

    Args:
        question: The user's question.
        context: Retrieved document chunks relevant to the question.

    Returns:
        The generated answer text.

    Raises:
        LLMProviderError: If the LLM API call fails.
    """
```

### Testing
- **Coverage:** 80% minimum for new code
- **Naming:** `test_<function>_<scenario>_<expected>`
- **Categories:** `tests/unit/`, `tests/integration/`, `tests/e2e/`

```python
def test_ask_question_with_valid_input_returns_answer():
    ...

def test_ask_question_with_empty_context_returns_fallback():
    ...
```

### Error Handling
- Never bare `except:` - always specify exception types
- Chain exceptions with `from` for context
- Use custom exception hierarchy for domain errors

## PR Requirements

Before opening a PR:
- [ ] All tests pass (`pytest`)
- [ ] Types check (`mypy --strict`)
- [ ] Linting passes (`ruff check && ruff format`)
- [ ] New code has tests (80% coverage)
- [ ] Documentation updated if needed
- [ ] ADR created for significant architectural decisions

**Review process:**
- 1 approval required
- CI must pass
- Squash merge to main

## Security

**Never commit:**
- API keys, secrets, passwords
- `.env` files (use `.env.example` as template)
- Credentials of any kind

**Required:**
- Secrets in environment variables only
- Input validation on all endpoints
- Content moderation on user input (OpenAI Moderation API)

## Key Patterns

### LLM Provider Abstraction
Use Protocol-based interface for swappable LLM providers. Providers receive `base_url` at construction time from `settings.llm_gateway_base_url`:

```python
class LLMProvider(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None
    ) -> str: ...
```

Construction pattern (inject a gateway-configured client built by `build_gateway_client`):
```python
provider = OpenAICompatProvider(
    default_model=settings.default_llm_model,
    timeout_seconds=settings.llm_timeout_seconds,
    client=build_gateway_client(settings, timeout_seconds=settings.llm_timeout_seconds),
)
```

### Module Structure (backend)
Each module in `src/retriever/modules/` is self-contained:
```
module_name/
├── __init__.py
├── routes.py       # FastAPI routes
├── services.py     # Business logic
├── schemas.py      # Pydantic models (request/response)
└── repos.py        # Data access via SQLAlchemy async session
```

### Configuration
Use `pydantic-settings` for all configuration. Environment variables override defaults. Computed fields derive values from primitives (e.g., `llm_gateway_base_url` from account/gateway IDs or `LLM_GATEWAY_URL`).

## Documentation Index

Use this index to find relevant documentation without loading all files. Read only what's needed for the current task.

### Core Documentation

| Path | Purpose | Read When |
|------|---------|-----------|
| `docs/implementation-plan.md` | Overview and quick links to all docs | Starting work, need navigation |
| `docs/architecture.md` | System design, tech stack, module patterns | Understanding codebase structure |
| `docs/increments.md` | 13-increment implementation roadmap | Planning work, checking dependencies |
| `docs/development-standards.md` | Code quality, Git workflow, PR process | Writing code, creating PRs |

### Guides

| Path | Purpose | Read When |
|------|---------|-----------|
| `docs/guides/deployment.md` | Cloud Run + Cloudflare Pages deployment instructions | Deploying, configuring environments |
| `docs/guides/adding-documents.md` | Managing policy documents for RAG | Working with document ingestion |

### Architectural Decision Records (ADRs)

Read ADRs when you need to understand *why* a technical choice was made or when considering changes to that area.

**Foundation & Stack**
| ADR | Path | Topics |
|-----|------|--------|
| 001 | `docs/decisions/001-tech-stack.md` | Python, FastAPI, Pydantic, async |
| 003 | `docs/decisions/003-system-architecture.md` | Modular monolith, clean architecture, module boundaries |
| 011 | `docs/decisions/011-development-environment.md` | Dev containers, VS Code, Codespaces |

**LLM & RAG Pipeline**
| ADR | Path | Topics |
|-----|------|--------|
| 002 | `docs/decisions/002-llm-provider-strategy.md` | OpenRouter, Claude, provider abstraction, fallback |
| 004 | `docs/decisions/004-vector-database.md` | Chroma, embeddings storage, persistence |
| 005 | `docs/decisions/005-embedding-model.md` | text-embedding-3-small, OpenAI embeddings |
| 013 | `docs/decisions/013-semantic-caching.md` | Query caching, similarity matching, cost reduction |
| 016 | `docs/decisions/016-hybrid-retrieval.md` | BM25, semantic search, Cohere reranking |
| 017 | `docs/decisions/017-conversation-history-schema.md` | Messages table, no FK constraint, MVP schema |

**Safety & Security**
| ADR | Path | Topics |
|-----|------|--------|
| 007 | `docs/decisions/007-authentication-strategy.md` | JWT, session management, future SSO |
| 009 | `docs/decisions/009-content-safety.md` | Moderation API, input/output filtering |
| 012 | `docs/decisions/012-rate-limiting.md` | slowapi, per-session limits, abuse prevention |
| 014 | `docs/decisions/014-hallucination-detection.md` | Claim verification, grounding, accuracy |
| 015 | `docs/decisions/015-prompt-injection-defense.md` | Pattern detection, attack prevention |

**Infrastructure & Operations**
| ADR | Path | Topics |
|-----|------|--------|
| 006 | `docs/decisions/006-frontend-architecture.md` | Jinja2, HTMX, Tailwind, server-rendered |
| 008 | `docs/decisions/008-observability-stack.md` | ~~Superseded by 018~~ Sentry, structlog |
| 018 | `docs/decisions/018-gcp-native-observability.md` | GCP Cloud Trace, Langfuse, OTel, structlog |
| 010 | `docs/decisions/010-resilience-patterns.md` | Circuit breakers, retries, timeouts, aiobreaker |

**Reference**
| ADR | Path | Topics |
|-----|------|--------|
| 000 | `docs/decisions/000-template.md` | ADR template for new decisions |

### Quick Reference

| Topic | Primary Doc | Related ADRs |
|-------|-------------|--------------|
| RAG pipeline | `docs/architecture.md` | 002, 004, 005, 013, 014, 016, 017 |
| Security | `docs/development-standards.md` | 007, 009, 012, 015 |
| Deployment | `docs/guides/deployment.md` | 010, 018 |
| Code patterns | `docs/development-standards.md` | 001, 003 |
| Adding features | `docs/increments.md` | (varies by feature) |

### Other Resources

| What | Where |
|------|-------|
| API Docs | Auto-generated at `/docs` (OpenAPI) |
| Setup | `README.md` |
| Config | `.env.example` |
