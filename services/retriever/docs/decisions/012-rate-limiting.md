---
adr: 12
title: Rate Limiting
status: accepted
date: 2024-12-18
tags:
  - api
  - rate-limiting
  - security
supersedes: null
superseded_by: null
related: [7]
---

# 012: Rate Limiting

## Status

Accepted

## Context

Need to prevent abuse and control costs. Without rate limiting:
- Single user could run up LLM costs
- DoS attacks possible
- No fair usage enforcement

## Decision

**slowapi** for per-session rate limiting.

Default: 10 requests per minute per session.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| No limits | Cost and abuse risk |
| Custom implementation | Reinventing the wheel |
| Redis-based limiting | Adds external dependency |
| API gateway limiting | No gateway in architecture |

## Consequences

**Easier:**
- Simple to configure
- Works with FastAPI out of the box
- Minimal overhead

**Harder:**
- In-memory storage (resets on restart)
- Per-instance limits (fine for single instance)

## Implementation

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/v1/rag/ask")
@limiter.limit("10/minute")
async def ask(request: Request, question: str):
    ...
```

## Rate Limit Response

When limit exceeded:
```json
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests. Please wait a moment before asking another question.",
    "retry_after": 30
}
```

## Future Enhancements

If needed:
- Per-user limits (after auth implemented)
- Different limits for admin endpoints
- Redis backend for distributed limiting
