# ADR 0010: Shared Evermore design system at `packages/design-system/`

> Renumbered from docs/adr/0010-shared-design-system-package.md.

- Status: accepted
- Date: 2026-06-30
- Deciders: project owner
- Relates to: ADR 0001 (monorepo structure), ADR 0003 (standardized tech stack)

## Context

Evermore is an application made of modules: the Stacker portal (SvelteKit) today, with BioWriter, Snapshot, Matchmaker, and Intake to follow. For the suite to read as one product, every module needs the same visual identity: color, type, spacing, motion, and component behavior.

The identity is designed in a Claude Design project ("BioWriter"), which holds the **Evermore design system**: a cool blue/slate product UI with a token-name-compatible architecture so primitives recolor cleanly. The repo had no shared, canonical home for it and no single set of tokens the modules agreed on, so each module was free to diverge.

## Decision

Adopt the Evermore design system as the canonical shared visual system, vendored at a new top-level **`packages/design-system/`**.

- **Location.** `packages/design-system/` is the single source of truth in the repo. A top-level `packages/` directory is introduced for cross-module shared assets; the design system is its first member.
- **Imported layer (the consumed contract).** Tokens (`tokens/{fonts,colors,typography,spacing,base}.css`), the `styles.css` entry point, the three variable fonts (`assets/fonts/`), the `readme.md` guide, `SKILL.md`, and the per-primitive design contracts (`components/**/*.prompt.md` + `*.d.ts`).
- **Not vendored.** The reference React `.jsx` implementations, the compiled `_ds_bundle.js` kit, the specimen guideline cards, and the interactive BioWriter preview stay in the Claude Design project (the canonical design tool) and are pulled in on demand via the `/design-sync` workflow. The repo carries the consumed layer plus the framework-agnostic contracts, not build artifacts or framework-specific source. Stacker's UI is Svelte, so the React primitives are reference, not dependency.
- **Consumption.** Modules consume the tokens as CSS custom properties. Stacker maps them into its Skeleton UI theme; future modules link `styles.css` (or its tokens) directly. The token *names* are Backchain-compatible by design, so primitives port cleanly.
- **Stacker re-skin.** Stacker's three portal themes (light/dark/neutral) and type scale are built on the Evermore palette (blue `#1A7AC2` interactive, slate `#1F3B54` structure, gray `#50636F` body, amber/green/red status) so the running portal matches the system.

## Consequences

- A new top-level `packages/` directory exists; treat it as the home for cross-module shared assets, not service code.
- The design system in the repo is a mirror, not the origin: changes to identity happen in the Claude Design project and sync down via `/design-sync`. The repo copy must not drift into an independent fork.
- The stale Backchain snapshot under `services/biowriter/design/` is now superseded by `packages/design-system/`; migrating BioWriter to consume the shared package is follow-up work (issue #162 follow-ups).
- Every new module inherits the identity by consuming `packages/design-system/` tokens rather than authoring its own theme.
