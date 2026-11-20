---
title: Evermore develops through the daedalus SDLC
date: 2026-11-20
status: accepted
related: [23]
---

# Evermore develops through the daedalus SDLC

## Context

ADR 0023 (`0023_github-native-project-management.md`) chose GitHub Issues, Projects, and pull requests as the work tracker. It did not say how an issue becomes a merged change. Work in this monorepo spans a Python service tier, shared packages, and a SvelteKit portal, with no single command that proves a change is sound, and decisions were recorded in `docs/adr/` with no schema or validation. Issue #343 (onboard evermore to the daedalus SDLC) asks to adopt the daedalus plugin, which gates code edits on a committed plan and runs one quality gate through Makefile targets.

## Decision

Evermore develops through the daedalus SDLC. Every code change starts from a GitHub issue, carries a committed plan in `docs/plans/` (and, for a Feature, an intent in `docs/intents/` and a spec in `docs/specs/`), and ships as one pull request after `make check` and `make verify` pass. Architecture decisions live in `docs/decisions/` as `NNNN_<slug>.md`, written through `/daedalus:decide` and validated by `check-docs`. The six Makefile targets (`setup`, `test`, `lint`, `format`, `check`, `verify`) are the one interface between the loop, local runs, and CI. This builds on ADR 0023 and does not change where work is tracked.

## Consequences

Edits outside `docs/` are refused until a plan is committed, which adds a planning step to small changes. `make check` runs at every turn end, so its run time is a recurring cost; if it grows past about two minutes, the slower stacker checks move to `verify`. `make verify` needs Docker for petdata's integration suite. Petdata's `bandit` scan still runs only in CI, a gap recorded in CLAUDE.md. ADR 0033 stays a proposal in `docs/planning/` until it is accepted, because the decision schema allows only `accepted` and `superseded`.
