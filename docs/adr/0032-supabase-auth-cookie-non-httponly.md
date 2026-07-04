# ADR 0011: Keep the Supabase auth cookie non-HttpOnly, mitigate with compensating controls

> Renumbered from docs/adr/0011-supabase-auth-cookie-non-httponly.md.

- Status: Accepted
- Date: 2026-06-30
- Deciders: project owner
- Pairs with: ADR 0009 (per-service Supabase projects), `docs/auth-flow.md` (SSR auth flow)

## Context

The `sb-<project-ref>-auth-token` cookie issued by `@supabase/ssr` is not flagged HttpOnly, so it is readable from `document.cookie` in the browser. This was verified on 2026-04-15 with a Playwright check and re-validated on 2026-06-29 against the cookie-writing path at `apps/stacker/src/lib/server/supabase.ts`, where `createServerClient`'s `setAll` forwards the library's cookie options unchanged (no HttpOnly is set, and setting one here would not match the cookie the browser client expects). A script-readable session token is reachable by any successful cross-site-scripting (XSS) payload.

HttpOnly is architecturally incompatible with the current transport. `apps/stacker/src/routes/+layout.ts` builds the client session with `createBrowserClient`, which reads the session from cookies on the client. An HttpOnly cookie is invisible to `document.cookie`, so the browser client could no longer read the session, breaking client-side hydration of the authenticated state. Flagging the cookie HttpOnly would force an SSR-only session model: a larger transport rewrite, not a flag flip.

## Decision

Keep the `sb-*-auth-token` cookie non-HttpOnly. Accept that the token is script-readable, and reduce the XSS attack surface that would let an attacker reach it with compensating controls instead of changing the cookie flag.

## Compensating controls

(a) **Hardening response headers (landed now).** `apps/stacker/src/hooks.server.ts` sets, on every response: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY` (plus `frame-ancestors 'self'` in the CSP), and a minimal `Permissions-Policy` (`camera=(), microphone=(), geolocation=()`).

(b) **Content-Security-Policy-Report-Only (landed now), as the rolling-out CSP.** A strict policy ships in Report-Only mode so it collects violation reports without breaking production. It is Report-Only, not enforcing, for two reasons specific to this app: SvelteKit injects inline hydration scripts, so a hand-rolled enforcing `script-src 'self'` without SvelteKit's own hash/nonce integration would break hydration; and Supabase JS connects at runtime to a per-environment external URL (`PUBLIC_SUPABASE_URL`), so an enforcing `connect-src 'self'` would break auth. The path to an enforcing CSP is SvelteKit's `kit.csp` hash/nonce integration (which emits hashes for the framework's inline scripts) plus a `connect-src` allowance for the Supabase origin. That migration is the follow-up; until it lands, Report-Only is the safe rollout step.

(c) **Trusted Types (future control).** `require-trusted-types-for 'script'` would block string-to-DOM-sink injection (the dominant DOM-XSS vector that could read the cookie). It is named here as a future control because it requires a DOM-sink audit first: any code path that assigns to an injection sink must be routed through a Trusted Types policy before the directive can be enabled without breaking the app.

(d) **Aggressive XSS testing.** The Playwright e2e suite is the place to add adversarial XSS coverage (payloads in user-controlled fields, reflected and stored), so a regression that introduces an injection sink is caught before it ships. The header assertions in `apps/stacker/tests/e2e/security-headers.spec.ts` lock the compensating headers in place.

## Consequences

- The session token remains readable from `document.cookie`. The residual risk is explicit and owned: a successful XSS can exfiltrate the token. The controls above shrink the probability of a successful XSS and the blast radius if one lands.
- The CSP ships Report-Only first, so it collects real violation data from production traffic before any directive is enforced. No request is blocked by the policy in this phase.
- Enforcing CSP and Trusted Types are tracked follow-ups, each gated on prerequisite work (SvelteKit `kit.csp` integration and a Supabase `connect-src` allowance for the former; a DOM-sink audit for the latter).
- `docs/auth-flow.md` "Open security questions" pointed at the HttpOnly question; this ADR resolves it.

## Alternatives considered

- **Flag the cookie HttpOnly.** Rejected: it breaks `createBrowserClient`'s client-side session read in `+layout.ts` and forces an SSR-only session model, a transport rewrite rather than a flag change. The compensating controls reduce the same risk without that rewrite.
- **Enforce the CSP immediately.** Rejected for now: an enforcing `script-src 'self'` breaks SvelteKit's inline hydration scripts, and an enforcing `connect-src 'self'` breaks the runtime Supabase connection to `PUBLIC_SUPABASE_URL`. Report-Only collects the data needed to reach enforcement safely.
