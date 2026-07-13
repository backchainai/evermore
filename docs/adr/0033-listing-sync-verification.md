# ADR 0033: Read-only listing-verification service (`listings`)

- Status: proposed
- Date: 2026-07-13
- Deciders: project owner

## Context

Kennel-card content is the top of the adoption funnel. The publication chain (per `docs/evermore-vision-and-architecture.md`): a volunteer writes the kennel card, it is entered in the SMS, the SMS publishes it to the public adoption-listing sites, and that text becomes the animal's public listing on the sites adopters search.

Evermore's living source of truth for the card is the **Composition** (versioned, human-edited). The grader (epic-tracked separately) scores the Composition. Nothing yet verifies that what is actually live on the public sites matches the current Composition. There are two drift points:

- **Composition -> SMS:** the manual "enter it in the SMS" step, the drift-prone one.
- **SMS -> public sites:** syndication lag or failure.

The vision doc names a future "Social Distribution & Analytics" module whose scope includes "content QA (errors, omissions, stale listings)." This ADR builds the read-only stale-listing slice of that concern, now, as its own service.

## Decision

Add a new service `services/listings/` (env prefix `LISTINGS_`, FastAPI title "Listing Compliance"), conforming to the tech-stack standard (ADR 0024) and mirroring the `services/petdata/` and `services/grader/` shape. Standalone, a peer to the other services.

- **Read-only.** The service verifies and reports. It does not publish, push, or write back to the SMS or the channels. Publishing is an explicit future module (recorded here as a non-goal).
- **Source of truth is the current Composition.** Compliance means the live public listing matches the current Composition's rendered kennel-card text (normalized match, tolerant of whitespace and HTML) plus photo presence, tracked against a Composition version stamp so the report can say "listing shows v3, current is v5."
- **Both drift points are checked.** Composition -> SMS and SMS -> channel are separate hops with separate status columns.
- **Read via official APIs first, scrape as a fallback.** Petfinder API v2 and the Adopt-a-Pet feed/API for the public-listing reads. Where a shelter's SMS exposes an API, the SMS-side read is performed by Pet Data (which owns SMS extraction); the listings service consumes Pet Data's extracted current card rather than building a second SMS connector. Scraping is a per-channel fallback only where no API exists. This outbound verification of destination channels is distinct from, and not a violation of, the platform rule that Pet Data owns inbound animal-data extraction.
- **Persistence and tenancy:** Supabase Postgres, SQLAlchemy async + Alembic (ADR 0025 pattern), org-scoped via RLS (ADR 0024). Sync-status results are an append-only time series so drift history stays queryable.
- **Surface:** a typed, authed, org-scoped API and a sync-status dashboard route in `apps/stacker` on the shared design-system tokens (ADR 0031). No LLM runs in this service, so there is no AI Gateway or Promptfoo dependency; contract and Schemathesis tests stand in.

## Consequences

- External dependencies gate part of the work: Petfinder API v2 credentials, Adopt-a-Pet feed/API access, and (for the Composition -> SMS hop) the shelter's SMS API access via Pet Data. Acquiring these is a prerequisite for the channel-adapter tickets; the scaffold, data model, and compliance engine proceed without them.
- Reusing Pet Data for SMS reads keeps the service thin and avoids a second extraction path.
- Read-only keeps the blast radius low: the platform cannot corrupt a live listing.
- The dashboard converts an invisible manual-sync failure mode into an observable per-animal, per-channel "in sync / stale / missing" table for shelter staff.

## Alternatives considered

- **Fold into the grader.** Rejected: the grader scores copy quality against research; this verifies publication fidelity across external channels. Different inputs, different integrations, different failure model.
- **A publisher that pushes the card to the SMS or channels.** Deferred: higher risk (mutating live listings), and the read-only verifier answers "are we in sync" without it. Publishing is a future module; this ADR records the non-goal.
- **Scrape-first.** Rejected: official APIs (Petfinder v2, Adopt-a-Pet) are more stable and lower-maintenance; scraping is a fallback only.
- **Build the full "Social Distribution & Analytics" module** (scheduling, engagement analytics, third-party campaign integrations). Deferred: out of scope now; this builds only the stale-listing QA slice.
