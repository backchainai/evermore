---
adr: 8
title: Observability Stack
status: accepted
date: 2024-12-18
tags:
  - observability
  - sentry
  - structlog
  - logging
supersedes: null
superseded_by: 0019
related: [10]
---

# 008: Observability Stack

> Migrated from retriever/decisions/008-observability-stack.md (originally #008, 2024-12-18).

## Status

Superseded by [ADR 0019](0019-gcp-native-observability.md)

## Context

Need error tracking and logging for debugging and monitoring. Requirements:
- Simple setup for MVP
- Error alerting
- Structured logs for debugging RAG issues
- Cost-effective

## Decision

**Sentry (errors) + structlog (structured logging)**

Simplified stack that covers MVP needs without complexity of full observability platform.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| OpenTelemetry + Jaeger | Complex setup, overkill for MVP |
| DataDog | Expensive, more features than needed |
| Custom logging only | No error alerting, poor debugging |
| ELK Stack | High ops overhead |

## Consequences

**Easier:**
- Sentry: one-click setup, free tier sufficient
- structlog: structured JSON logs, easy to query
- Quick to get running

**Harder:**
- No distributed tracing (add later if needed)
- No metrics dashboards (use Sentry performance)
- Limited to Sentry's free tier initially

## Implementation

```python
# src/infrastructure/observability/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_sentry(dsn: str):
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% of requests
    )

# src/infrastructure/observability/logging.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
```

## What Gets Logged

For every RAG request:
```json
{
    "request_id": "abc123",
    "event": "rag.ask.complete",
    "question_length": 45,
    "chunks_found": 5,
    "top_chunk_score": 0.89,
    "confidence": "high",
    "latency_ms": 2300,
    "cache_hit": false
}
```

## Upgrade Path

Add OpenTelemetry when:
- Need distributed tracing across services
- Multiple developers debugging concurrently
- Complex multi-step pipelines need visualization

Advanced observability items (metrics dashboards, user-journey tracking, anomaly detection) are deferred until product validation.
