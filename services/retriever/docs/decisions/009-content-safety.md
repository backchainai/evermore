---
adr: 9
title: Content Safety
status: accepted
date: 2024-12-18
tags:
  - safety
  - moderation
  - security
supersedes: null
superseded_by: null
related: [14, 15]
---

# 009: Content Safety

## Status

Accepted

## Context

Volunteers may ask inappropriate questions or attempt prompt injection. Need to:
- Filter harmful content
- Prevent prompt injection attacks
- Detect hallucinated answers
- Handle off-topic questions gracefully

## Decision

**Layered safety approach:**

1. **Input filtering**: OpenAI Moderation API (free, fast)
2. **Prompt injection defense**: Pattern-based detection
3. **Hallucination detection**: Verify claims against source chunks
4. **Output filtering**: Same moderation API on responses

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| NeMo Guardrails | Complex setup, learning curve |
| Llama Guard | Requires self-hosting |
| No moderation | Unacceptable risk |
| Custom ML classifier | Development time, maintenance |

## Consequences

**Easier:**
- OpenAI Moderation is free and fast (<100ms)
- Pattern-based injection defense is simple to implement
- Clear fallback behavior for flagged content

**Harder:**
- May over-filter edge cases (false positives)
- Hallucination detection adds latency
- Patterns need updating as attacks evolve

## Implementation

### Input/Output Moderation

```python
async def is_safe(text: str) -> bool:
    response = await openai.moderations.create(input=text)
    return not response.results[0].flagged
```

### Prompt Injection Defense

```python
INJECTION_PATTERNS = [
    r"ignore (previous|above|all) (instructions|rules)",
    r"disregard (all|your) (instructions|rules|guidelines)",
    r"you are now",
    r"system prompt",
    r"reveal (your|the) (instructions|prompt|api)",
]

def is_prompt_injection(question: str) -> bool:
    question_lower = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question_lower):
            return True
    return False
```

### Hallucination Detection

See [ADR-014](014-hallucination-detection.md) for details.

## User Experience

When content is flagged:
```
"I can only answer questions about volunteer policies and procedures."
```

When hallucination detected:
```
"I don't have enough information to answer that confidently."
```
