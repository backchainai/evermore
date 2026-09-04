#!/usr/bin/env bash
# scripts/gate-test.sh -- the repo's tracked `test` gate.
#
# Unit suites only. Each Python command is the one .github/workflows/ci.yml
# runs for that module, minus anything CI stands up infrastructure for; the
# modules CI has no job for (services/grader, packages/auth, packages/llm,
# packages/schema) run the plain `pytest` their own CLAUDE.md / pyproject.toml
# declare. Each module's own markers and ignores are preserved rather than
# re-derived:
#   - retriever: CI's `--ignore=tests/integration`, plus the pyproject addopts
#     it inherits (`-m 'not integration'` and the 80% `--cov-fail-under`), so
#     the local gate enforces the same coverage floor CI does.
#   - petdata: plain `uv run pytest`, whose pyproject addopts are
#     `-m "not integration"` -- the unit suite, no Postgres.
#
# CI-delegated (not run here, by design -- see .daedalus config `ci_delegated`):
#   - petdata's full suite (`pytest -m "integration or not integration"
#     --cov=src`) and the `alembic upgrade head` before it: they need the
#     pgvector Postgres service ci.yml starts. The 85% branch-coverage floor
#     (`fail_under` in petdata's pyproject) is measured over that full suite,
#     so it is CI's gate, not this one -- running --cov over the unit suite
#     alone would report a different number against the same floor.
#   - retriever's tests/integration/ suite: a live-server E2E suite needing
#     Supabase Auth, a running retriever and an LLM gateway (`make dev-full`).
#     Not run in CI either; it is a local pre-release check.
#   - apps/stacker's Playwright suite (`npm run test:e2e`): needs a built
#     frontend plus a preview server and browser binaries. No workflow runs
#     it today.
#   - the container-build job (Docker image builds) and mutation.yml.
#
# apps/stacker's vitest unit suite (`npm run test:unit`, src/**/*.test.ts,
# node environment, no browser) IS run here even though no workflow runs it:
# it is a real unit suite with no infrastructure needs, so it belongs in the
# local test tier.
#
# Toolchain: `uv` is a hard prerequisite (the gate prerequisite Daedalus
# documents, and every Python phase runs through it), so a missing `uv` fails
# up front rather than skipping most of the repo silently. `npm` is not: a
# machine with no Node skips the stacker phase with a loud SKIP line. A
# missing apps/stacker/node_modules is installed with `npm ci` (gitignored,
# and what ci.yml's stacker job does), and a missing .env is created from
# .env.example because svelte-kit cannot generate $env/static/public without
# it.
#
# Every phase runs; failures are collected and reported in one summary at the
# end (the Daedalus gate log keeps only a tail, so one summary listing every
# failed module beats a fail-fast first error in a 7-module tree).
# `uv run --frozen` everywhere: the gate resolves nothing and never rewrites a
# tracked uv.lock.
#
# Run with: bash scripts/gate-test.sh

set -euo pipefail

SELF="scripts/gate-test.sh"

# Repo root from this script's own location, not $PWD: the gate is invoked
# under `sh -c` by hooks/scripts/daedalus-gates.sh and by hand from any
# subdirectory.
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

FAILED=()
SKIPPED=()
RAN=0

# phase <label> <dir> <cmd...> -- run one module's suite from <dir>, record a
# failure instead of aborting the run.
phase() {
  local label="$1" dir="$2"
  shift 2
  printf '\n===== %s  [%s] %s\n' "$label" "$dir" "$*"
  RAN=$((RAN + 1))
  if (cd "$dir" && "$@"); then
    printf '===== PASS %s\n' "$label"
  else
    printf '===== FAIL %s\n' "$label"
    FAILED+=("$label  ($dir: $*)")
  fi
}

# skip <label> <reason> -- a phase whose toolchain is unavailable here.
skip() {
  printf '\n===== SKIP %s -- %s\n' "$1" "$2"
  SKIPPED+=("$1 -- $2")
}

command -v uv >/dev/null 2>&1 || {
  echo "$SELF: uv is not on PATH; it is a gate prerequisite for every Python module (https://docs.astral.sh/uv/getting-started/installation/)" >&2
  exit 1
}

# --- services/retriever (ci.yml `retriever` job) -----------------------------
# Dev tooling lives in [dependency-groups] dev, which uv installs by default.
phase retriever-pytest services/retriever uv run --frozen python -m pytest tests/ --ignore=tests/integration

# --- services/petdata (unit slice of ci.yml's `petdata` job) -----------------
# Dev tooling is an optional extra, so the phase carries `--extra dev`.
phase petdata-pytest services/petdata uv run --frozen --extra dev pytest

# --- services/grader (no CI job; services/grader/CLAUDE.md) ------------------
phase grader-pytest services/grader uv run --frozen --extra dev pytest

# --- packages/* (no CI job; each pyproject's pytest config) ------------------
for pkg in auth llm schema; do
  phase "$pkg-pytest" "packages/$pkg" uv run --frozen --extra dev pytest
done

# --- apps/stacker vitest unit suite ------------------------------------------
if command -v npm >/dev/null 2>&1; then
  [ -f apps/stacker/.env ] || cp apps/stacker/.env.example apps/stacker/.env
  if [ -d apps/stacker/node_modules ]; then
    phase stacker-vitest apps/stacker npm run test:unit
  else
    printf '\n===== apps/stacker/node_modules absent; running npm ci\n'
    if (cd apps/stacker && npm ci); then
      phase stacker-vitest apps/stacker npm run test:unit
    else
      RAN=$((RAN + 1))
      printf '===== FAIL stacker-npm-ci\n'
      FAILED+=("stacker-npm-ci  (apps/stacker: npm ci)")
    fi
  fi
else
  skip stacker-vitest "npm not on PATH"
fi

# --- summary -----------------------------------------------------------------
printf '\n===== %s summary\n' "$SELF"
for entry in ${SKIPPED[@]+"${SKIPPED[@]}"}; do
  printf 'SKIP  %s\n' "$entry"
done
if [ "${#FAILED[@]}" -eq 0 ]; then
  printf 'PASS  %d phase(s)\n' "$RAN"
  exit 0
fi
for entry in ${FAILED[@]+"${FAILED[@]}"}; do
  printf 'FAIL  %s\n' "$entry"
done
printf '%s: %d of %d phase(s) failed\n' "$SELF" "${#FAILED[@]}" "$RAN" >&2
exit 1
