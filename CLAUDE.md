# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Evermore is

An AI platform for nonprofit animal shelters: it ingests animal data from any shelter system, generates research-backed adoption marketing, answers staff questions, and is measured against one outcome, more healthy, safe, and permanent adoptions. It rides on top of existing shelter management systems (Shelterluv and peers) rather than replacing them. Owned by Backchain LLC, Apache-2.0. Initial design partner: Friends of Homeless Animals (FOHA), pro bono.

**Read the canonical docs before doing real work:**
- Product and architecture: `docs/evermore-vision-and-architecture.md`
- Decisions: `docs/adr/0001-monorepo-structure.md`, `0002-github-native-project-management.md`, `0003-standardized-tech-stack.md`
- The execution plan: `docs/plans/repo-restructure-and-rename.md`
- Research corpus: `docs/research/README.md`

## Current state: mid-consolidation

This is **transitioning from four separate git repositories into one monorepo.** Until Phase 2 of the restructure plan runs, the four modules still exist as their own git repos under this directory and are git-ignored at the root:

| Now (separate repo) | Becomes |
|---|---|
| `petbio/` | `services/petdata/` (also a code-level rename, not just a move) |
| `retriever/` | `services/retriever/` |
| `stacker/` | `apps/stacker/` |
| `platform/` | retires; its docs fold into `docs/` |
| (new) | `services/biowriter/` |

The root git repo currently tracks documentation and scaffold only. Do not commit the four module directories as plain files; they consolidate with history via `git subtree` (plan Phase 2).

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

- This directory is not yet fully under one git history; treat moves and deletes carefully and get approval before deleting.
- User-visible content avoids em-dashes (use colons, parentheses, commas).
- Per-module build/test commands live in each module's own `CLAUDE.md` until consolidation; the tech-stack standard governs all of them.
