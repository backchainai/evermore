#!/usr/bin/env bash
#
# Publish the built dashboard to Cloudflare Pages by direct upload.
#
# Direct upload (rather than the Pages git integration) is deliberate: this
# repository is ~3 GB and holds FOHA staff personal contact details, so it must
# not be pushed to GitHub. Only the single rendered HTML file leaves the
# machine.
#
# Called automatically by run_weekly.sh when CF_PAGES_PROJECT is set in .env.
# Safe to run on its own to republish without re-pulling stats:
#     adoption-profiles/analytics/deploy_dashboard.sh
#
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="$PWD/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

DASHBOARD="analytics/FOHA Weekly Stats Dashboard.html"
DIST="analytics/dist"

# The dashboard is served at a subpath, not at the root of the host, so
# foha.backchain.app can carry other FOHA pages later without moving this one.
# Override in .env if the path ever changes.
SITE_PATH="${CF_PAGES_PATH:-profile-engagement}"

if [[ -z "${CF_PAGES_PROJECT:-}" ]]; then
  echo "error: CF_PAGES_PROJECT is not set. Add it to $ENV_FILE." >&2
  exit 1
fi

if [[ ! -f "$DASHBOARD" ]]; then
  echo "error: $DASHBOARD not found. Run build_dashboard.py first." >&2
  exit 1
fi

# Stage a clean upload directory. The dashboard filename contains spaces and is
# not a valid entry point, so it is copied to index.html under the site path.
# Everything the page needs is already embedded in that one file (no CSS, JS, or
# data fetches), so the whole site is a single document.
rm -rf "$DIST"
mkdir -p "$DIST/$SITE_PATH"
cp "$DASHBOARD" "$DIST/$SITE_PATH/index.html"

# Defense in depth. Cloudflare Access is the actual control; these headers keep
# the page out of search indexes and block framing even if a request reaches it.
cat > "$DIST/_headers" <<'HEADERS'
/*
  X-Robots-Tag: noindex, nofollow
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
HEADERS

printf 'User-agent: *\nDisallow: /\n' > "$DIST/robots.txt"

echo "[deploy] staged $DIST ($(du -h "$DIST/$SITE_PATH/index.html" | cut -f1) $SITE_PATH/index.html)"

# npx fetches wrangler on demand; no global install required.
# Auth comes from CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID in .env, or from
# a prior `npx wrangler login`.
npx --yes wrangler@latest pages deploy "$DIST" \
  --project-name "$CF_PAGES_PROJECT" \
  --branch main \
  --commit-dirty=true

echo "[deploy] published to project '$CF_PAGES_PROJECT' at /$SITE_PATH"
