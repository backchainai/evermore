# ADR 0005: retriever migrates Langfuse v3 to v4

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner

## Context

ADR 0003 sets Langfuse v4 as the platform's LLM-observability standard and notes that the v3 to v4 step is a full SDK rewrite requiring a per-consumer migration ADR. retriever is the only current consumer: it pins `langfuse>=3.0` and instruments LLM completion, embedding, and RAG-orchestration methods with the v3 `@observe()` decorator (introduced in its ADR 018).

The Langfuse Python SDK was rewritten for v4 (released March 2026) on top of OpenTelemetry. Two facts shape the migration:

- **The decorator survives; the low-level SDK does not.** `from langfuse import observe` and `@observe()` remain in v4. The v3 low-level calls (separate `span()` / `generation()` style methods) are consolidated into a single `start_observation` / `start_as_current_observation` API with an `as_type` parameter (`span`, `generation`, `retriever`, `embedding`, and others). Any manual, non-decorator instrumentation must be rewritten; the decorator sites largely carry over.
- **v4 is OpenTelemetry-native.** It emits OTel spans and accepts a custom `tracer_provider` and `span_exporter`, with a `should_export_span` filter that by default exports only Langfuse and `gen_ai.*` spans. This is what lets Langfuse tracing stay on its own pipeline (to the Langfuse backend) rather than leaking LLM spans into the application's general telemetry backend. That separation matters because retriever's general telemetry backend is changing in parallel (ADR 0006, Datadog via the OTel Collector); the two OTel consumers must be wired so they do not cross-contaminate.

## Decision

Migrate retriever to Langfuse v4:

- **Pin `langfuse>=4.0`** and follow the official v4 migration guide.
- **Keep `@observe()`** on the LLM completion, embedding, and RAG-orchestration methods. It remains a no-op when Langfuse credentials are absent, so unconfigured environments are unaffected.
- **Rewrite any low-level v3 SDK calls** to the unified `start_observation` / `start_as_current_observation` API with the appropriate `as_type`.
- **Isolate the Langfuse OTel pipeline.** Initialize Langfuse with its own `tracer_provider` (or rely on `should_export_span`'s default Langfuse/`gen_ai.*` filter) so LLM traces flow to Langfuse and application spans flow to the Collector-fronted backend (ADR 0006). The two pipelines are complementary: Langfuse owns token/cost/LLM-pipeline views; Datadog owns request/infra APM.
- **Update configuration** for the v4 surface, including `LANGFUSE_BASE_URL` (the v3 `LANGFUSE_HOST` is deprecated) and the v4 batching/sampling environment variables.

This work is tracked by issue #57; it is sequenced alongside ADR 0006's observability cutover (#58) because both touch retriever's OTel wiring.

## Consequences

- LLM observability has a brief gap during cutover: while the SDK and any low-level call sites are rewritten and verified, traces may not land in Langfuse. The migration runs on a branch behind CI, and Langfuse's no-op-when-unconfigured behavior means a half-migrated state degrades to no LLM tracing rather than to errors.
- The self-hosted or SaaS Langfuse backend must be on a version compatible with the v4 SDK; the deployment is verified before the SDK pin lands.
- Because v4 and the application's general tracing are both OpenTelemetry now, the wiring is deliberately separated so LLM spans do not flood the Datadog backend and request spans do not flood Langfuse.
- Decorator-level instrumentation is largely preserved, so the day-to-day authoring pattern for new LLM call sites is unchanged.

## Alternatives considered

- **Stay on Langfuse v3.** Rejected: ADR 0003 makes v4 the standard and forbids grandfathering; v3 is the superseded major line.
- **Drop Langfuse and use the general telemetry backend (Datadog) for LLM observability too.** Rejected: Datadog does not provide Langfuse's LLM-specific token, cost, and pipeline-trace views. ADR 0006 keeps the two concerns separate by design.
- **Replace Langfuse with OpenLLMetry or a raw OTel gen-ai convention.** Rejected: a larger change than the standard calls for, and it abandons Langfuse's prompt-management and eval surfaces the platform expects to use.
