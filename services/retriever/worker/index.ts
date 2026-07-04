// Cloudflare Worker router that fronts the retriever FastAPI container.
//
// This file is the ONLY place the retriever service touches a Cloudflare
// primitive (ADR 0029 (all-cloudflare-hosting): application code stays portable; Cloudflare concerns
// live at the deployment boundary). Nothing under `src/` imports from here.
//
// The Worker does no application or business logic: it forwards every inbound
// request to a single container instance running the existing Docker image.

import { Container, getContainer } from "@cloudflare/containers";

// Deployment-specific config forwarded into the container when set. Cloudflare
// cannot wildcard-forward bindings, so each key is named explicitly; the
// forwarding mechanism itself is expressed once (see `envVars` below). The
// container's Python app fails fast unless an LLM gateway is resolvable
// (`config.py` raises when neither LLM_GATEWAY_URL nor CLOUDFLARE_ACCOUNT_ID +
// CLOUDFLARE_GATEWAY_ID is set), so the gateway keys below are required for the
// container to boot, not merely optional. The production CORS origin is
// forwarded too, but as a non-secret `vars` value (ALLOWED_ORIGINS, below).
// Names match the env vars the Python app reads via pydantic-settings
// (case-insensitive, no prefix).
const FORWARDED_ENV_KEYS = [
  "DATABASE_URL",
  "LLM_GATEWAY_URL",
  "LLM_GATEWAY_TOKEN",
  "LLM_GATEWAY_AUTH_HEADER",
  "CLOUDFLARE_ACCOUNT_ID",
  "CLOUDFLARE_GATEWAY_ID",
  "SUPABASE_URL",
  "SUPABASE_PUBLISHABLE_KEY",
  "SUPABASE_SECRET_KEY",
] as const;

export type Env = {
  // Durable Object namespace that backs the container class (see wrangler.jsonc
  // `durable_objects.bindings` + `migrations.new_sqlite_classes`).
  RETRIEVER_CONTAINER: DurableObjectNamespace<RetrieverContainer>;

  // Non-secret config, from wrangler.jsonc `vars`.
  PORT: string;
  // Production CORS allow-list, from `vars`. Comma-separated string, parsed into
  // a list by config.py (`allowed_origins` -> `allowed_origins_list`). Optional
  // at the type level so local dev (no `vars` override) falls back to config.py's
  // default origins.
  ALLOWED_ORIGINS?: string;
} & {
  // Each forwarded binding, injected via `wrangler secret put` (NOT committed).
  // Optional at the type level so `wrangler types` / local dev do not require
  // them to be present. Derived from the one key list so the type and the
  // forwarding logic cannot drift.
  [K in (typeof FORWARDED_ENV_KEYS)[number]]?: string;
};

export class RetrieverContainer extends Container<Env> {
  // The FastAPI app listens on 8000 (Dockerfile `EXPOSE 8000`; entrypoint.sh
  // runs `uvicorn --port ${PORT:-8000}`).
  defaultPort = 8000;

  // Release container compute after a period of inactivity.
  sleepAfter = "10m";

  // Environment forwarded into the container process. The Python app reads these
  // via pydantic-settings and has no Cloudflare dependency. PORT comes from
  // `vars`; the bindings in FORWARDED_ENV_KEYS are populated by `wrangler secret
  // put` and forwarded here (only when set) so the container receives them at
  // runtime.
  envVars = {
    PORT: this.env.PORT ?? "8000",
    ...(this.env.ALLOWED_ORIGINS
      ? { ALLOWED_ORIGINS: this.env.ALLOWED_ORIGINS }
      : {}),
    ...Object.fromEntries(
      FORWARDED_ENV_KEYS.flatMap((key) => {
        const value = this.env[key];
        return value ? [[key, value] as const] : [];
      }),
    ),
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Pure routing: forward to a single named container instance. Use a stable
    // instance name so requests share one warm container (MVP scope).
    const container = getContainer(env.RETRIEVER_CONTAINER, "retriever");
    return container.fetch(request);
  },
} satisfies ExportedHandler<Env>;
