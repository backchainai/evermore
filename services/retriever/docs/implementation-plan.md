# Retriever: Implementation Plan

AI-powered Q&A system for shelter volunteers, using RAG to answer questions from policy/procedure documents.

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design, tech stack, project structure |
| [Increments](increments.md) | Implementation roadmap (13 increments) |
| [Development Standards](development-standards.md) | Code quality, Git workflow, PR process |
| [ADRs](decisions/) | Architecture Decision Records |
| [Deployment Guide](guides/deployment.md) | How to deploy to Cloud Run + Cloudflare Pages |
| [Adding Documents](guides/adding-documents.md) | Managing policy documents |

---

## Requirements Summary

- **Users**: Volunteers (self-service)
- **Documents**: 50-500 pages, Word/Markdown/text formats (stored in Git repo)
- **Updates**: Quarterly or less frequent
- **Interface**: Web application (mobile-friendly)
- **LLM**: Anthropic Claude (via OpenRouter)
- **Auth**: Simple login (future: integrate with volunteer management system)
- **Deployment**: Cloud Run (backend) + Cloudflare Pages (frontend)

---

## Milestones

| Milestone | Increments | What You Get |
|-----------|------------|--------------|
| **Core MVP** | 1-4 | Functional Q&A from documents |
| **Quality MVP** | 1-5 | + Caching, evaluation, hybrid retrieval |
| **Full MVP** | 1-7 | + Safety, authentication |
| **Production** | 1-13 | Complete system with monitoring, feedback |

---

## Key Design Decisions

### RAG Pipeline
- **Chunking**: Structure-aware (1500 chars, 800 overlap, respects headers)
- **Retrieval**: Hybrid search (semantic + BM25) with reranking
- **Caching**: Semantic cache for similar questions (~40% cost reduction)
- **Quality**: Hallucination detection, confidence scoring, golden Q&A dataset

### Architecture
- **Style**: Modular monolith with clean architecture
- **LLM**: OpenRouter with Protocol-based abstraction for swapping
- **Vector DB**: Supabase Postgres + pgvector (HNSW cosine + GIN full-text)
- **Database**: Supabase managed Postgres (users, messages, documents)

### Safety & Resilience
- **Content moderation**: OpenAI Moderation API
- **Prompt injection**: Pattern-based detection
- **Resilience**: Timeouts + retries + circuit breakers
- **Rate limiting**: 10 req/min per session

See [ADRs](decisions/) for detailed rationale on each decision.

---

## Dependencies

```toml
[project]
dependencies = [
    # Web framework
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "python-multipart>=0.0.18",

    # LLM & Embeddings
    "openai>=1.60",

    # Database & Vector DB
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pgvector>=0.3",

    # Auth (Supabase JWKS / RS256 JWT)
    "pyjwt[crypto]>=2.10",

    # Validation & Config
    "pydantic>=2.10",
    "pydantic-settings>=2.6",

    # Observability
    "structlog>=24.4",
    "opentelemetry-api>=1.28",
    "opentelemetry-sdk>=1.28",
    "opentelemetry-instrumentation-fastapi>=0.49b0",
    "opentelemetry-exporter-gcp-trace>=1.8",
    "opentelemetry-resourcedetector-gcp>=1.8",
    "opentelemetry-exporter-otlp-proto-grpc>=1.28",
    "langfuse>=3.0",

    # Resilience
    "tenacity>=9.0",
    "aiobreaker>=1.2",
]

[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "mypy>=1.19.1",
    "pip-audit>=2.10.0",
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
    "respx>=0.22.0",
    "ruff>=0.8",
]
```

---

## Operational Concerns

### Observability
- **Distributed tracing**: GCP Cloud Trace (production) / Jaeger (local dev) via OpenTelemetry
- **Logging**: structlog (JSON, request IDs)
- **LLM observability**: Langfuse (when credentials configured)

### Cost Tracking
- Per-request cost logged in audit table
- Budget alerts at 80% threshold
- Cost dashboard in admin UI

### Health Checks
```
GET /health          → Basic liveness
GET /health/ready    → Dependencies OK
```

### Resilience
| Dependency | Timeout | Circuit Breaker |
|------------|---------|-----------------|
| OpenRouter | 30s | Open after 5 failures |
| OpenAI Embeddings | 10s | Open after 5 failures |
| Supabase Postgres | 5s | None (managed) |

---

## Future: Production Hardening (Post-Validation)

> **Philosophy:** First validate the product is useful and wanted, then harden for operations.

These items are captured from engineering review but intentionally deferred until the app has proven its value with real users.

### When to Implement

Trigger production hardening when:
- App has been used by real volunteers for 2+ weeks
- Positive feedback confirms product-market fit
- Decision made to invest in long-term operation

### Deferred Operational Items

**Data Durability**
- [ ] Verify Supabase automated backup schedule and retention
- [ ] Point-in-time recovery testing
- [ ] Backup verification tests
- [ ] Define RPO/RTO targets (suggested: RPO 24h, RTO 1h)

**Disaster Recovery**
- [ ] Document runbooks for common failure scenarios
- [ ] Secondary hosting provider config
- [ ] Incident response procedures

**Advanced Observability**
- [ ] Rich metrics dashboard (GCP Cloud Monitoring)
- [ ] User journey tracking
- [ ] Anomaly detection
- [ ] Langfuse prompt version management

**LLMOps Maturity**
- [ ] A/B testing infrastructure for models and prompts
- [ ] Model performance benchmarking
- [ ] Prompt version control
- [ ] Smart model routing (Haiku for simple, Sonnet for complex)
- [ ] Cost attribution by user/session

**Data Pipeline Hardening**
- [ ] Pipeline failure handling (partial success, corrupted docs)
- [ ] Data versioning (track embedding model version per chunk)
- [ ] Incremental indexing (only reindex changed documents)
- [ ] Large document streaming

**Security & Compliance**
- [ ] API key rotation strategy
- [ ] Data privacy procedures (GDPR/CCPA if applicable)
- [ ] Complete admin audit logging
- [ ] Data retention and anonymization policies

**Deployment Maturity**
- [ ] Blue-green or canary deployment
- [ ] Automatic rollback on high error rates
- [ ] Resource limits and scaling thresholds

### Estimated Effort

Once triggered:
- **High priority items** (backups, DR docs): 1-2 weeks
- **Full operational maturity**: 4-6 weeks additional

---

## Open Questions

1. **Existing volunteer system**: What system do volunteers currently use? (for future auth integration)
