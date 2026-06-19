# ADR 0002: GitHub-native project management

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner

## Context

We assume open-source growth and outside contribution to Evermore. We want work tracking that is portable and familiar to contributors. The project is consolidating into a single monorepo (ADR 0001), where GitHub Issues (which are per-repo) become coherent rather than fragmented.

Evermore work currently lives in the operator's consulting Beads database (prefix `prof-`): two epics (`prof-iqb` "Build Evermore subscription portal foundation", 20 children; `prof-0e1` "Launch Evermore portal MVP", 10 children) plus a handful of standalone retriever issues, labeled `appevr` / `appstkr` / `apppetb` / `apprtvr`. Beads is CLI-first and single-operator-oriented; it is unfamiliar to drive-by contributors.

## Decision

Use **GitHub-native project management** for Evermore:

- **GitHub Issues** for work items; **GitHub Projects (v2)** for planning and flow; **Pull Requests** for change.
- **`anthropics/claude-code-action@v1`** for `@claude` PR and issue workflows.
- **Issue templates** (bug, feature, task) and a **PR template** in `.github/`; `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `good-first-issue` and `help-wanted` labels for contributor onboarding.
- **Retire Beads for Evermore.** Do not initialize `evermore/.beads`.
- **Migrate** the existing Evermore issues from the consulting Beads database to GitHub Issues, then close the `prof-iqb` and `prof-0e1` epics in Beads as "migrated to GitHub."

Label taxonomy (ported from the design we settled on, now as GitHub labels):

- **component** (one required): `petdata`, `biowriter`, `retriever`, `stacker`, `platform`
- **area** (optional): `auth`, `subs`, `schema`, `ux`, `data`, `research`, `eval`, `infra`
- **milestone**: the `v1` kennel-card wedge, plus module milestones as needed

## Consequences

- Contributor-friendly and portable; one tracker for the whole monorepo.
- Evermore's tracking diverges from the operator's consulting Beads workflow. This is intentional and correct for an OSS product.
- The Beads → GitHub migration is a one-time scripted step (`gh issue create` from a Beads export, with labels and milestones mapped).
- `platform/CLAUDE.md` (which documented Beads tracking and the wrong label names) is rewritten during consolidation.
