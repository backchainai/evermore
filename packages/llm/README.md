# evermore-llm

Shared model-call transport infrastructure for the Evermore services: one
`build_gateway_client` helper that builds a single `AsyncOpenAI` client
pointed at the OpenAI-compatible LLM gateway (chat, embeddings, and
moderation all go through it). This executes the follow-up documented in
[`docs/adr/0028-llm-gateway-consolidation.md`](../../docs/adr/0028-llm-gateway-consolidation.md):
"Promote `build_gateway_client` into a shared Python package once one exists,
so petdata and biowriter import it rather than copying it." retriever imports
it from here today; petdata and biowriter will import it from the same
package once they start making gateway calls, rather than copying it.

## Scope boundary

This package holds shared transport plumbing only:

- `evermore_llm.gateway_client` provides `build_gateway_client`, the
  `GatewaySettings` structural `Protocol` it reads, and the `GatewayScope`
  traffic-class literal ("chat", "embeddings", "moderation").

It does **not** hold service-specific wiring (which model to call, how a
service's settings resolve their own fields) or domain contracts (those
belong in [`packages/schema`](../schema/README.md)). Each service keeps its
own `Settings` class; it only needs to expose the four members
`GatewaySettings` names to be accepted by `build_gateway_client`.

## Usage

```python
from evermore_llm import build_gateway_client

client = build_gateway_client(settings, scope="chat")
```

`settings` is any object exposing `llm_gateway_token`, `llm_gateway_auth_header`,
a `llm_gateway_base_url` property, and a `gateway_token_for(scope)` method
(structural typing via `GatewaySettings`; no inheritance required).

## Deviations from repo defaults

Pinned to Python 3.13+, not the repo's 3.14 floor: it matches its current
consumer, `services/retriever`, the same rationale
[`packages/auth`](../auth/README.md) documents.
