---
adr: 13
title: Semantic Caching
status: accepted
date: 2024-12-18
tags:
  - caching
  - performance
  - rag
supersedes: null
superseded_by: null
related: [2, 5, 16]
---

# 013: Semantic Caching

## Status

Accepted

## Context

Volunteers ask similar questions repeatedly. Without caching:
- Unnecessary LLM costs
- 3-second responses instead of 50ms
- Higher load on OpenRouter

## Decision

**Cache RAG answers using semantic similarity matching.**

If a semantically similar question was asked recently, return the cached answer.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Exact-match cache | Misses similar questions ("where do I sign in" vs "sign in location") |
| No cache | Expensive, slow |
| LLM-level caching | Less control, doesn't help with retrieval costs |

## Consequences

**Easier:**
- ~40% cache hit rate for common questions
- 60x faster responses for cached queries (3s → 50ms)
- ~40% reduction in LLM costs

**Harder:**
- Need cache invalidation strategy
- Additional storage for cache
- Threshold tuning for similarity

## Implementation

```python
class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.95):
        self.threshold = similarity_threshold

    async def get(self, question: str) -> Answer | None:
        """Return cached answer if similar question was asked."""
        question_embedding = await embed(question)
        results = self.cache_collection.query(
            query_embeddings=[question_embedding],
            n_results=1
        )

        if results and results['distances'][0][0] < (1 - self.threshold):
            return Answer.parse_raw(results['documents'][0][0])
        return None

    async def set(self, question: str, answer: Answer) -> None:
        """Store answer in cache (only for high-confidence answers)."""
        if answer.confidence != "high":
            return
        question_embedding = await embed(question)
        self.cache_collection.add(
            embeddings=[question_embedding],
            documents=[answer.json()],
            metadatas=[{"question": question, "timestamp": datetime.utcnow().isoformat()}]
        )
```

## Cache Invalidation

Clear cache when:
- Documents are reindexed
- Manually via admin endpoint
- TTL expires (default: 24 hours)

## Metrics

Track:
- Cache hit rate
- Questions served from cache
- Cost savings from caching
