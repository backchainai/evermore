# ADR 0008: Host all compute on Cloudflare; keep application code portable

- Status: accepted
- Date: 2026-06-25
- Deciders: project owner
- Amends: ADR 0003 (backend hosting becomes Cloudflare Containers); ADR 0006 (telemetry becomes OTLP-only, backend deferred)

## Context

Evermore runs a SvelteKit frontend (stacker) and Python FastAPI backends (retriever, petdata, with biowriter to come) over Supabase Postgres, with outbound model calls through Cloudflare AI Gateway (ADR 0007). The frontend targets Cloudflare Pages; the backends are 12-factor containers reaching Supabase over the Postgres wire.

## Decision

Run all compute on Cloudflare. Application code stays portable: Cloudflare-specific concerns live at the deployment boundary, not in application logic.

- **Frontend: Cloudflare Pages.** stacker deploys to Pages.
- **Backends: Cloudflare Containers, Worker-fronted.** retriever, petdata, and biowriter run as container images behind a Worker router.
- **Data and auth: Supabase, fronted by Cloudflare Hyperdrive.** Supabase Postgres (pgvector), Supabase Auth, and RLS are unchanged. Connection-pool sizing is environment-driven.
- **Models: Cloudflare AI Gateway** (ADR 0007); content moderation uses gateway-native Guardrails.
- **Object storage: Cloudflare R2,** accessed through a storage interface.
- **Secrets: Wrangler secret bindings.** Services read configuration and secrets as environment values.
- **Observability: OTLP-only, backend deferred.** Detailed below.
- **CI/CD: GitHub Actions** authenticated to Cloudflare with a scoped API token. Pages and Containers deploy on merge to main with per-PR preview deploys; a gated Alembic migration runs against Supabase before a new revision takes traffic.
- **Out of scope:** a Workers rewrite of the backends, Cloudflare D1, and Vectorize.

### Portability

Application code depends on standard, portable interfaces, not on Cloudflare services. Each service is a 12-factor container. Cloudflare-specific concerns live at the deployment boundary and do not appear in application logic.

### Observability

Telemetry is two layers with a contract between them.

- **Module layer (each service).** Each service emits structured JSON logs, one object per line, INFO and DEBUG to stdout and WARNING and above to stderr, each record carrying its own severity field and the active OTel `trace_id` and `span_id`. Traces and metrics use the OpenTelemetry API only and export OTLP to an endpoint supplied by the environment. A service holds no collector, backend SDK, or routing logic.
- **Platform layer (Evermore).** The platform owns the log JSON schema, the OTel resource and semantic conventions (`service.name`, `service.version`, `deployment.environment`), the OTLP endpoint each module receives, sampling and redaction policy, the Collector, and the trace, metric, and log backends.
- **Interface contract.** The boundary is three things: structured-log JSON on stdout and stderr to the platform schema, OTLP for traces and metrics to a platform-supplied endpoint, and standard OTel resource and semantic conventions on every signal.
- **Backend deferred.** No managed trace, metric, or log backend is committed; signals export OTLP to a configurable endpoint (locally, Jaeger).
- **Where it lives.** The module side of the contract is implemented once in the shared infra package (the home of `build_gateway_client`, ADR 0007), and every service adopts it.

## Consequences

- Infrastructure added: a Worker router per backend service, Hyperdrive in front of Supabase, R2 for files, and a Cloudflare API token in CI.
- Application-code change per backend: a Dockerfile and PORT/host wiring, environment-driven pool sizing, a storage interface, and the shared telemetry configuration. No GCP or Datadog SDKs remain in application code.
- ADR 0003's backend-hosting target (Cloud Run) and ADR 0006's telemetry backend (Datadog) are superseded; the rest of ADR 0003 stands (Pages, Supabase, AI Gateway, R2, GitHub Actions, OTel-API-only instrumentation).

## Follow-ups

- Define the Evermore telemetry contract (log JSON schema, OTel resource and semantic conventions, OTLP endpoint convention) and implement the module side in the shared infra package.
- Bring retriever and petdata to the telemetry contract, including the stdout/stderr split and removal of the GCP trace exporter and GCP log-correlation field.
- Containerize the backends on Cloudflare Containers (Worker router, Wrangler config), including the petdata Dockerfile and 12-factor wiring.
- Provision Hyperdrive in front of Supabase and make pool sizing environment-driven.
- Introduce the R2 storage interface ahead of Composition export.
- Add CI/CD that deploys Pages and Containers on merge with PR previews and a gated migration step.
- Rewrite the retriever deployment guide for Cloudflare.
