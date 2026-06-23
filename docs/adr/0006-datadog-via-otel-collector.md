# ADR 0006: Telemetry backend is Datadog via the OpenTelemetry Collector

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner
- Supersedes: retriever ADR 018 (GCP Native Observability)

## Context

ADR 0003 sets the platform observability standard: OpenTelemetry API only in application code, wired through the OpenTelemetry Collector to Datadog, with structlog for JSON logs and Sentry for errors. retriever currently diverges. Its ADR 018 (GCP Native Observability, which itself superseded retriever ADR 008) chose a fully GCP-native stack: Cloud Trace via an OTel exporter, structlog to Cloud Logging, Cloud Error Reporting, and Langfuse for LLM observability. ADR 018's deciding rationale was cost: roughly $0/month on the GCP free tier versus $50 to $110+/month for Datadog + Sentry.

ADR 0003 reopened that decision deliberately ("nothing is sacred; any prior choice can be reconsidered") and resolved it the other way, for reasons that outrank per-module cost at this stage:

- **Platform consistency.** Every service reports to one backend with one set of dashboards and alert semantics. Per-module observability stacks do not compose.
- **On-distribution, contributor-familiar tooling.** Datadog + OTel Collector is widely represented and easier for contributors and LLM-assisted development than a GCP-bespoke setup.
- **Low switching cost here specifically.** retriever's application code is already OTel-API-only (ADR 018 built it that way and called the exporter "a single-file swap"). The backend change is therefore a wiring change, not an application rewrite.

## Decision

Adopt Datadog via the OpenTelemetry Collector as the telemetry backend for every service, and formally supersede retriever ADR 018:

- **Backend:** Datadog. Application code emits the OpenTelemetry API only. No `ddtrace`, no Datadog-specific SDK in application code, no direct Cloud Trace exporter.
- **Transport:** application spans go OTLP to an OpenTelemetry Collector; the Collector's Datadog exporter forwards to Datadog. The Collector is the one place that knows about Datadog.
- **retriever wiring:** the exporter-selection logic in retriever's tracing setup replaces the `CloudTraceSpanExporter` path with OTLP to the Collector. The local-dev OTLP path (Jaeger in docker-compose) is retained for offline tracing.
- **Logs:** structlog JSON to stdout stays. On Cloud Run, stdout is still captured by the platform; trace/span correlation fields remain in the log lines.
- **Errors:** add Sentry (ADR 0003). Error tracking moves off Cloud Error Reporting to Sentry.
- **LLM observability stays separate:** token, cost, and LLM-pipeline traces remain in Langfuse v4 (ADR 0005), not Datadog. The two are complementary; the Langfuse OTel pipeline is isolated from the Datadog pipeline so neither floods the other.
- **retriever ADR 018 is marked superseded** by this ADR (and its predecessor ADR 008 stays superseded).

This work is tracked by issues #58 (Datadog via OTel Collector), #59 (add Sentry), and is coordinated with #57 (Langfuse v4) because all three touch retriever's OTel wiring.

## Consequences

- **Cost rises** from roughly $0/month (GCP free tier) to Datadog's paid tier plus Sentry. This is the explicit trade ADR 0003 made: platform consistency and on-distribution tooling are worth more than per-module cost optimization at this stage. The cost was ADR 018's central reason for choosing GCP-native; that reason is acknowledged and outweighed, not overlooked.
- **A Collector deployment is now required** (sidecar or gateway alongside the services). That is new operational surface ADR 018 avoided by using managed GCP services.
- **Application-code churn is small** because the code is OTel-API-only: the change is exporter wiring, Collector deployment, and Sentry initialization, not instrumentation rewrites.
- retriever loses the zero-config Cloud Run to Cloud Logging / Error Reporting path; logs still reach stdout, and error tracking is Sentry.
- Every service shares one telemetry backend, so cross-service dashboards and alerts become possible.

## Alternatives considered

- **Keep retriever's GCP-native stack (ADR 018).** Rejected: it fragments observability per module and keeps retriever off the platform standard. Its cost advantage does not outweigh consistency and contributor familiarity at this stage.
- **Datadog via the `ddtrace` agent/SDK in application code.** Rejected: ADR 0003 requires OTel-API-only application code so the backend stays swappable. `ddtrace` would couple the code to Datadog and undo the cheap-switch property this decision relies on.
- **A vendor-neutral backend (Grafana/Tempo, or Cloud Trace via the Collector).** Rejected for now: the standard names Datadog. The Collector indirection keeps this reversible: a future ADR can repoint the Collector's exporter without touching application code.
