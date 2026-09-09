#!/usr/bin/env bash
# scripts/gate-lint.sh -- the repo's tracked `lint` gate.
#
# Every command here is the command .github/workflows/ci.yml runs, in CI's
# order, for the three path-filtered jobs (petdata, retriever, stacker). The
# modules CI has no job for (services/grader, packages/auth, packages/llm,
# packages/schema) run the quality gates their own CLAUDE.md / pyproject.toml
# declare. Where a module's CLAUDE.md and ci.yml disagree, CI wins:
#   - petdata: CI runs `uv run mypy src/`, its CLAUDE.md suggests
#     `uv run python -m mypy src/` for local runs. CI's form is used here.
#   - petdata: CI runs `uvx bandit`, its CLAUDE.md says `uv run bandit`
#     (bandit is not a petdata dev dependency, so only `uvx` resolves).
#   - retriever: its CLAUDE.md's "all quality checks" line uses
#     `ruff check --fix` and a bare `ruff format`. A lint gate must never
#     modify the tree, so this script uses CI's check/verify forms only
#     (`ruff check`, `ruff format --check`).
#
# CI-delegated (not run here, by design -- see .daedalus config `ci_delegated`):
#   - `npm run gen:types` + `git diff --exit-code` (stacker's OpenAPI contract
#     drift check): it rewrites tracked types.generated.ts files, so it is a
#     mutating check and cannot live in a lint gate.
#   - `npm run build` (stacker production build) and the container-build job:
#     builds, not lint.
#   - codeql.yml and mutation.yml: separate workflows, neither gates a merge
#     locally.
#
# Toolchain: `uv` is a hard prerequisite (it is the gate prerequisite Daedalus
# documents, and every Python phase runs through it), so a missing `uv` fails
# the gate up front rather than skipping half the repo silently. `npm` is not:
# a machine with no Node skips the stacker phase with a loud SKIP line. A
# missing apps/stacker/node_modules or .env is installed/created rather than
# skipped -- both are gitignored, both are exactly what ci.yml's stacker job
# does before `npm run check`, and `svelte-kit sync` cannot generate
# $env/static/public types without .env.
#
# Every phase runs; failures are collected and reported in one summary at the
# end (the Daedalus gate log keeps only a tail, so one summary listing every
# failed phase is more useful in a 7-module tree than a fail-fast first
# error). `uv run --frozen` everywhere: the gate resolves nothing and never
# rewrites a tracked uv.lock.
#
# Run with: bash scripts/gate-lint.sh

set -euo pipefail

SELF="scripts/gate-lint.sh"

# Repo root from this script's own location, not $PWD: the gate is invoked
# under `sh -c` by hooks/scripts/daedalus-gates.sh and by hand from any
# subdirectory.
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

FAILED=()
SKIPPED=()
RAN=0

# phase <label> <dir> <cmd...> -- run one module's check from <dir>, record a
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
phase retriever-ruff-check services/retriever uv run --frozen ruff check src/ tests/
phase retriever-ruff-format services/retriever uv run --frozen ruff format --check src/ tests/
phase retriever-mypy services/retriever uv run --frozen python -m mypy src/ --strict

# --- services/petdata (ci.yml `petdata` job) ---------------------------------
# Dev tooling is an optional extra, so every phase carries `--extra dev`
# (ci.yml runs `uv sync --extra dev` once up front).
phase petdata-ruff-format services/petdata uv run --frozen --extra dev ruff format --check src/ tests/
phase petdata-ruff-check services/petdata uv run --frozen --extra dev ruff check src/ tests/
phase petdata-mypy services/petdata uv run --frozen --extra dev mypy src/
phase petdata-bandit services/petdata uvx bandit -r src/ -q

# --- services/grader (no CI job; services/grader/CLAUDE.md quality gates) ----
phase grader-ruff-format services/grader uv run --frozen --extra dev ruff format --check src/ tests/
phase grader-ruff-check services/grader uv run --frozen --extra dev ruff check src/ tests/
phase grader-mypy services/grader uv run --frozen --extra dev mypy src/
phase grader-bandit services/grader uvx bandit -r src/ -q

# --- packages/* (no CI job; ruff + mypy strict per each pyproject.toml) ------
for pkg in auth llm schema; do
  phase "$pkg-ruff-format" "packages/$pkg" uv run --frozen --extra dev ruff format --check src/ tests/
  phase "$pkg-ruff-check" "packages/$pkg" uv run --frozen --extra dev ruff check src/ tests/
  phase "$pkg-mypy" "packages/$pkg" uv run --frozen --extra dev mypy src/
done

# --- apps/stacker (ci.yml `stacker` job) -------------------------------------
if command -v npm >/dev/null 2>&1; then
  [ -f apps/stacker/.env ] || cp apps/stacker/.env.example apps/stacker/.env
  if [ -d apps/stacker/node_modules ]; then
    phase stacker-check apps/stacker npm run check
  else
    printf '\n===== apps/stacker/node_modules absent; running npm ci\n'
    if (cd apps/stacker && npm ci); then
      phase stacker-check apps/stacker npm run check
    else
      RAN=$((RAN + 1))
      printf '===== FAIL stacker-npm-ci\n'
      FAILED+=("stacker-npm-ci  (apps/stacker: npm ci)")
    fi
  fi
else
  skip stacker-check "npm not on PATH"
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
