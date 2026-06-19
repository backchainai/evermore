---
adr: 3
title: System Architecture
status: accepted
date: 2024-12-18
tags:
  - architecture
  - modular-monolith
  - clean-architecture
supersedes: null
superseded_by: null
related: [1]
---

# 003: System Architecture

## Status

Accepted

## Context

Need to choose an architecture that:
- Supports a small team (1-2 developers)
- Enables future extraction of services if needed
- Keeps operational complexity low
- Allows API-first design for future integrations

## Decision

**Modular Monolith** with clean architecture principles.

Single deployable unit with well-defined module boundaries:
- `modules/auth/` - Authentication
- `modules/rag/` - RAG/Q&A pipeline
- `modules/documents/` - Document management
- `infrastructure/` - Shared technical concerns

**Key principles:**
- Dependencies point inward (business logic isolated from framework)
- Each module is self-contained with routes, services, schemas
- Shared infrastructure is injected, not imported directly
- API-first: frontend is just another API consumer

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Microservices | Overkill for team size, high ops overhead |
| Flat monolith | Hard to maintain as codebase grows |
| Serverless functions | Cold starts hurt UX, complex local dev |

## Consequences

**Easier:**
- Single deployment (Railway/Render)
- Simple local development
- Easy to understand code organization
- Clear extraction path if services needed later

**Harder:**
- Must enforce module boundaries through discipline
- Shared database (SQLite) limits some isolation
- All modules scale together (fine for this use case)

## Module Structure

Each module follows this pattern:

```
module_name/
├── __init__.py
├── routes.py       # FastAPI routes (thin layer)
├── services.py     # Business logic (testable)
├── schemas.py      # Pydantic models (API contracts)
├── models.py       # Domain models (if needed)
└── repos.py        # Data access (if needed)
```

## Extraction Path

If a module needs to become a service:
1. Module already has clear boundaries
2. Extract to separate FastAPI app
3. Replace imports with HTTP/gRPC calls
4. Deploy independently

This path exists but is not needed for foreseeable scale.
