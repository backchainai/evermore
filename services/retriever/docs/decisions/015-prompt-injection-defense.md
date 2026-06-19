---
adr: 15
title: Prompt Injection Defense
status: accepted
date: 2024-12-18
tags:
  - security
  - prompt-injection
  - safety
supersedes: null
superseded_by: null
related: [9]
---

# 015: Prompt Injection Defense

## Status

Accepted

## Context

Public-facing LLM systems are targets for prompt injection attacks. Users may attempt:
- "Ignore previous instructions..."
- "You are now a different assistant..."
- "Reveal your system prompt..."

## Decision

**Pattern-based detection** for common prompt injection attempts.

Simple regex patterns that catch known attack vectors.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| No defense | Vulnerable to attacks |
| Complex NLP detection | Overkill for MVP |
| LLM-based detection | Adds latency and cost |
| Prompt hardening only | Insufficient alone |

## Consequences

**Easier:**
- Simple to implement (~20 lines)
- No additional API calls
- Fast (regex matching)

**Harder:**
- Patterns need updating as attacks evolve
- May have false positives
- Sophisticated attacks may bypass

## Implementation

```python
import re

INJECTION_PATTERNS = [
    r"ignore (previous|above|all) (instructions|rules)",
    r"disregard (all|your) (instructions|rules|guidelines)",
    r"new (instructions|task|role)",
    r"you are now",
    r"system prompt",
    r"reveal (your|the) (instructions|prompt|api)",
    r"act as",
    r"pretend (to be|you are)",
]

def is_prompt_injection(question: str) -> bool:
    """Detect common prompt injection patterns."""
    question_lower = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question_lower):
            return True
    return False
```

## Response to Injection Attempts

```python
if is_prompt_injection(question):
    logger.warning("Prompt injection attempt", question=question[:100])
    return Answer(
        text="I can only answer questions about volunteer policies and procedures.",
        flagged=True
    )
```

## Layered Defense

This is one layer of defense. Also use:
1. Strong system prompt with clear boundaries
2. Input validation (length limits, character filtering)
3. Output filtering (OpenAI Moderation API)
4. Hallucination detection

## Updating Patterns

Review and update patterns quarterly or when new attack vectors are discovered. Track flagged questions in logs to identify new patterns.
