# ADR 0036: Listing engagement data lives in the Pet Data service

- Status: accepted
- Date: 2026-09-06
- Deciders: project owner
- Relates to: ADR 0030 (three Supabase projects, one per service), ADR 0035 (canonical animal identifier), ADR 0038 (proposed engagement collector)

## Context

Weekly listing engagement samples (search impressions, detail views, click-through rate) are only interpretable per animal, alongside the card that produced them. So engagement rows have to join to the Animal Record, and Pet Data owns the Animal Record.

ADR 0030 (proposed) sets the data topology as three Supabase projects, one per service, with identity standalone. A new data domain therefore has to answer whether it earns a fourth project.

## Decision

Engagement lives in the Pet Data service's own database.

Pet Data already owns the Animal Record and needs the aggregator listing id field regardless, so engagement rows sit next to the record they describe, with no cross-project join. No fourth Supabase project is created for engagement, and ADR 0030 needs no amendment for it.

## Consequences

- Weekly engagement samples are stored as Pet Data rows keyed by the canonical animal identifier (ADR 0035), with the aggregator listing id as an attribute of the row rather than a join key.
- Pet Data's schema grows an engagement table and its Alembic history covers it. Nothing of the sort exists yet: `petdata_animals` has no listing id column, and there is no engagement table in `services/petdata/alembic/versions/`.
- The cross-service query cost of not colocating engagement with grades is accepted. Correlating "the grade went up and engagement went up" crosses a service boundary.
- **Open, and not decided here: where the profile grader's own score records live.** `services/grader` is currently a tech-stack scaffold with no data layer (its `CLAUDE.md` records the data layer as later work). Putting score records in Pet Data too would cut against ADR 0030's one-database-per-service rule; giving the grader its own database reopens the fourth-project question that this ADR declined for engagement. This ADR settles engagement only and leaves that question open.

## Alternatives considered

- **A fourth Supabase project for engagement.** Rejected: it would put engagement across a project boundary from the Animal Record it must join to, for a data domain amounting to a few counters per animal per week.
- **Engagement in the grader's database.** Rejected: engagement measures adopter behavior against a published listing, not a property of a grade, and the grader has no data layer yet. It would also still be a cross-project join to the Animal Record.
- **Engagement in the `listings` service proposed by ADR 0033.** Not taken: that service is scoped read-only to publication fidelity (is the live listing the current Composition), and it does not exist yet. Engagement is a time series about adopter behavior, not a sync check. If `listings` does land, its per-animal, per-channel status table and these engagement rows both key on the reference code (ADR 0035), which keeps a later move cheap.
