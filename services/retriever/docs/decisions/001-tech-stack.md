---
adr: 1
title: Tech Stack Selection
status: accepted
date: 2024-12-18
tags:
  - foundation
  - python
  - fastapi
supersedes: null
superseded_by: null
related: [3, 11]
---

# 001: Tech Stack Selection

## Status

Accepted

## Context

Need a modern, maintainable tech stack for building a RAG-based Q&A application for shelter volunteers. Key requirements:
- Async support for I/O-bound LLM/embedding operations
- Strong typing for maintainability
- Fast development velocity
- Good documentation and community support

## Decision

**Backend:**
- Python 3.13+
- FastAPI (web framework)
- Pydantic 2.x (validation and settings)
- uvicorn (ASGI server)

**Why FastAPI:**
- Native async support
- Automatic OpenAPI documentation
- Pydantic integration for validation
- Dependency injection built-in
- Excellent typing support

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Django | Heavier, less async-native, ORM overkill for this use case |
| Flask | Less structured, no built-in async, requires more boilerplate |
| Node.js/Express | Team expertise is Python, Python has better ML/AI ecosystem |
| Go | Faster but slower development, less AI/ML library support |

## Consequences

**Easier:**
- Fast development with good DX
- Strong typing catches errors early
- Auto-generated API docs
- Easy to find developers familiar with stack

**Harder:**
- Python GIL limits CPU-bound concurrency (not an issue for I/O-bound RAG)
- Deployment slightly more complex than serverless (but Railway/Render handle this)
