# ADR 0034: Invite-only magic-link authentication for volunteer sign-in

- Status: accepted
- Date: 2026-09-06
- Deciders: project owner
- Relates to: ADR 0030 (per-service Supabase projects), ADR 0032 (Supabase auth cookie)

## Context

Volunteers are being brought in to rewrite adoption profiles, which turns stacker sign-in from a scaffold concern into a launch blocker. Access is already invite-only and admin-provisioned, and open self-serve signup is off (`apps/stacker/CLAUDE.md`).

The login page contradicts that. `apps/stacker/src/routes/login/+page.svelte` renders a required password input (lines 49 to 58) and `apps/stacker/src/routes/login/+page.server.ts:14` calls `supabase.auth.signInWithPassword`. An invited volunteer has no password to type. Worse, the field advertises a sign-in method that cannot work for them, so the page misleads the exact users it is being opened for.

Magic-link delivery already exists end to end: the template `apps/stacker/supabase/templates/magic_link.html` is registered at `apps/stacker/supabase/config.toml:243`, and `apps/stacker/src/routes/auth/confirm/+server.ts` verifies the link's `token_hash` (`verifyOtp`) and establishes the SSR session, landing the user authenticated on `/app`.

## Decision

A magic link sent to the invited email address is the only sign-in method for Evermore.

- The operator creates the account directly in the auth database (Supabase Studio or a service-role call) and then sends the invite. There is no self-service signup.
- There is no domain-based allowlist. Membership is granted per address by the operator.
- The password sign-in path is removed from the login UI.

## Consequences

- Supabase `enable_signup = false` stays as it is. Verified in `apps/stacker/supabase/config.toml` at line 169 (`[auth]`), line 204 (`[auth.email]`) and line 255 (`[auth.sms]`). One scope limit, already recorded in `apps/stacker/CLAUDE.md`: `config.toml` governs local and self-hosted only, so a hosted project's signup setting, redirect allow-list and email templates must be set in the Dashboard or Management API. Whether the hosted project matches the committed config is not verified here.
- Domain-allowlisted signup is deferred, not cancelled. If the shelter's own email domain later becomes a reliable membership signal, it can return as an additive path.
- **The order of work is fixed: production SMTP first, then magic-link sign-in, and the password form comes out as part of that same change.** Magic link cannot deliver mail until SMTP is configured for the hosted project: `[auth.email.smtp]` is still commented out in `apps/stacker/supabase/config.toml` (lines 220 to 227), and Supabase's built-in mailer is limited to testing volumes. Nothing in the app requests a link yet either: `signInWithOtp` appears nowhere in the tree, and `apps/stacker/src/routes/login/+page.server.ts:14` (`signInWithPassword`) is the only working sign-in path today, even though the callback half already exists at `apps/stacker/src/routes/auth/confirm/+server.ts`. Removing the password form before magic link can actually deliver mail would leave nobody able to sign in, the owner included. The two halves are tracked as issue #157 (production SMTP for auth email) and issue #158 (passwordless magic-link sign-in, which is where the password form is removed).
- **Blocker before any volunteer is invited: the portal layouts hardcode admin rights.** `apps/stacker/src/routes/app/petdata/+layout.server.ts:7` and `apps/stacker/src/routes/app/retriever/+layout.server.ts:7` both return `isAdmin: true`, each with a comment marking it a stub pending a real role check. An invited volunteer would land with admin rights in both modules. The stub must be replaced with a real role check before the first invite goes out. This ADR changes no code; that fix is tracked separately.
- Open, and not decided here: the invite email template routes to `/invite/accept` with `type=invite`, and that page sets a password (`apps/stacker/src/routes/invite/accept/+page.server.ts:31`, `updateUser({ password })`). With magic link as the only sign-in method, the set-password step in the invite flow has no purpose. Whether to retire that route or hold it for a future password path is unresolved.
- No in-app magic-link request form exists today: sending a link is an operator action from Supabase Studio or a service-role call. A self-serve "email me a link" form on the login page is the natural next step and is not part of this decision.

## Alternatives considered

- **Keep password sign-in alongside magic link.** Rejected: without transactional email there is no password reset or verification, so a volunteer who forgets or mistypes is stuck, and offering two visible methods invites the one that does not work.
- **Hide the password field but keep the server action.** Rejected as the decision: a hidden-but-live credential path is a surface to maintain and to get wrong. Removing it from the login UI is what is decided; the server action's fate follows from that.
- **Domain-based allowlisted self-service signup.** Deferred: it assumes a stable shelter email domain for volunteers, which is not established. Per-address invitation is exact and needs no such assumption.
