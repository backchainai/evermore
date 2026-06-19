---
adr: 16
title: Hybrid Retrieval with Reranking
status: accepted
date: 2024-12-18
tags:
  - rag
  - retrieval
  - reranking
  - bm25
supersedes: null
superseded_by: null
related: [4, 5, 13]
---

# 016: Hybrid Retrieval with Reranking

## Status

Accepted

## Context

Pure semantic search has limitations:
- Misses exact keyword matches ("check-in" vs "sign in")
- May rank less relevant chunks higher
- Doesn't leverage keyword signal

## Decision

**Combine semantic + keyword search (BM25), then rerank results.**

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Semantic only | Misses keyword matches |
| Keyword only | Poor semantic understanding |
| No reranking | Lower retrieval quality |

## Consequences

**Easier:**
- Better retrieval accuracy (10-15% improvement)
- Catches both semantic and keyword matches
- More robust to query variations

**Harder:**
- Slightly more complex retrieval logic
- Small additional cost for reranking (~$0.001/query)
- Need to tune merge strategy

## Implementation

```python
async def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
    # 1. Semantic search (over-retrieve)
    semantic_chunks = await self.vector_store.similarity_search(
        query, k=top_k * 2
    )

    # 2. Keyword search (BM25)
    keyword_chunks = await self.keyword_search(query, k=top_k)

    # 3. Merge and deduplicate
    merged = self._merge_results(semantic_chunks, keyword_chunks)

    # 4. Rerank (Cohere API or RRF)
    reranked = await self._rerank(query, merged, top_k)

    return reranked[:top_k]
```

## Reranking Options

### Option A: Cohere Rerank API
- Cost: ~$0.001 per query
- Quality: High
- Latency: ~100ms

```python
reranked = await cohere.rerank(
    query=query,
    documents=[c.text for c in chunks],
    top_n=top_k
)
```

### Option B: Reciprocal Rank Fusion (Free)
- Cost: Free (compute only)
- Quality: Good
- Latency: <10ms

```python
def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    scores = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] += 1 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
```

## Dependencies

```toml
"cohere>=5.0.0",      # Reranking API
"rank-bm25>=0.2.2",   # BM25 keyword search
```

## Metrics

Track:
- Retrieval accuracy (correct doc in top-3)
- Score distribution (are chunks relevant?)
- Query types that benefit most from hybrid
