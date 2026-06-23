---
adr: 14
title: Hallucination Detection
status: accepted
date: 2024-12-18
tags:
  - safety
  - rag
  - hallucination
  - quality
supersedes: null
superseded_by: null
related: [9, 16]
---

# 014: Hallucination Detection

## Status

Accepted

## Context

LLM may generate information not present in source documents. This is the #1 risk in RAG systems - volunteers could receive incorrect information about safety procedures.

## Decision

**Validate that answer claims are grounded in retrieved chunks** before returning to user.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Trust LLM output | Unacceptable risk for safety-critical info |
| Manual review all answers | Doesn't scale |
| NLI model only | More complex, higher latency |
| No detection | Volunteers could get wrong info |

## Consequences

**Easier:**
- Better accuracy for volunteers
- Catch fabricated information
- Flag low-confidence answers for review

**Harder:**
- Adds ~100ms latency
- Some false positives possible
- Requires tuning claim extraction

## Implementation

```python
class HallucinationDetector:
    async def check(self, answer: str, chunks: list[Chunk]) -> bool:
        """
        Returns True if answer is grounded, False if hallucinated.
        """
        claims = self._extract_claims(answer)

        supported_count = 0
        for claim in claims:
            if await self._is_supported(claim, chunks):
                supported_count += 1

        support_ratio = supported_count / len(claims) if claims else 1.0
        return support_ratio >= 0.8  # 80% of claims must be supported

    def _extract_claims(self, answer: str) -> list[str]:
        """Extract factual claims from answer."""
        # Split into sentences, filter declarative statements
        ...

    async def _is_supported(self, claim: str, chunks: list[Chunk]) -> bool:
        """Check if claim is entailed by any chunk."""
        # Simple string matching + optional LLM verification
        for chunk in chunks:
            if claim.lower() in chunk.text.lower():
                return True
        return False
```

## When Hallucination Detected

```python
if not await hallucination_detector.check(answer_text, chunks):
    logger.warning("Hallucination detected", answer=answer_text)
    return Answer(
        text="I don't have enough information to answer that confidently.",
        confidence="low",
        needs_human_review=True
    )
```

## Cost

- Latency: ~100ms additional
- LLM cost: ~$0.0001/query (if using LLM for verification)
- Worth it for accuracy in safety-critical domain
