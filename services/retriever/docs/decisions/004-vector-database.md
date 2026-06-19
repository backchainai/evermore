---
adr: 4
title: Vector Database
status: superseded
date: 2024-12-18
tags:
  - rag
  - vector-db
  - chroma
supersedes: null
superseded_by: "pgvector migration (stack migration Phase 3)"
related: [5, 16]
---

# 004: Vector Database

> **Superseded:** Vector DB migrated from Chroma to Supabase Postgres + pgvector. See `backend/src/retriever/infrastructure/vectordb/`.

## Status

Superseded

## Context

Need vector storage for document embeddings. Requirements:
- 50-500 pages of documents (~500-5000 chunks)
- Quarterly updates (not real-time)
- Simple operations preferred
- Low cost for MVP

## Decision

**Chroma** in embedded/persistent mode.

- Runs in-process with FastAPI
- Persists to local disk (`data/chroma/`)
- No separate service to manage

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Pinecone | Managed cost, overkill for scale |
| pgvector | Requires PostgreSQL, more ops |
| Qdrant | More features than needed, separate service |
| Weaviate | Complex for MVP |
| FAISS | No persistence built-in |

## Consequences

**Easier:**
- Zero external services
- Simple backup (copy data directory)
- Fast local development
- No network latency for queries

**Harder:**
- Limited to single instance (no horizontal scaling)
- Must migrate if >100k chunks or high concurrency needed
- Embedded mode has some locking considerations

## Migration Path

If scale requires:
```
Phase 1 (MVP): Chroma embedded
    ↓ (10k+ queries/day or 100k chunks)
Phase 2: Chroma server mode (separate process)
    ↓ (1M chunks or multi-tenancy)
Phase 3: Migrate to Qdrant/Weaviate/pgvector
```

## Configuration

```python
# src/infrastructure/vectordb/chroma.py
import chromadb
from chromadb.config import Settings

def create_chroma_client():
    return chromadb.PersistentClient(
        path="./data/chroma",
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=False,
        )
    )
```

## Backup Strategy

Back up `data/chroma/` directory:
- After every document reindex
- Daily incremental backup to cloud storage
- See [Future: Production Hardening](../implementation-plan.md#future-production-hardening-post-validation)
