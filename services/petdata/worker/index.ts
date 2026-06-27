// Cloudflare Worker router that fronts the petdata FastAPI container.
//
// This file is the ONLY place the petdata service touches a Cloudflare
// primitive (ADR 0008: application code stays portable; Cloudflare concerns
// live at the deployment boundary). Nothing under `src/` imports from here.
//
// The Worker does no application or business logic: it forwards every inbound
// request to a single container instance running the existing Docker image.

import { Container, getContainer } from "@cloudflare/containers";

// Deployment-specific secrets and config forwarded into the container when set.
// Cloudflare cannot wildcard-forward bindings, so each key is named explicitly;
// the forwarding mechanism itself is expressed once (see `envVars` below). This
// is a deliberate subset of the PETDATA_ settings: the tunables that carry safe
// code defaults (pool sizing, retries, CORS) are intentionally not forwarded.
// All use the PETDATA_ prefix the Python app reads via pydantic-settings.
const FORWARDED_ENV_KEYS = [
  "PETDATA_DATABASE_URL",
  "PETDATA_DATABASE_REQUIRE_SSL",
  "PETDATA_COOKIES",
  "PETDATA_SMS_BASE_URL",
  "PETDATA_SMS_TABLE_ANIMALS",
  "PETDATA_SMS_TABLE_VOLUNTEER_NOTES",
  "PETDATA_SMS_TABLE_WALK_RECORDS",
] as const;

export type Env = {
  // Durable Object namespace that backs the container class (see wrangler.jsonc
  // `durable_objects.bindings` + `migrations.new_sqlite_classes`).
  PETDATA_CONTAINER: DurableObjectNamespace<PetdataContainer>;

  // Non-secret config, from wrangler.jsonc `vars`.
  PORT: string;
} & {
  // Each forwarded binding, injected via `wrangler secret put` (NOT committed).
  // Optional at the type level so `wrangler types` / local dev do not require
  // them to be present. Derived from the one key list so the type and the
  // forwarding logic cannot drift.
  [K in (typeof FORWARDED_ENV_KEYS)[number]]?: string;
};

export class PetdataContainer extends Container<Env> {
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
    const container = getContainer(env.PETDATA_CONTAINER, "petdata");
    return container.fetch(request);
  },
} satisfies ExportedHandler<Env>;
