---
adr: 18
title: GCP Native Observability
status: accepted
date: 2026-03-13
tags:
  - observability
  - gcp
  - langfuse
  - opentelemetry
supersedes: 8
superseded_by: null
related: [8, 10]
---

# 018: GCP Native Observability

## Status

Accepted — supersedes [ADR-008](008-observability-stack.md).

## Context

ADR-008 prescribed Sentry (error tracking) + structlog (logging) as the MVP observability stack, with OpenTelemetry as a future upgrade path. The tech stack standard recommends Datadog + Sentry.

As the backend migrates to Cloud Run (GCP), a fully GCP-native stack provides equivalent capabilities at zero cost by leveraging services included in the free tier. The project also needs LLM-specific observability (token tracking, cost calculation, pipeline traces) which neither Sentry nor Datadog provide natively.

## Decision

Replace the Sentry + Datadog approach with GCP native services + Langfuse:

| Concern | Tool | Cost |
|---------|------|------|
| Distributed tracing | GCP Cloud Trace via OTel exporter | $0 (free tier) |
| Logging | structlog JSON → stdout → Cloud Logging (automatic on Cloud Run) | $0 (free tier) |
| Error tracking | Cloud Error Reporting (automatic from structured error logs) | $0 (free tier) |
| LLM observability | Langfuse `@observe()` | $0 (self-host) or low SaaS |
| Local dev tracing | Jaeger via OTLP in docker-compose | $0 |

**Total production cost: $0/month** vs $50-110+/month for Datadog + Sentry.

## Implementation

### Exporter Selection Logic

```
gcp_project_id set?  → GCP Cloud Trace exporter
OTEL_EXPORTER_OTLP_ENDPOINT set?  → OTLP/gRPC exporter (Jaeger)
debug mode?  → Console exporter
otherwise  → No-op (spans still created for context propagation)
```

### Log-Trace Correlation

structlog processors inject `trace_id`, `span_id`, and `logging.googleapis.com/trace` into every log event. Cloud Logging automatically correlates logs with Cloud Trace spans via this field.

### Langfuse

`@observe()` decorators on LLM completion, embedding, and RAG orchestration methods. Acts as a no-op when Langfuse credentials are not configured.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Datadog + Sentry (tech stack standard) | $50-110+/mo, overkill for current scale |
| Sentry only (ADR-008) | No distributed tracing, no LLM observability |
| Grafana Cloud | Free tier generous, but adds vendor outside GCP |
| OpenLLMetry | Less mature than Langfuse for LLM-specific traces |

## Trade-offs

**Advantages:**
- Zero cost at current scale
- Vendor consolidation (already deploying to Cloud Run)
- Automatic Cloud Run integration (no agent to install)
- OTel-based — exporter is swappable if needs change
- Langfuse provides LLM-specific views Sentry/Datadog lack

**Disadvantages:**
- No Sentry-style alerting rules (use Cloud Monitoring alerts instead)
- No Datadog dashboards (use Cloud Trace UI + Cloud Monitoring)
- GCP Cloud Trace UI is less polished than Datadog APM
- Langfuse is a younger project (mitigated: `@observe()` is a thin decorator)

## Upgrade Path

If observability needs outgrow GCP free tier:
1. OTel exporter is a single-file swap — replace `CloudTraceSpanExporter` with any OTel-compatible backend
2. Langfuse `@observe()` can coexist with OTel spans (complementary, not competing)
3. Cloud Monitoring alerts can be replaced with PagerDuty/OpsGenie integration

## Consequences

- `infrastructure/observability/tracing.py` becomes the single source of truth for exporter selection
- All log lines include `trace_id`/`span_id` when a span is active
- Every request gets a `request_id` via middleware
- LLM calls are visible in Langfuse with token/cost tracking
- Local development uses Jaeger for trace visualization
