# ADR 0034: Shared LLM gateway client at `packages/llm/`

- Status: accepted
- Date: 2026-07-27
- Deciders: project owner
- Relates to: ADR 0022 (monorepo structure), ADR 0028 (llm-gateway-consolidation), ADR 0031 (shared-design-system-package)

## Context

ADR 0028 consolidated all outbound model traffic (chat, embeddings, moderation) onto one OpenAI-compatible gateway, authenticated with a single gateway token, built through one `build_gateway_client` helper. Its follow-ups said to promote that constructor into a shared package once one existed, so petdata and biowriter would import it rather than copy it. `packages/` now exists (ADR 0031 created it for the design system), so the promotion can happen.

`build_gateway_client` lived in `services/retriever/src/retriever/infrastructure/llm/gateway_client.py`, reading retriever's `Settings` object directly. Shared code cannot import a service's config: ADR 0022 puts shared code in `packages/`, imported directly by the services, and a package that imported retriever's `Settings` would recreate that coupling one layer up instead of removing it.

## Decision

`build_gateway_client` moves out of retriever into a new shared package, `packages/llm/` (distribution name `evermore-llm`, import name `evermore_llm`). The service-local `gateway_client.py` is deleted. Retriever consumes the package via `[tool.uv.sources] evermore-llm = { path = "../../packages/llm", editable = true }`, the same mechanism it already uses for `packages/auth`.

- **Settings decoupling.** Because the package cannot import a service's config, it defines a structural `typing.Protocol` named `GatewayConfig`, naming the four members the constructor reads: `llm_gateway_auth_header`, `llm_gateway_token`, the read-only property `llm_gateway_base_url`, and `gateway_token_for`. Retriever's `Settings` satisfies `GatewayConfig` structurally with no change to `Settings` itself, and mypy checks the match at each call site. `packages/auth` uses the same service-agnostic pattern, so `packages/llm` follows precedent rather than inventing a new one.
- **Scope boundary.** `packages/llm` owns shared model-call infrastructure: the gateway client constructor, the `GatewayConfig` protocol, and the `GatewayScope` Literal. Service-specific wiring, provider selection, fallback chains, retry and circuit-breaker policy, and dependency-injection wiring, stays in the service that needs it. Cross-service domain contracts go in `packages/schema`, not here. Telemetry for outbound model calls is out of scope and belongs to `packages/observability` (#114).
- **Consumers, and the deferral.** retriever is the one consumer today. petdata makes no gateway calls and carries no `openai` dependency, so adding `packages/llm` there now would add an unused dependency; petdata imports the package when it starts making gateway calls. biowriter is not yet scaffolded as a Python service, so its wiring is deferred to #64. Both services import the same shared helper when their gateway needs arrive; the scope boundary above is what stops a third copy of the constructor from appearing before then.

## Consequences

- retriever's gateway wiring now imports `evermore_llm.build_gateway_client` instead of a service-local module; the tests for the constructor moved to `packages/llm/tests/` with the code they test.
- `packages/llm` has no standalone CI job. It is verified transitively through the retriever CI job: the `packages/**` paths filter in `.github/workflows/ci.yml` already triggers that job on changes here, and retriever's test suite exercises the shared client against its own `Settings`. This is the same coverage arrangement `packages/auth` and `packages/schema` run under today.
- Adding petdata or biowriter as a second consumer becomes an editable path dependency plus satisfying `GatewayConfig`, not a copy of the constructor.
- A future contributor can tell from placement alone whether new gateway code belongs in `packages/llm` (shared across services) or in a service's own infrastructure layer (specific to one service).
