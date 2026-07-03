---
title: Stacker Test Effectiveness Audit
prepared_by: Claude Code (daedalus implementer)
updated: 2026-07-03T14:21:23-04:00
purpose: Audit stacker's Playwright e2e specs for effectiveness and rank the missing vitest unit-layer coverage by regression risk.
tags: []
aliases: []
---

# Stacker Test Effectiveness Audit

**Module:** `apps/stacker`
**Date:** 2026-07-03
**Scope:** `apps/stacker/tests/e2e/**` (6 e2e specs) plus a gap map of `apps/stacker/src/**` logic with no vitest unit coverage

## 1. Summary

Module `apps/stacker`. Six Playwright e2e specs were audited: `auth.spec.ts`, `admin.spec.ts`, `chat.spec.ts`, `home.spec.ts`, `security-headers.spec.ts`, `favicon.spec.ts`. Vitest is wired via the `test:unit` script (`vitest run`), but the only existing unit test in the module is `src/lib/server/stripe-webhook.test.ts`; everything else in `src/lib/` runs with zero unit-layer coverage today.

| Verdict | Count | Files |
|---|---|---|
| Keep | 4 | `home.spec.ts`, `favicon.spec.ts`, `security-headers.spec.ts` (strengthened), `auth.spec.ts` (6 of 7 tests unchanged) |
| Rewrite | 1 test | `auth.spec.ts` (`'login form shows error for empty submission'` -> `'login form blocks empty submission via native required validation'`) |
| Delete | 2 files | `admin.spec.ts`, `chat.spec.ts` |

Files edited: `apps/stacker/tests/e2e/auth.spec.ts` (one test rewritten), `apps/stacker/tests/e2e/security-headers.spec.ts` (one assertion added). Files deleted: `apps/stacker/tests/e2e/admin.spec.ts`, `apps/stacker/tests/e2e/chat.spec.ts`.

## 2. Per-spec verdict ledger

| Spec | Verdict | Rationale | Action |
|---|---|---|---|
| `auth.spec.ts` | keep (6) + rewrite (1) | The empty-submission test was mislabeled: it asserted that the email input and submit button were enabled, not that any error behavior occurred. Rewritten to assert native `required` validation actually blocks submission (URL stays `/login`, and the email input's `validity.valueMissing` is `true`). | Rewrote `'login form shows error for empty submission'` as `'login form blocks empty submission via native required validation'`; the other 6 tests are unchanged. |
| `admin.spec.ts` | delete | Its sole test duplicated the `auth.spec.ts` `/app/retriever/admin -> /login` redirect assertion; no unique signal. Authed-admin coverage (the server-side guard checks `locals.user.app_metadata.is_admin`) needs a Supabase auth harness that does not exist yet. | Deleted the file; the authed-admin gap is recorded in section 5 (Follow-on). |
| `chat.spec.ts` | delete | Its sole test duplicated the `/app/retriever/chat -> /login` redirect assertion, same pattern as `admin.spec.ts`. Authed chat interaction needs the same auth harness. | Deleted the file; recorded as a gap in section 5 (Follow-on). |
| `home.spec.ts` | keep | Two smoke tests assert rendered outcomes (heading text, tagline text, sign-in link visibility), not structure alone. | none |
| `security-headers.spec.ts` | keep + strengthen | Verifies the hardening headers set by `hooks.server.ts`, which is exactly its job, but it never checked `Permissions-Policy` even though `hooks.server.ts` sets it alongside the other headers. | Added `expect(headers['permissions-policy']).toBe('camera=(), microphone=(), geolocation=()')`; all existing assertions kept. |
| `favicon.spec.ts` | keep | Verifies favicon wiring (declared `<link rel="icon">`) and reachability (real HTTP status and content-type) with concrete outcome assertions. | none |

## 3. Flake-surface findings

All six specs rely on Playwright's built-in auto-waiting: `toHaveURL`, `getByRole`, and `request.get` all poll/await internally. None of the specs call `page.waitForTimeout` or any arbitrary sleep. The Playwright config runs with `fullyParallel: true`, and every test in every spec is independent (each navigates fresh and asserts on its own outcome), so there is no order dependence between tests or between specs. The network coupling in `security-headers.spec.ts` and `favicon.spec.ts` (real `request.get` calls against a running server) is intrinsic to their job: they exist specifically to assert real server response headers and status codes, not incidental flakiness. Conclusion: no flakes to ticket.

## 4. Ranked unit-layer gap map

Vitest is configured (`test:unit`), but the only existing unit test is `src/lib/server/stripe-webhook.test.ts`. The rest of `src/lib/` has no unit coverage. Ranked by regression risk:

### High

| Rank | Target | Untested behavior | Why it matters |
|---|---|---|---|
| 1 | `src/hooks.server.ts` (`authGuard`) | Protected-path redirect (`/app/**` without a session -> `/login`); authed `/login` -> `/app` redirect; `safeGetSession` returning `{ session: null, user: null }` when `getUser()` errors even though a session cookie exists. | This is the auth/authz core for the whole portal. Only the unauthenticated redirect off a protected path is covered, and only at the e2e layer (`auth.spec.ts`); the authed-redirect-away-from-login branch and the session/getUser-error edge case have no coverage at any layer. |
| 2 | `src/lib/api/base-client.ts` | Trailing-slash `baseUrl` normalization; `Authorization: Bearer <token>` header injection; `Content-Type` omitted when the body is `FormData`; timeout/`AbortController` wiring; non-ok response mapped to `ApiError(status, body)`. | Every module API call (retriever, petdata) is built on this client. Zero tests exist for it, so a regression here silently breaks every module's data fetching at once. |
| 3 | `src/lib/portal/config.ts` | `parseEnabledModules` env-string parsing; `isModuleEnabled`; `resolveModuleStatus` (disabled / active / locked); `getModulesWithStatus` filtering. | This gates which modules a shelter user can see and access in the portal shell. A parsing or status-resolution bug here either hides a paid module or exposes a locked one. |

### Medium

| Rank | Target | Untested behavior | Why it matters |
|---|---|---|---|
| 4 | `src/lib/portal/state/animal-subject.svelte.ts` | localStorage persistence; malformed-JSON guard on read; shape validation inside `initAnimalSubject`. | Cross-module state; a silent failure here desyncs which animal the portal thinks is "in context" across modules. |
| 5 | `src/lib/portal/theme/theme-store.svelte.ts` | `VALID_THEMES` guard inside `setTheme`; initialization from storage. | Guards against an invalid stored theme value breaking the UI on load; small surface but user-visible if it regresses. |
| 6 | `src/lib/modules/{retriever,petdata}/api/client.ts` | Endpoint path construction; `encodeURIComponent` applied to path ids; FormData upload path; DELETE calls. | Each module's typed API surface sits directly on `base-client.ts`; id-encoding or path-construction bugs would misroute or fail requests for retriever/petdata data. |

### Low

| Rank | Target | Untested behavior | Why it matters |
|---|---|---|---|
| 7 | `src/lib/portal/user-display.ts` | `initialsFromEmail` / `displayNameFromEmail` / `firstNameFromEmail` edge cases: null/undefined input, single-part local part, empty string. | Pure functions with no side effects; cheap, high-confidence wins, but cosmetic (display-only) so ranked lowest. |

`src/lib/server/stripe-webhook.ts` already has `stripe-webhook.test.ts` and is excluded from this gap map.

## 5. Follow-on

A follow-on issue is filed (the lead will file it) to stand up the vitest unit layer scoped from section 4, starting with the High-ranked targets (`hooks.server.ts` authGuard, `base-client.ts`, `portal/config.ts`). Authed admin and chat e2e coverage (the gaps left by deleting `admin.spec.ts` and `chat.spec.ts`) is blocked on a Supabase auth test harness (session-cookie injection or equivalent test helper) that does not exist yet in this module.
