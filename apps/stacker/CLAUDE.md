# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project: Stacker

Unified portal frontend for shelter management tools. Built with SvelteKit, hosts multiple backend service modules behind a single UI.

### Stack

- **Frontend:** SvelteKit + Svelte 5 runes + Skeleton UI v4
- **Styling:** Tailwind CSS v4 + custom portal themes (Daylight, Foundry, Neutral)
- **Icons:** Lucide Svelte
- **Auth:** Supabase Auth (SSR pattern via `@supabase/ssr`)
- **Deploy:** Cloudflare Pages

### Architecture

Stacker is a **portal frontend** that hosts module UIs for independent backend services:

| Module | Backend Service | API URL Env Var |
|--------|----------------|-----------------|
| Retriever | Retriever API (Cloud Run) | `PUBLIC_RETRIEVER_API_URL` |
| Pet Data | Pet Data API (Cloud Run) | `PUBLIC_PETDATA_API_URL` |

Each module provides:
- `src/lib/modules/{id}/index.ts` — `ModuleDefinition` export
- `src/lib/modules/{id}/api/` — TypeScript API client + types
- `src/lib/modules/{id}/components/` — Svelte components (modules with their own UI; Retriever has these, Pet Data ships an API client only so far)
- `src/routes/app/{id}/` — SvelteKit routes

Portal shell lives at `src/lib/portal/` (components, config, theme, types).

## Commands

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Type checking (TypeScript + Svelte)
npm run check

# Production build
npm run build

# E2E tests (Playwright — requires build first)
npm run test:e2e
```

## Adding a Module

1. Create `src/lib/modules/{id}/index.ts` exporting a `ModuleDefinition`
2. Create `src/lib/modules/{id}/api/client.ts` extending `BaseApiClient`
3. Create `src/routes/app/{id}/` with SvelteKit routes
4. Register in `src/lib/portal/config.ts` MODULE_REGISTRY
5. Add `PUBLIC_{ID}_API_URL` to `.env.example`

## Gotchas

**Svelte 5 runes only:** Use `$state`, `$derived`, `$effect`, `$props`. No `writable()` stores.

**Supabase SSR auth:** `hooks.server.ts` uses `getUser()` (server-verified). The `safeGetSession` helper on `event.locals` does both user and session.

**wrangler log errors:** `npm run check` and `npm run build` emit EPERM errors for wrangler log files — harmless.

**Environment files:** `.env` must exist for `svelte-kit sync` to generate `$env/static/public` types. Copy from `.env.example`.
