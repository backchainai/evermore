# ADR 0007: Route outbound model calls through one OpenAI-compatible LLM gateway

- Status: accepted
- Date: 2026-06-23
- Deciders: project owner

## Context

Evermore services make three kinds of outbound model calls: chat completions, embeddings, and content moderation. Addressing each provider directly spreads provider keys across the application and puts cost, caching, and rate-limit policy at each call site rather than in one place.

ADR 0003 names one LLM gateway for the stack. An OpenAI-compatible gateway exposes a single "compat" base URL that serves chat, embeddings, and moderation, addressing providers with `{provider}/{model}` model strings. It also stores provider keys (BYOK): the OpenAI and Anthropic keys live in the gateway, and the application authenticates with a single gateway token instead of carrying each provider's secret.

## Decision

All services route outbound model calls (chat, embeddings, moderation) through one OpenAI-compatible LLM gateway via a shared `build_gateway_client` helper. retriever is the first adopter; petdata and biowriter adopt the same helper when built.

- **One base URL, one client.** All chat, embedding, and moderation calls go to the gateway's OpenAI-compatible compat endpoint through a single `AsyncOpenAI` client built from settings (`build_gateway_client`). Models are addressed as `{provider}/{model}` strings (for example `anthropic/claude-sonnet-4.6`, `openai/text-embedding-3-small`, `openai/omni-moderation-latest`). Moderation no longer bypasses the gateway to call OpenAI directly.
- **Generic gateway, Cloudflare default.** The design targets any OpenAI-compatible gateway. Cloudflare AI Gateway is the default implementation: its base URL is `https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/compat`, derived from the Cloudflare account and gateway ids. Setting `llm_gateway_url` points the client at any other OpenAI-compatible gateway with config alone.
- **BYOK auth, one secret.** Provider keys (OpenAI, Anthropic) are stored in the gateway. The application sends only a single gateway token (`llm_gateway_token`) on a configurable auth header (`llm_gateway_auth_header`, default `cf-aig-authorization`). The app's LLM secret surface drops from two provider keys to one gateway token.
- **No model changes.** Chat is pinned to the confirmed live gateway slug `anthropic/claude-sonnet-4.6`, embeddings stay `openai/text-embedding-3-small` at 1536 dimensions, moderation stays `omni-moderation-latest`. This is a transport consolidation, not a model swap.
- **Gateway required, no fallback.** The gateway is the only path to a model provider. There is no direct, no-gateway route. When no gateway is configured (`llm_gateway_url` unset and the Cloudflare ids absent), `settings.llm_gateway_base_url` raises `ValueError` and the app fails fast with a clear error rather than routing anywhere implicitly. Every environment that makes model calls (local dev, CI, production) configures a gateway.

### LLM gateway vs Langfuse: who owns what

The gateway and Langfuse (ADR 0005) are complementary, split by layer:

- **LLM gateway owns the transport layer:** cost accounting, caching, rate limiting, and transport-level OpenTelemetry for outbound model calls.
- **Langfuse owns the application layer:** app-level traces, evals, and prompt management.

Neither replaces the other. The gateway sees requests and responses at the wire; Langfuse sees the RAG pipeline's semantics.

## Consequences

- The application carries one LLM secret (`llm_gateway_token`) instead of separate provider keys. Key rotation and provider onboarding move into the gateway. The `OPENROUTER_API_KEY` and `OPENAI_API_KEY` settings are retired.
- Cost, cache, and rate-limit policy live in one place (the gateway) rather than at each call site, and apply uniformly to chat, embeddings, and moderation.
- Moderation now depends on the gateway being reachable on the same path as chat and embeddings. The moderator fails open on errors and timeouts, so a gateway outage degrades to "not blocked" rather than to request failure.
- Every environment that makes model calls configures a gateway. An unconfigured environment fails fast at the call site with a clear `ValueError` rather than silently degrading, so a missing gateway is caught immediately.

## Carve-outs

- **Embedding-model swap.** Changing the embedding model is out of scope here: it would force a vector-dimension migration of stored embeddings. The 1536-dimension `openai/text-embedding-3-small` is retained.
- **All-Cloudflare hosting (#90).** Moving hosting onto Cloudflare is a separate decision tracked in #90, not part of this transport consolidation.

## Follow-ups

- Promote `build_gateway_client` into a shared Python package once one exists, so petdata and biowriter import it rather than copying it.
