---
adr: 10
title: Resilience Patterns
status: accepted
date: 2024-12-18
tags:
  - resilience
  - circuit-breaker
  - retry
  - fault-tolerance
supersedes: null
superseded_by: null
related: [2, 8]
---

# 010: Resilience Patterns

## Status

Accepted

## Context

External API dependencies (OpenRouter, OpenAI) can fail. Need to:
- Handle timeouts gracefully
- Retry transient failures
- Prevent cascading failures
- Provide fallback behavior

## Decision

**Timeouts + tenacity (retries) + aiobreaker (circuit breaker)** for all external API calls.

Circuit breakers are included from the start because cascading failures are unacceptable for user experience.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| No resilience | Fragile, poor UX on failures |
| Defer circuit breakers | Cascading failures hurt UX too much |
| Complex resilience (Istio) | Overkill for monolith |

## Consequences

**Easier:**
- Fail-fast behavior prevents thread pool exhaustion
- Automatic recovery when service returns
- Clear error messages for users

**Harder:**
- Slightly more complex code
- Need to tune thresholds based on real traffic

## Configuration

| Dependency | Timeout | Retry Strategy | Circuit Breaker |
|------------|---------|----------------|-----------------|
| OpenRouter API | 30s | 2 retries, exponential backoff | Open after 5 failures, 60s reset |
| OpenAI Embeddings | 10s | 2 retries, exponential backoff | Open after 5 failures, 60s reset |
| Chroma | 5s | 1 retry (local, should be fast) | None (local) |

## Implementation

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from aiobreaker import CircuitBreaker
import httpx

# Circuit breaker for LLM calls
llm_breaker = CircuitBreaker(
    fail_max=5,           # Open after 5 consecutive failures
    timeout_duration=60,  # Stay open for 60 seconds
)

@llm_breaker
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
async def call_openrouter(messages: list) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        ...
```

## Fallback Behavior

1. **On timeout/error**: Return friendly "Service temporarily unavailable, please try again"
2. **On circuit open**: Fail immediately (don't wait for timeout)
3. **Model fallback**: Sonnet → Haiku chain (see [ADR-002](002-llm-provider-strategy.md))
4. **Ultimate fallback**: Return retrieved chunks without LLM generation

```python
except LLMProviderError:
    return Answer(
        text="I found these relevant sections:\n\n" +
             "\n\n".join(c.text for c in chunks),
        confidence="low",
        is_fallback=True
    )
```
