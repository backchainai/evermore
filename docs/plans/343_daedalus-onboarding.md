---
title: Onboard evermore to the daedalus SDLC
issue: 343
type: Task
date: 2026-11-20
---

# Onboard evermore to the daedalus SDLC

## Context

Implements the acceptance criteria of #343: the six daedalus Makefile targets, `.claude/settings.json` enablement and denials, CLAUDE.md `## Commands` and `## Issue tracker`, the four artifact folders, `REVIEW.md`, CI coverage of the gate, and removal of the stale `.daedalus/config.json`.

Operator decisions taken in planning:

1. ADRs move from `docs/adr/` into `docs/decisions/` with daedalus names (`NNNN_slug.md`), and every live reference is repointed.
2. ADR 0030 (per-service Supabase projects) is marked `proposed` but is accepted in practice; the operator confirmed it, so it moves with the rest as `status: accepted`. ADR 0033 (listing-sync verification) is still a proposal, which the decision schema rejects. It moves to `docs/planning/` and returns through `/daedalus:decide` when accepted. Its number stays unused.
3. No `check.yml`. `ci.yml` already runs the gate per module behind path filters; it gains the jobs it lacks (grader, `packages/*`, stacker unit tests).

`docs/CLAUDE.md` makes ADRs append-only, so the move edits only metadata and references:

- Each file gets frontmatter `title` set to its existing H1 verbatim (so H1 equals title), `date` from its existing frontmatter or `Date` line, and `status` taken from the `docs/adr/README.md` index, lowercased, except that 0030 is `accepted` per the operator. That corrects 0008 and 0019, whose frontmatter says `accepted` while their bodies and the index say superseded; both get `status: superseded` and `superseded_by` naming the successor's new path.
- Existing extra keys (`adr`, `tags`, `supersedes`, `superseded_by`, `related`) stay; `superseded_by` paths are repointed. `0021`'s inline `# proposed | ...` comment on `status` is removed so the value parses.
- Live links and backticked filename references are repointed, including sibling links between ADRs and links to 0033, which now point to `docs/planning/`.
- Provenance lines (`> Renumbered from docs/adr/...`, `> Migrated from ...`), the README's old-to-new mapping, the two CHANGELOGs, and `docs/security/coverage-ledger.md` (the #224 audit record) are history and stay as written.
- No other ADR body prose changes.

Makefile design. There is no root pyproject, so targets loop over `PY_MODULES := services/petdata services/retriever services/grader packages/auth packages/llm packages/schema` with `uv run --frozen`. Ruff is scoped to `src/ tests/` as CI does, because bare ruff fails today on petdata's and retriever's `alembic/` (see Experiments).

- `setup`: per module `uv sync --locked --all-extras`; in stacker `npm ci`, `[ -f .env ] || cp .env.example .env`, `npx svelte-kit sync`.
- `test`: per module `pytest` (default addopts exclude integration); stacker `npm run test:unit`.
- `lint`: per module `ruff check src/ tests/` and `mypy src/`; stacker `npm run check`.
- `format`: per module `ruff format src/ tests/`.
- `check`: `test` and `lint`, plus per module `ruff format --check src/ tests/`.
- `verify`: `check`, then `petdata-integration`, then stacker `npm run gen:types`, `git diff --exit-code` on the two `types.generated.ts` files, and `npm run build`.
- `petdata-integration`: fails fast with a clear message when port 5434 is already bound; runs `docker compose -p petdata-test -f docker-compose.test.yml up -d --wait`, then `alembic upgrade head` and `pytest -m "integration or not integration"` with `TEST_DATABASE_URL` and `PETDATA_DATABASE_URL` set to `postgresql+asyncpg://postgres:postgres@localhost:5434/petdata_test`, saves the exit status, always runs `down` on the `petdata-test` project, and exits with the saved status.

Existing dev targets (`env`, `dev`, `dev-full`, `down`, ...) are untouched. Petdata's CI also runs `uvx bandit`, which `make check` does not; CLAUDE.md `## Commands` records that gap rather than adding a dependency here.

## Files

- `Makefile`
- `.claude/settings.json`
- `.gitignore`
- `CLAUDE.md`
- `REVIEW.md`
- `.github/workflows/ci.yml`
- `docs/intents/README.md`
- `docs/specs/README.md`
- `docs/plans/README.md`
- `docs/decisions/`
- `docs/adr/`
- `docs/planning/proposal_listing-sync-verification.md`
- `docs/CLAUDE.md`
- `README.md`
- `docs/architecture.md`
- `docs/auth-flow.md`
- `docs/cloudflare-ai-gateway-setup.md`
- `docs/evermore-vision-and-architecture.md`
- `docs/module-template.md`
- `docs/security/data-integrity-recovery.md`
- `docs/security/stacker-packages-audit.md`
- `docs/security/threat-model.md`
- `packages/auth/README.md`
- `packages/llm/README.md`
- `apps/stacker/src/hooks.server.ts`
- `services/petdata/CLAUDE.md`
- `services/petdata/README.md`
- `services/petdata/docs/design/development-standards.md`
- `services/petdata/docs/design/architecture.md`
- `services/petdata/docs/design/phase1-data-extraction.md`
- `services/retriever/CLAUDE.md`
- `services/retriever/docs/development-standards.md`
- `services/retriever/docs/architecture.md`
- `services/retriever/docs/guides/deployment.md`

`.daedalus/config.json` is untracked; it is deleted locally, not committed.

## Work order

1. Add the six targets and `petdata-integration` to `Makefile` and `.PHONY`. Check: `make setup && make check` exits 0, and `time make check` is recorded for step 4. Commit.
2. Move the decisions. `git mv` each `docs/adr/NNNN-slug.md` to `docs/decisions/NNNN_slug.md`; `0021` becomes `0021_apache-2-0-licensing.md`, since the slug pattern forbids `.`. Move 0033 to `docs/planning/proposal_listing-sync-verification.md`. Delete `000-template.md`, which the decide skill's template replaces. Turn `docs/adr/README.md` into `docs/decisions/README.md`: the daedalus folder table above the existing index, with the 0030 row marked accepted and the 0033 row pointing to `docs/planning/`. Normalize frontmatter as in Context. Repoint references matching `docs/adr/`, `adr/`, and bare `[0-9]{3,4}-[a-z0-9.-]+\.md` across the Files list. Rewrite `docs/CLAUDE.md`: its intro, the `adr/` section (now `decisions/`, naming the one-time metadata normalization), and "What is not here", so it lists `docs/intents/`, `docs/specs/`, `docs/plans/`, `docs/decisions/`, and `docs/planning/` (proposals), each pointing to its README. Checks:
   - `daedalus.sh check-docs` exits 0.
   - A one-off link check, run from the scratchpad, finds every relative `.md` link and backticked `docs/...` or `NNNN[-_]slug.md` reference outside the history exclusions resolving to an existing file.
   - Each decision's `status` matches the index.
   - `make check` exits 0.

   Commit.
3. Record ADR 0039, `docs/decisions/0039_adopt-daedalus-sdlc.md`, from the decide template: evermore develops through the daedalus SDLC, with decisions in `docs/decisions/`; it relates to ADR 0023. Check: `check-docs` exits 0. Commit.
4. (parallel with 5) Write the three remaining scaffolding files and settings:
   - `docs/intents/README.md`, `docs/specs/README.md`, and `docs/plans/README.md` from the daedalus template.
   - `REVIEW.md` from the template, with Project specifics for evermore: no client or branded SMS names, Supabase RLS and auth path changes, and secrets kept in `.env`.
   - `.claude/settings.json`, merged: the daedalus plugin, the three marketplaces, and the merge, review, force-push, and reset denials, keeping the supabase enablement.
   - `CLAUDE.md`, adding `## Commands` (the six targets; the healthy `make check` tail with changing numbers as `N`; the measured run time; notes that `ci.yml` runs the gate per module, that `make verify` needs Docker, and that bandit runs only in CI) and `## Issue tracker` (GitHub Issues on `backchainai/evermore`).

   Delete `.daedalus/config.json`. Check: `make check` and `check-docs` exit 0. Commit.
5. (parallel with 4) In `ci.yml`:
   - Add `grader` and `packages` path filters.
   - Add a `grader` job and a `packages` matrix job (auth, llm, schema), each running `uv sync --locked --all-extras`, `ruff format --check src/ tests/`, `ruff check src/ tests/`, `mypy src/`, and `pytest`.
   - Add `npm run test:unit` to the stacker job after `npm run check`.
   - Add the new jobs to `ci-success` needs and results.

   Check: `make check` exits 0, and the workflow parses under `actionlint` (via `npx` or `uvx`) or a YAML load. Commit. Comment on #316 (wire grader into CI) that the grader CI part landed here.

Departure (step 4): `.gitignore` ignored all of `.claude/`, so `.claude/settings.json` could not be committed; it now ignores `.claude/*` except `settings.json`. The `.daedalus/config.json` deletion was refused by the auto-mode classifier and is left to the operator.

## Tests

No new test files. The change is the gate itself:

- `make check` runs the existing unit suites of all six Python modules and stacker's vitest suite.
- `make verify` adds petdata's integration suite against Postgres, plus the stacker type-drift and build checks.
- `check-docs` validates every moved decision.

## Verification

- `make check` exits 0.
- `make verify` exits 0 with Docker running, and leaves no `petdata-test` container behind, including after a deliberately failing run.
- `daedalus.sh check-docs` exits 0.
- The step 2 link check reports no unresolved reference.
- A new session on the branch prints the daedalus SDLC status.
- On the pull request, `ci.yml` runs and passes the grader, packages, and stacker jobs.

## Experiments

- Every Python module passes ruff, mypy, and unit pytest: ruled out for bare ruff. Evidence: in a sandbox copy, `uv run --frozen ruff check` exits 1 in petdata (6 errors in `alembic/`) and retriever (10 in `alembic/env.py`), and `ruff format --check` exits 1 in both on one migration each. Scoped to `src/ tests/`, both exit 0. Sync, pytest, and mypy exit 0 in all six modules, and no unit test needs network, Docker, or `.env`. Plan change: ruff scoped to `src/ tests/`.
- Stacker `check` and `test:unit` pass read-only without setup: ruled out. Evidence: without `.env`, `npm run check` exits 1 (12 missing `$env/static/public` members). On a fresh tree, `test:unit` exits 1 until `svelte-kit sync` creates `.svelte-kit/tsconfig.json`. With `.env` copied from `.env.example` and a sync, both exit 0 (19 tests), and no tracked file changes. Plan change: `setup` creates `.env` and runs `svelte-kit sync`.
- `make verify` runs locally against `make petdata-db-up`: ruled out for the database step, unknown for the integration run itself. Evidence: `docker-compose.yml` creates `petdata`; only `docker-compose.test.yml` creates `petdata_test` (both on port 5434). Docker was unavailable in the sandbox, so alembic and the integration pytest were not run. The stacker half (gen:types, no diff, build) exits 0 with `.env`. Plan change: `petdata-integration` uses `docker-compose.test.yml`.

## Architect review

- Important: the `docs/adr` grep check could not pass without rewriting ADR provenance lines -> amended: provenance lines, the README mapping, the CHANGELOGs, and the coverage ledger are history; a link check replaces the grep.
- Important: repointing by `docs/adr/` misses sibling ADR links, bare backticked filenames, and `adr/` without a prefix -> amended: repoint by all three patterns, and the link check covers them.
- Important: `docs/module-template.md` and `docs/security/threat-model.md` hold ADR references and were missing from Files -> amended: added.
- Important: the source of `status` was unstated, and 0008/0019 frontmatter wrongly says `accepted` -> amended: status comes from the README index, 0008/0019 become `superseded` with successors, and a check compares status to the index.
- Important: `docs/CLAUDE.md` also says there is no plans directory and counts four kinds of content -> amended: step 2 rewrites the intro and "What is not here".
- Important: `petdata-integration` left the container up on failure and shared the `petdata` compose project -> amended: separate `petdata-test` project, `down` always runs, and a fail-fast port check.
- Important: the em-dash rule is a regex check, not reviewer judgment -> partly amended: REVIEW.md no longer lists it. A lint gate for it is new enforcement outside #343's acceptance criteria, with an unknown count of existing hits, so it is left for a follow-up issue.
- Nit: `make check` drops petdata's bandit run -> amended: the gap is recorded in CLAUDE.md `## Commands`; adding bandit as a locked dependency is out of scope.
- Nit: living docs call 0030 an ADR or current, and the operator should confirm it is unaccepted -> amended: the operator confirmed 0030 is accepted, so it stays in `docs/decisions/` as `accepted` and those mentions stand.
- Nit: `docs/security/coverage-ledger.md` is an audit record -> amended: left as history and removed from Files.
- Nit: the Stop hook runs `make check` at every turn end -> amended: the measured time goes into `## Commands`; if it exceeds about two minutes, stacker `svelte-check` moves to `verify` with the operator's agreement.
