# ADR 0038: Collect listing engagement with a scheduled Cloudflare Worker

- Status: accepted
- Date: 2026-09-06
- Deciders: project owner
- Relates to: ADR 0029 (all-Cloudflare hosting), ADR 0035 (canonical animal identifier), ADR 0036 (engagement in Pet Data), ADR 0037 (hosted-only execution)

The owner chose this design on 2026-09-07, after being shown the alternative of a saved third-party scraper profile that a human re-authenticates by hand. One prerequisite is still his to arrange (see "What this decision still needs").

## Context

Evermore needs weekly listing engagement per animal (search impressions, detail views, click-through rate) to measure whether better cards produce more adopter interest.

The aggregator exposes no API and no CSV export that returns engagement data. Its pet-list API and its shelter export both return listings only, which Evermore already has. The only source of engagement figures is the authenticated stats report page.

ADR 0037 rules out the existing workstation collector, so a hosted replacement is needed. The owner set two requirements on any such collector: the credential is stored securely as an environment variable in the hosted environment, and tests prove the collector issues no PUTs or POSTs beyond what login requires.

## Decision

A Cloudflare Worker on a weekly Cron Trigger, making two `fetch` calls.

- **Fetch 1:** POST the login form to the aggregator's login path.
- **Fetch 2:** carry the returned session cookie into the report request, then parse the server-rendered table deterministically.
- **Credentials:** set with `wrangler secret put`, read at runtime as `env.KEY`. Never in `wrangler.jsonc`, never in the repo.
- **URL allowlist:** the collector may request only the login path, the report path, and the report path's `?current_page=N` form. Any other URL is a bug and fails the request.
- **Write discipline, enforced by tests:** exactly one POST is permitted (the login), and every other non-GET is rejected.
- **Storage:** engagement rows land in the Pet Data database (ADR 0036), keyed by the canonical animal identifier (ADR 0035).

Two fetches and an HTML parse means no headless browser, no container, and no Playwright dependency in the hosted path.

## Evidence

Measured on 2026-09-06 against the live pages. These are observations, not guarantees about future page structure.

**The login page needs no browser.** One form with three inputs, zero hidden inputs, no CSRF token, no captcha, no bot-defence vendor, and no JavaScript touching the form. A plain form POST is sufficient.

**The report is plain server-rendered HTML.** 96 data rows over four pages, at 25, 25, 25 and 21 rows.

**Two data invariants held across the full sample and should become ingest gates.**

1. The printed click-through rate equals `100 * (seven-day detail views / seven-day search impressions)` on 96 of 96 rows. Worst observed error 0.0495 percentage points, consistent with display rounding only.
2. Each all-time counter is at least its thirty-day counter, which is at least its seven-day counter: 768 comparisons, zero violations.

**Keep the existing empty-parse abort gate.** A failed login renders as an empty parse, so a collector that treats zero parsed rows as a valid result would silently record zero animals. It must fail loudly instead.

## Consequences

- The engagement pipeline becomes hosted and unattended, satisfying ADR 0037.
- The collector depends on the aggregator's HTML structure. A page redesign breaks it, which is why the invariants above and the empty-parse abort are gates rather than nice-to-haves: the failure has to be loud and weekly, not silent.
- Scraping an authenticated report page is a per-channel fallback, consistent with ADR 0033's "official APIs first, scrape as a fallback" rule. Here there is no API to prefer.
- A new deployable unit joins the Cloudflare footprint (a Worker with a Cron Trigger), alongside the existing service Workers.
- The aggregator credential becomes a production secret with a rotation obligation. No rotation procedure is defined yet.

## Alternatives considered

- **A Cloudflare Container running the existing Playwright collector.** Rejected: the container documentation never mentions Playwright or headless Chromium, so support is unestablished. It would also carry a browser runtime to do what two fetches do.
- **Browser Run.** Rejected: it supports Playwright, but using it requires rewriting the existing Python collector in TypeScript for no gain over two fetches, given the login form needs no browser at all (see Evidence).
- **A third-party scraping service with a saved authenticated profile.** Put to the owner directly on 2026-09-07, side by side with the Worker design above, and declined. Four things counted against it: the saved browser state only persists when a session ends, so a run that does not close cleanly saves nothing; profile retention is undocumented, so the profile may not survive the week between collections; refreshing it needs a human to log in by hand, which puts back the manual step ADR 0037 removes; and the credential lives with the third party rather than with us. Measured behavior counted against it too: its scrape endpoint silently ignores a saved profile and returns HTTP 200 with a success flag while serving the login page, and a success response that actually delivers the login page is an unsafe failure mode for an unattended collector. The service remains useful for ad-hoc manual verification of that page and is not part of the production design.
- **Keep the workstation collector.** Rejected by ADR 0037.

## What this decision still needs

One prerequisite is left, and it is the owner's to arrange:

1. The aggregator credentials installed as Worker secrets.

Worker egress is not a prerequisite. A deployed Cloudflare Worker fetches public hosts directly; the network restriction that made egress look like a blocker applies to the development environment this work was measured from, not to a deployed Worker.

Until the credentials are installed, the engagement pipeline has no hosted path and no data is being collected.
