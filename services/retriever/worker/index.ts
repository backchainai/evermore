// Cloudflare Worker router that fronts the retriever FastAPI container.
//
// This file is the ONLY place the retriever service touches a Cloudflare
// primitive (ADR 0008: application code stays portable; Cloudflare concerns
// live at the deployment boundary). Nothing under `src/` imports from here.
//
// The Worker does no application or business logic: it forwards every inbound
// request to a single container instance running the existing Docker image.

import { Container, getContainer } from "@cloudflare/containers";

export interface Env {
  // Durable Object namespace that backs the container class (see wrangler.jsonc
  // `durable_objects.bindings` + `migrations.new_sqlite_classes`).
  RETRIEVER_CONTAINER: DurableObjectNamespace<RetrieverContainer>;

  // Non-secret config, from wrangler.jsonc `vars`.
  PORT: string;

  // Secrets, injected via `wrangler secret put` (NOT committed). Optional at the
  // type level so `wrangler types` / local dev do not require them to be present.
  DATABASE_URL?: string;
  LLM_GATEWAY_TOKEN?: string;
  SUPABASE_URL?: string;
}

export class RetrieverContainer extends Container<Env> {
  // The FastAPI app listens on 8000 (Dockerfile `EXPOSE 8000`; entrypoint.sh
  // runs `uvicorn --port ${PORT:-8000}`).
  defaultPort = 8000;

  // Release container compute after a period of inactivity.
  sleepAfter = "10m";

  // Environment forwarded into the container process. The Python app reads these
  // via pydantic-settings and has no Cloudflare dependency. PORT comes from
  // `vars`; the secret bindings are populated by `wrangler secret put` and are
  // forwarded here so the container receives them at runtime.
  envVars = {
    PORT: this.env.PORT ?? "8000",
    ...(this.env.DATABASE_URL ? { DATABASE_URL: this.env.DATABASE_URL } : {}),
    ...(this.env.LLM_GATEWAY_TOKEN
      ? { LLM_GATEWAY_TOKEN: this.env.LLM_GATEWAY_TOKEN }
      : {}),
    ...(this.env.SUPABASE_URL ? { SUPABASE_URL: this.env.SUPABASE_URL } : {}),
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
