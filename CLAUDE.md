# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Evermore is

An AI platform for nonprofit animal shelters: it ingests animal data from any shelter system, generates research-backed adoption marketing, answers staff questions, and is measured against one outcome, more healthy, safe, and permanent adoptions. It rides on top of the Shelter Management System (SMS) a shelter already runs rather than replacing it. Owned by Backchain LLC, Apache-2.0. Initial design partner: a nonprofit animal shelter, served pro bono.

**Read the canonical docs before doing real work:**
- Product and architecture: `docs/evermore-vision-and-architecture.md`
- Decisions: `docs/adr/0001-monorepo-structure.md`, `0002-github-native-project-management.md`, `0003-standardized-tech-stack.md`
- The execution plan: `docs/plans/repo-restructure-and-rename.md`
- Research corpus: `docs/research/README.md`

## Current state: consolidated monorepo (post Phase 2)

The four formerly-separate module repos are now tracked directly in this one git repo. Phase 2 imported each module's committed tree as a clean snapshot (a true monorepo: no submodules, no subtrees, no nested `.git`); the granular pre-consolidation history lives in the archived `ckrough/*` origin repos, not here. Per-module build and test commands live in each module's own `CLAUDE.md`; the tech-stack standard governs all of them.

| Module path | From | Notes |
|---|---|---|
| `services/petdata/` | `petbio` | Directory moved. The code-level `petbio` -> `petdata` rename (Python package, imports, env prefix) is still pending (plan Phase 3); the package inside is still named `petbio`. |
| `services/retriever/` | `retriever` | The inner `backend/` was flattened up to the service root. |
| `apps/stacker/` | `stacker` | SvelteKit portal. |
| `services/biowriter/` | (new) | Not yet scaffolded (plan Phase 5/6). |

`platform` is retired; its docs (`architecture.md`, `auth-flow.md`, `subscriptions.md`, `module-template.md`) folded into `docs/`.

Pending follow-ups from the plan: physically remove the now-unused top-level `petbio/`/`retriever/`/`stacker/`/`platform/` directories and drop their `.gitignore` entries (Phase 2 cleanup); the `petbio` -> `petdata` code rename (Phase 3); FOHA scrub before the repo flips public; tech-stack conformance (Phase 5).

## The data spine (settled vocabulary, do not overload)

`Sources -> Animal Record -> Package -> Composition -> Export`

- **Animal Record:** canonical normalized data for one animal (Pet Data owns it).
- **Package:** a curated, versioned, named evidence selection; every item carries provenance `{source, location, category}`.
- **Composition:** the generated + human-edited piece (Package + Template + edits); auto-versioned, retains provenance.
- **Export:** a flat file (PDF/DOCX/Drive) rendered from a Composition; no provenance.
- **"Extraction"** means retrieving existing data out of a shelter system (a Pet Data capability), not distilling research.

## Settled decisions

- **Monorepo** (ADR 0001), owner `github.com/backchainai`, repo `evermore`.
- **GitHub-native tracking** (ADR 0002): Issues + Projects + PRs + the Claude Code action. Beads is retired for Evermore; do **not** `bd init` here. Existing issues migrate from the consulting Beads db to GitHub.
- **Aggressive tech-stack standardization** (ADR 0003): every module conforms to `~/.claude/standards/tech-stack-standard.md`; nothing is grandfathered. Heavy lift is petdata's SQLite -> Supabase Postgres migration.
- **The wedge:** the research-backed kennel card.

## Working conventions

- The repo is now under one git history. Treat moves and deletes carefully and get approval before deleting.
- User-visible content avoids em-dashes (use colons, parentheses, commas).
- Per-module build/test commands live in each module's own `CLAUDE.md`; the tech-stack standard governs all of them.
- FOHA is still referenced in imported module code, tests, and docs. Removing it is a tracked prerequisite before the repo goes public; do not add new references.
