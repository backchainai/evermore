#!/usr/bin/env bash
#
# Weekly Adopt-a-Pet report: pull per-pet stats, then rebuild the dashboard,
# in the correct order and from the correct directory. This is the single
# command to run each week.
#
# One-time setup (installs the Playwright Chromium binary):
#     uv run --with playwright playwright install chromium
#
# Usage (from anywhere):
#     adoption-profiles/analytics/run_weekly.sh
#
# Credentials come from adoption-profiles/.env (gitignored). Run this script
# with no .env present and it prints a fill-in-the-blanks template. Environment
# variables already set in the shell win over .env, so a one-off override still
# works:
#     AAP_USER='...' AAP_PASS='...' adoption-profiles/analytics/run_weekly.sh
#
# Extra flags are forwarded to the extractor, e.g.:
#     run_weekly.sh --headed                 # watch the browser
#     run_weekly.sh --as-of 2026-07-22       # label a specific pull date
#     run_weekly.sh --allow-count-swing      # accept a large roster change
#
set -euo pipefail

# Resolve to adoption-profiles/ regardless of where this is invoked from.
cd "$(dirname "$0")/.."

ENV_FILE="$PWD/.env"

# Load .env without letting it clobber anything already exported in the shell.
# `set -a` exports every assignment the file makes; the pre-pass records which
# vars were already set so those are restored afterward.
if [[ -f "$ENV_FILE" ]]; then
  _preset_user="${AAP_USER:-}"
  _preset_pass="${AAP_PASS:-}"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  [[ -n "$_preset_user" ]] && AAP_USER="$_preset_user"
  [[ -n "$_preset_pass" ]] && AAP_PASS="$_preset_pass"
  unset _preset_user _preset_pass
fi

if [[ -z "${AAP_USER:-}" || -z "${AAP_PASS:-}" ]]; then
  echo "error: no Adopt-a-Pet credentials found." >&2
  echo >&2
  echo "Create $ENV_FILE with:" >&2
  echo >&2
  cat >&2 <<'TEMPLATE'
    # Adopt-a-Pet shelter login. Use SINGLE quotes: passwords often contain
    # characters the shell would otherwise expand ($, !, backtick).
    AAP_USER='shelter-login-email'
    AAP_PASS='shelter-password'

    # Optional, for `deploy_dashboard.sh` only.
    #CF_PAGES_PROJECT='foha-dashboard'
    #CLOUDFLARE_ACCOUNT_ID=''
    #CLOUDFLARE_API_TOKEN=''
TEMPLATE
  echo >&2
  echo ".env is gitignored. The tool never prints or stores the password." >&2
  echo "(A credential-prefixed command can land in your shell history; .env avoids that.)" >&2
  exit 1
fi

echo "==> Pulling per-pet stats from Adopt-a-Pet"
uv run analytics/aap_pet_stats.py "$@"

echo "==> Rebuilding the dashboard from history.json"
uv run analytics/build_dashboard.py

if [[ -n "${CF_PAGES_PROJECT:-}" ]]; then
  echo "==> Publishing to Cloudflare Pages"
  analytics/deploy_dashboard.sh
else
  echo "==> Skipping publish (CF_PAGES_PROJECT unset in .env)"
fi

echo "==> Done. Open: analytics/FOHA Weekly Stats Dashboard.html"
