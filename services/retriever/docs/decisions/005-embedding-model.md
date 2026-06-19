---
adr: 5
title: Embedding Model
status: accepted
date: 2024-12-18
tags:
  - rag
  - embeddings
  - openai
supersedes: null
superseded_by: null
related: [4, 13, 16]
---

# 005: Embedding Model

## Status

Accepted

## Context

Need embeddings for semantic search over shelter policy documents. Requirements:
- Good quality for Q&A retrieval
- Cost-effective for 500-5000 chunks
- Fast enough for real-time queries
- Easy to integrate

## Decision

**OpenAI `text-embedding-3-small`**

- 1536 dimensions
- ~$0.02 per 1M tokens
- Good balance of quality and cost

## Alternatives Considered

| Alternative | Cost | Quality | Reason Not Chosen |
|-------------|------|---------|-------------------|
| text-embedding-3-large | 2x | Higher | Overkill for document count |
| Open-source (all-MiniLM) | Free | Lower | Quality tradeoff, self-hosting |
| Cohere embeddings | Similar | Similar | Another vendor dependency |
| Voyage AI | Higher | Higher | Cost for MVP |

## Consequences

**Easier:**
- Same API as LLM calls (OpenAI-compatible)
- Well-documented, stable API
- Good default quality

**Harder:**
- Vendor lock-in for embeddings
- Re-embedding required if switching models
- Network dependency for embedding generation

## Cost Estimate

For 500 pages of documents:
- ~250,000 tokens for initial indexing
- Cost: ~$0.005 (negligible)
- Re-indexing quarterly: ~$0.02/year

Query embeddings are similarly cheap (~$0.00002 per query).

## Future Considerations

- **Dimensionality reduction**: `text-embedding-3-small` supports 512/768 dimensions for faster search
- **Fine-tuning**: If retrieval quality is poor, consider fine-tuning open-source embeddings on domain data
- **Caching**: Query embeddings could be cached if same questions are asked frequently
