# Stacker + Packages Security Audit (issue #227)

Trust-boundary review for issue #227, epic #222. Scope: the `apps/stacker` SvelteKit portal (108 tracked files) and the shared `packages/` tree (42 tracked files), 150 files total. The per-file coverage ledger is in `docs/security/coverage-ledger.md` under "Slice: stacker + packages (issue #227)". This document records the browser-facing trust-boundary analysis and the findings referenced by the ledger's `FINDING-Sxx` verdicts.

Every finding names **actor, path, asset, severity** (severity per epic #222: exploitability x asset). This is a public document: no working exploit strings, live endpoints, or credential locations appear here. Where exploitable detail exists it is marked "(exploitable detail -> private SECURITY.md channel)".

## Findings summary

| ID | Severity | Boundary | Path | One-line |
|---|---|---|---|---|
| FINDING-S1 | High | Output rendering (XSS) | `apps/stacker/src/lib/modules/retriever/components/ChatMessage.svelte` | Assistant/model output rendered through `marked.parse()` into `{@html}` with no HTML sanitizer |
| FINDING-S2 | Medium | Auth/session (compensating control) | `apps/stacker/src/hooks.server.ts` | CSP shipped Report-Only, so it does not actually block the XSS-to-token-exfil path the non-HttpOnly cookie depends on |
| FINDING-S5 | Medium | Stripe webhook | `apps/stacker/src/lib/server/stripe-webhook.ts`, `src/routes/api/webhooks/stripe/+server.ts` | `service_role` key in the webhook grants full-DB write authority; blast radius is the entire schema, gated only by Stripe signature verification |
| FINDING-S3 | Low | Auth (JWKS) | `packages/auth/src/evermore_auth/jwks.py` | JWT `iss` (issuer) claim not pinned during validation |
| FINDING-S4 | Low | Auth config | `apps/stacker/supabase/config.toml` | `minimum_password_length = 6`, below the common 8-char baseline |
| FINDING-S6 | Low | Stripe webhook | `apps/stacker/src/lib/server/stripe-webhook.ts` | No application-level event-id idempotency store; replay protection relies solely on Stripe's signature timestamp tolerance |

No **Critical** findings. One **High** finding (FINDING-S1) is filed as a redacted follow-on issue per AC7 (see "Filed follow-on issues" below). Medium/Low findings are recorded here.

## Auth and session (AC5)

**Supabase Auth flow.** Access is invite-only; open signup is disabled (`enable_signup = false` in `supabase/config.toml`, confirmed at both `[auth]` and `[auth.email]`). The SSR flow is the standard `@supabase/ssr` server-client pattern:

- `src/lib/server/supabase.ts` builds a `createServerClient` from `PUBLIC_SUPABASE_URL` and `PUBLIC_SUPABASE_PUBLISHABLE_KEY` (both `PUBLIC_`-prefixed; the publishable/anon key is designed to be public). Cookies are read/written through SvelteKit's `cookies` API.
- `src/hooks.server.ts` `safeGetSession()` calls `getSession()` and then re-validates with `getUser()` (a server round-trip to the Supabase Auth API), discarding the session if `getUser()` errors. This is the correct SSR posture: the session is not trusted on the strength of the cookie alone; the user is server-verified on every request. The `authGuard` handle redirects unauthenticated requests to `/login` for `/app`-prefixed paths and bounces authenticated users off `/login`.
- `src/routes/auth/confirm/+server.ts` verifies the email link `token_hash` via `verifyOtp` and establishes the SSR session, redirecting to a `next` target (default `/app`); failures route to the neutral `/auth/error` page. `src/routes/invite/accept/+page.server.ts` requires an already-authenticated invite session to set a password (`updateUser`). `src/routes/logout/+server.ts` performs server-side sign-out.

**Token/session lifetime.** `jwt_expiry = 3600` (1 hour access token) with refresh-token rotation handled by Supabase. Reasonable for a staff portal.

**Non-HttpOnly cookie compensating-control verification.** The issue text refers to "ADR 0011"; the actual governing decision in this repo is **`docs/adr/0032-supabase-auth-cookie-non-httponly.md`** (the "ADR 0011" reference is stale; ADR 0011 in this tree is the development-environment decision). Per the epic, this audit **verifies** the documented compensating controls hold in code, it does not relitigate the decision.

The compensating controls are implemented in `hooks.server.ts` `securityHeaders` and applied to every response:

- `X-Content-Type-Options: nosniff` — present.
- `X-Frame-Options: DENY` and CSP `frame-ancestors 'self'` — present (clickjacking defense).
- `Referrer-Policy: strict-origin-when-cross-origin` — present.
- `Permissions-Policy: camera=(), microphone=(), geolocation=()` — present.
- A strict Content-Security-Policy — present in value, but shipped as **`Content-Security-Policy-Report-Only`**, not enforcing.

Verdict: the header controls (nosniff, frame options, referrer policy, permissions policy) hold as documented. The CSP control is only partially in force: because it is Report-Only, it collects violation reports but does **not** block script execution or exfiltration. For a non-HttpOnly cookie whose entire threat is JavaScript reading the token during an XSS, an enforcing CSP is the load-bearing compensating control, and it is not yet enforcing. This is recorded as **FINDING-S2 (Medium)** and it materially raises the severity of the XSS sink in FINDING-S1. The ADR acknowledges the Report-Only status as an interim step pending the SvelteKit `kit.csp` hash/nonce migration; this finding tracks closing that gap, not reopening the cookie decision.

**JWKS verification** (`packages/auth/src/evermore_auth/jwks.py`, shared by the FastAPI services). `JwksValidator` uses `PyJWKClient(jwks_url, cache_keys=True)` to fetch and cache signing keys, then `jwt.decode(..., algorithms=["RS256","ES256"], audience="authenticated")`.

- Algorithms are pinned to two asymmetric families (RS256, ES256); `none` and symmetric `HS*` are excluded, so there is no algorithm-confusion / key-substitution vector.
- Signature, expiry (`exp`, enforced by default), and audience (`aud = "authenticated"`) are all validated.
- The token **issuer (`iss`) is not pinned** (no `issuer=` argument). The JWKS URL is per-project, which constrains which keys can sign, so this is defense-in-depth rather than an open hole, but pinning `iss` to the project's auth URL closes a class of cross-project token-confusion. Recorded as **FINDING-S3 (Low)**.
- `dependencies.py` derives `is_admin` from `payload.app_metadata.is_admin` (Supabase `app_metadata` is server-controlled, not user-editable) and `subscribed_tools` from a JWT claim; both ride on the signature-verified token. `require_admin` (403 on non-admin) and `require_subscription` (403 on missing entitlement) are sound authorization gates.

`minimum_password_length = 6` (`config.toml`) is below the common 8-character baseline: **FINDING-S4 (Low)**. Note `config.toml` governs local/self-hosted only; the hosted project's password policy, Site URL, redirect allow-list, and email templates are set in the Supabase Dashboard / Management API (documented in `apps/stacker/CLAUDE.md`), which this static audit cannot observe. Config-as-code parity for the hosted project is tracked separately (repo memory: hosted Supabase config as code).

## Tenant isolation / RLS (AC2)

Stacker owns exactly one user-scoped table in its own migrations: `public.subscriptions` (`supabase/migrations/20260702000000_subscriptions.sql`). `seed.sql` creates no users or rows (invite-only). The other user-scoped data (animal records, conversation history) lives in the petdata and retriever services and is covered by issues #225 / #226, not here.

| Table | RLS enabled | Row-scoping policy | Enforcement layer | Verdict |
|---|---|---|---|---|
| `public.subscriptions` | Yes (`enable row level security`) | `users_read_own_subs`: `SELECT using (auth.uid() = user_id)` | Database RLS (not app-side filter) | clean |

Observations:

- RLS is the enforcement layer at the database, not an app-side `.eq()` filter. The authenticated role can only `SELECT` its own rows; there is intentionally **no** authenticated `INSERT/UPDATE/DELETE` policy.
- All writes go through the Stripe webhook's `service_role` client, which bypasses RLS by design (see the Stripe webhook section). This is a deliberate, documented split: reads are RLS-gated to the owner, writes are service-role-only from a signature-verified webhook.
- `user_id` is a FK to `auth.users(id)` with `on delete cascade`, so subscription rows do not outlive their user.

No cross-tenant leakage path was found in stacker's own data layer: no server route reads or writes `subscriptions` with elevated privilege outside the webhook, and the module API clients (`src/lib/modules/*/api/`) call the backend services over HTTP rather than touching the database directly.

## Stripe webhook (AC3)

Files: `src/routes/api/webhooks/stripe/+server.ts` (endpoint) and `src/lib/server/stripe-webhook.ts` (logic).

- **Signature verification.** The handler reads the exact raw body via `request.text()` and verifies it with `stripe.webhooks.constructEventAsync(rawBody, signature, webhookSecret, undefined, cryptoProvider)` (the async Web Crypto form required by `adapter-cloudflare`). A missing signature returns 400; a verification failure returns 400 before any database access. Signature verification is present and correct, and it gates all subsequent processing.
- **`service_role` blast radius.** `createStripeAdminClient` builds a `service_role` Supabase client (`persistSession: false`, `autoRefreshToken: false`). `service_role` **bypasses RLS for the entire schema**: although the code only calls `.from('subscriptions').upsert(...)`, the key itself authorizes full read/write to every table. Any code-execution or logic flaw reachable after signature verification would inherit that authority. The mitigating control is that the key is only ever constructed inside this server-only endpoint (confirmed: `env.STRIPE_WEBHOOK_SUPABASE_SERVICE_KEY` is imported via `$env/dynamic/private` and appears in no client-reachable module) and is only exercised after a valid Stripe signature. Recorded as **FINDING-S5 (Medium)**: large blast radius, gated behind signature verification; consider a dedicated least-privilege writer (a `SECURITY DEFINER` RPC or a scoped role limited to `subscriptions`) to shrink it.
- **Replay / idempotency.** The write is an `upsert` keyed on `(user_id, module_id)`, so replaying the *same* event is idempotent (it re-writes the same terminal state). There is **no application-level event-id dedup store and no event-ordering guard**, so replay protection rests entirely on Stripe's signature timestamp tolerance (the default ~5-minute window enforced inside `constructEventAsync`). Within that window, a captured valid event could be replayed, but the upsert makes same-event replay a no-op; across events there is no monotonic-ordering check (a replayed older "active" after a newer "canceled" is time-boxed out by the tolerance rather than by app logic). Recorded as **FINDING-S6 (Low)**.
- **Forged/replayed mutation surface (threats 3, 4).** A forged webhook cannot pass signature verification, so it cannot mutate anything. A replayed valid webhook can, within the tolerance window, only re-assert a subscription row's state via the idempotent upsert; `mapStatus` collapses unknown Stripe states to `incomplete` (the safest non-entitling value), and `customer.subscription.deleted` forces `canceled`. The mutation surface is therefore confined to the `subscriptions` table's entitlement columns, and the checkout path that would set `supabase_user_id` metadata is not yet built (rows without that metadata are acknowledged with 200 and skipped).

## Output rendering / XSS (AC4)

Sink enumeration (grep across `apps/stacker/src` and `packages` for `{@html}`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`):

| Sink | Path | Data source | Escaping | Verdict |
|---|---|---|---|---|
| `{@html renderedContent}` | `src/lib/modules/retriever/components/ChatMessage.svelte:35` | Assistant (retriever LLM) message content, rendered by `marked.parse(content)` | Svelte auto-escaping **bypassed** by `{@html}`; `marked` does **not** sanitize HTML | **FINDING-S1 (High)** |

This is the only raw-HTML sink in scope. All other tenant/user data reaches the DOM through Svelte's default expression interpolation (`{content}`, `{timeStr}`, etc.), which auto-escapes; the user-role branch of the same component renders `{content}` inside a `<p class="whitespace-pre-wrap">`, escaped.

**FINDING-S1 (High).**

- **Actor:** hostile content inside ingested shelter data ("data as actor" / model output as injection vector, threat 1). The retriever module is a RAG system over ingested documents; an attacker who can influence what the model emits (poisoned corpus content, prompt injection) can cause the assistant message to contain arbitrary HTML/JavaScript.
- **Path:** `ChatMessage.svelte` renders assistant messages as `{@html marked.parse(content)}`. `marked` passes raw HTML in its input straight through to output and performs no sanitization (its historical `sanitize` option is removed; the documented guidance is to run a sanitizer such as DOMPurify on the output). The rendered HTML is inserted with `{@html}`, which bypasses Svelte's escaping. Result: model-controlled markup executes in a staff user's authenticated browser session.
- **Asset:** staff session credentials (the Supabase auth cookie is **non-HttpOnly** per ADR 0032, so injected JavaScript can read it), plus any authenticated action or PII reachable from the staff session.
- **Severity: High.** Exploitability is modest-precondition rather than trivial (requires influencing model output, which threat 1 treats as in-scope, and a staff user viewing the poisoned message), but the asset is session credentials sitting behind a single failed layer, and the CSP that would blunt token exfil is Report-Only (FINDING-S2), so it does not block the exfil. The fix is to sanitize `marked` output (e.g., DOMPurify) before `{@html}`, and to land the enforcing CSP.
- Exploitable detail (concrete injection payloads, corpus-poisoning mechanics) -> private SECURITY.md channel; this public entry carries the redacted reference only.

## Client-side secret exposure (AC6)

Scan of `apps/stacker/src` for private env and secret material reaching client code (`$env/static/private`, `$env/dynamic/private`, `SERVICE_ROLE`, `SERVICE_KEY`, `STRIPE_SECRET`, `STRIPE_WEBHOOK`), excluding server-only files (`.server.ts`, `lib/server/`, `+server.ts`, tests):

- **Result: clean.** The only `$env/.../private` import is in `src/routes/api/webhooks/stripe/+server.ts` (a server endpoint), pulling `STRIPE_WEBHOOK_SECRET` and `STRIPE_WEBHOOK_SUPABASE_SERVICE_KEY` via `$env/dynamic/private`. No private env, service-role key, or Stripe secret is referenced from any client-reachable module.
- Client-exposed configuration is limited to `PUBLIC_`-prefixed values (`PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `PUBLIC_RETRIEVER_API_URL`, `PUBLIC_PETDATA_API_URL`). The Supabase publishable/anon key is intended to be public and is RLS-gated. `.env.example` documents only placeholder values.
- SvelteKit's boundary enforces this: `$env/static/private` and `$env/dynamic/private` cannot be imported into client-side code without a build error, so the split is structurally enforced, not just conventional.

## Supabase config-IaC (read completely)

`supabase/config.toml`, `supabase/migrations/*.sql`, `supabase/seed.sql`, and `supabase/templates/{invite,magic_link}.html` were read in full.

- `config.toml`: `enable_signup = false` (invite-only, good), `jwt_expiry = 3600`, `enable_confirmations = false` (moot with signup disabled), `secure_password_change = false` (password change does not require recent re-auth; Low, and local-only), `minimum_password_length = 6` (FINDING-S4). MFA/TOTP and external OAuth providers are present but commented/disabled. No secrets are committed; SMTP and third-party blocks are commented placeholders.
- Email templates are static HTML with only Supabase's own template variables (`{{ .SiteURL }}`, `{{ .TokenHash }}`); no user-controlled interpolation, no injection surface.
- Reminder (from `apps/stacker/CLAUDE.md`): `config.toml` and `supabase/templates/*` govern local/self-hosted only. The hosted project's equivalent settings live in the Dashboard / Management API and are outside this static audit's observable surface.

## Finding disposition (AC7)

Epic #222 requires Critical/High findings to be "filed as follow-on issues **or private reports**," and its public-repo discipline requires that directly exploitable detail for such a finding go to the private channel, never a public tracker.

- **FINDING-S1 (High)** is dispositioned as a **private report**, not a public issue. Publicly filing an unpatched High-severity XSS on a public repository would itself be a disclosure of a live vulnerability, which the epic's discipline forbids. The redacted finding is recorded in this document; the exploitable detail (concrete injection payloads, corpus-poisoning mechanics) and the remediation request are routed to the private security channel in `SECURITY.md` (email `security@backchain.ai`) and are the appropriate content for a GitHub **private security advisory** on this repository. The maintainer should open that private advisory / send the private report; this audit does not autonomously publish the vulnerability.
- **No Critical findings.**
- Medium and Low findings (FINDING-S2, S3, S4, S5, S6) are recorded in this document and rolled up to epic #222 for disposition; per discipline they are not individually filed as public issues.
