# Auth Flow

End-to-end authentication path for Evermore: how a browser session becomes a validated request to a module backend.

## Identity provider

Supabase Auth is the single identity provider. All modules trust a single Supabase project's JWT signing keys.

- **Token format:** RS256 JWT
- **JWKS endpoint:** `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`
- **Audience claim:** `authenticated`
- **Role claim:** `role` (values: `authenticated`, plus custom roles like `admin` set via Supabase user metadata)

## Sequence

```
Browser              stacker (SvelteKit SSR)         module backend          Supabase
   │                       │                              │                     │
   │ ─ POST /login ─────────▶                              │                     │
   │                       │ ─ signInWithPassword ───────────────────────────────▶
   │                       │ ◀─ session (access_token, refresh_token) ──────────│
   │ ◀─ Set-Cookie: sb-* ─│                              │                     │
   │                       │                              │                     │
   │ ─ GET /app/retriever ─▶                              │                     │
   │                       │ hooks.server.ts:               │                     │
   │                       │   safeGetSession() → user, jwt │                     │
   │                       │ +layout.server.ts:             │                     │
   │                       │   load subscriptions for user  │                     │
   │ ◀─ HTML + sub state ─│                              │                     │
   │                       │                              │                     │
   │ ─ POST /api/ask ──────▶ (SvelteKit endpoint or       │                     │
   │                         direct from browser)         │                     │
   │                       │ BaseApiClient:                │                     │
   │                       │   Authorization: Bearer <jwt> ─▶                     │
   │                       │                              │ JWKS validate ──────▶│
   │                       │                              │ ◀─ public keys ─────│
   │                       │                              │ verify sig+exp+aud  │
   │                       │                              │ check subscription   │
   │                       │                              ◀─ 200 / 401 / 403 ──│
   │ ◀─ response ─────────│                              │                     │
```

## Stacker side

- `hooks.server.ts` — calls `getUser()` (server-verified) on every request, attaches `safeGetSession` helper to `event.locals`.
- `src/routes/app/+layout.server.ts` — gates all `/app/*` routes; redirects to `/login` if no session; loads subscription list.
- `src/lib/api/base-client.ts` (`BaseApiClient`) — abstracts JWT-bearing HTTP calls; every module's API client extends this.
- `src/lib/server/supabase.ts` — server-side Supabase client factory.

## Module backend side

Reference implementation: `retriever/backend/src/retriever/modules/auth/`.

Components every backend implements:

1. **JWKS validator** (`auth/jwks.py`)
   - Fetches public keys from Supabase JWKS URL on startup; caches with TTL refresh.
   - Validates RS256 signature, expiration, audience (`authenticated`).
2. **Auth dependencies** (`auth/dependencies.py`)
   - `require_auth` — extracts `Authorization: Bearer`, validates, returns user claims.
   - `require_admin` — composes `require_auth` and checks `role == 'admin'`.
3. **Subscription dependency** (`auth/subscription.py` — see `subscriptions.md`)
   - Checks the user has an active subscription for this module.
4. **Wiring** (`main.py` or per-route)
   - Auth and subscription deps applied to all `/api/v1/*` routes.
   - `/health`, `/openapi.json`, `/llms.txt`, `/manifest` remain public.

## Error semantics

| Status | Meaning | Example |
|---|---|---|
| 401 | Authentication failure | Missing/expired/invalid JWT |
| 403 (`role_required`) | Authenticated but lacks role | Non-admin hits admin route |
| 403 (`subscription_required`) | Authenticated but no entitlement | User without retriever sub hits `/api/v1/ask` |

Response body shape:

```json
{ "error": "subscription_required", "module": "retriever" }
```

## Common failure modes

- **Bad signature:** stale JWKS cache. Refresh on validation failure once before rejecting.
- **Expired token:** browser should refresh via Supabase client; if backend sees expired, return 401 with `{error: "token_expired"}` so client can retry post-refresh.
- **Audience mismatch:** misconfigured Supabase project — verify JWKS URL matches the project that issued the token.
- **Cookie not present:** SSR not initialized — verify `hooks.server.ts` runs.

## Open security questions

- Auth cookie HttpOnly status: tracked in `prof-0e1.13`.
