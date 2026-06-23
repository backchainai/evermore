---
adr: 2
title: LLM Provider Strategy
status: accepted
date: 2024-12-18
tags:
  - llm
  - openrouter
  - abstraction
supersedes: null
superseded_by: null
related: [10, 13]
---

# 002: LLM Provider Strategy

## Status

Accepted

## Context

Need to integrate Claude for answer generation. Want flexibility to:
- Switch models (Sonnet, Haiku, Opus)
- Change providers if needed
- A/B test different models in future
- Handle provider outages gracefully

## Decision

Use **OpenRouter** as the primary LLM gateway with a **Protocol-based abstraction** for swappable providers.

```python
class LLMProvider(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None
    ) -> str: ...
```

**Default model:** `anthropic/claude-sonnet-4` via OpenRouter

**Fallback chain:** Sonnet → Haiku (for resilience)

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Direct Anthropic SDK | Locked to one provider, no fallback options |
| LiteLLM | Had production issues, adds complexity |
| Multiple direct integrations | More code to maintain |

## Consequences

**Easier:**
- Swap models with config change
- Fallback to cheaper/faster model on failure
- OpenRouter handles rate limiting, retries
- Access to multiple providers through one API
- OpenAI-compatible API (familiar patterns)

**Harder:**
- Extra hop through OpenRouter (minimal latency impact)
- Slight cost markup vs. direct API
- Dependency on OpenRouter availability (mitigated by fallback)

## Implementation

```python
# src/infrastructure/llm/openrouter.py
class OpenRouterProvider:
    def __init__(self, api_key: str, default_model: str = "anthropic/claude-sonnet-4"):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.default_model = default_model

    async def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
```

## Future Providers

Add when needed:
- `src/llm/anthropic.py` - Direct Anthropic SDK
- `src/llm/local.py` - Ollama/local models

Swap providers by changing `LLM_PROVIDER` env var.
