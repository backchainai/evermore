# evermore-llm

Shared OpenAI-compatible LLM gateway client builder for the Evermore
services. One canonical copy of the gateway-transport plumbing, consumed by
every service that makes outbound model calls (chat, embeddings, moderation):

- `evermore_llm.build_gateway_client` constructs an `AsyncOpenAI` client
  pointed at the gateway's OpenAI-compatible endpoint, given a config object
  and an optional traffic-class scope.
- `evermore_llm.GatewayConfig` is the structural `typing.Protocol` naming the
  four members the builder reads (`llm_gateway_auth_header`,
  `llm_gateway_token`, `llm_gateway_base_url`, `gateway_token_for`). A
  service's own settings class satisfies it structurally, with no import of
  this package's types required at the settings definition site.
- `evermore_llm.GatewayScope` is the `Literal["chat", "embeddings",
  "moderation"]` traffic-class type shared by the config protocol and every
  consumer.

The gateway-consolidation decision and the reasoning behind the
`GatewayConfig` seam are owned by
[`docs/adr/0028-llm-gateway-consolidation.md`](../../docs/adr/0028-llm-gateway-consolidation.md)
and
[`docs/adr/0034-packages-llm-gateway-client.md`](../../docs/adr/0034-packages-llm-gateway-client.md);
this README covers only the package's own API surface. Shared model-call
infrastructure lives here; service-specific wiring (which settings class,
which FastAPI dependency graph builds the client) and domain contracts
(`Package`, `Composition`, and the rest of the data spine) do not, those
belong to `packages/schema`.

## Usage

```python
from evermore_llm import build_gateway_client

client = build_gateway_client(settings, scope="chat")
```

`settings` is any object that structurally satisfies `GatewayConfig`; a
service's existing settings class needs no changes to qualify.

## Deviations from repo defaults

Pinned to Python 3.13+, not the repo's 3.14 floor: it matches its current
consumer, `services/retriever`. ADR
[`0024-standardized-tech-stack.md`](../../docs/adr/0024-standardized-tech-stack.md)
already tracks retriever's move to 3.14 as outstanding work, not
grandfathered.

## Security contract

`gateway_token_for` is part of this package's security contract, not just its type
signature. An implementation must return the token scoped to the requested traffic class
and fall back to the shared token only when the scoped one is unset. Returning the shared
token for every scope type-checks against `GatewayConfig` but defeats the blast-radius
narrowing that scoped tokens exist to provide (see issue #228).

`build_gateway_client` sends no gateway auth header at all when the resolved token is
empty, and passes the placeholder `api_key="unused"`. A consumer that leaves its token
unset therefore gets a client that looks working but authenticates nothing. Set the
gateway token in every environment that reaches a real gateway.
