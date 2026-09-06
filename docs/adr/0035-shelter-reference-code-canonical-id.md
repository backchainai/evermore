# ADR 0035: The shelter reference code is the canonical animal identifier

- Status: accepted
- Date: 2026-09-06
- Deciders: project owner
- Relates to: ADR 0033 (read-only listing-verification service), ADR 0036 (engagement in Pet Data)

## Context

Three streams have to resolve to one animal: profile grades from the grader, listing engagement samples from the aggregator, and the Animal Record that Pet Data owns. Without one agreed identifier each stream carries its own key and nothing joins.

The owner's decision, in substance: the shelter reference code is the most reasonable UID to use across the board. Most aggregators carry it, it is the shelter system's key id, and it follows the animal for life (an animal adopted and then returned keeps the same primary reference code).

## Decision

The shelter reference code is the canonical animal identifier across Evermore, and it is the Animal Record's primary key.

Aggregator listing ids are attributes of engagement rows, never join keys. A listing id identifies one listing on one channel at one time; the reference code identifies the animal.

## Consequences

- Every per-animal table keys on the reference code: grader score records, engagement samples (ADR 0036), and the per-animal, per-channel listing-status table that ADR 0033 promises. ADR 0033 describes that table but names no identifier; this ADR supplies it.
- The Animal Record's primary key already is this column, so the decision ratifies the existing shape rather than changing it: `petdata_animals.id`, a `String` primary key (`services/petdata/alembic/versions/001_initial_schema.py:61`, `services/petdata/src/petdata/models/tables.py:63`), documented as `A-00000` shape at `packages/schema/src/evermore_schema/animal.py:73`.
- Distinct from it, and explicitly not the canonical identifier: `source_record_id`, the shelter system's own internal record id (`services/petdata/src/petdata/modules/api/parser.py:68` maps the source system's `id` field into it). On `petdata_animals` that column is nullable with no index and no unique constraint (`001_initial_schema.py:73`, `tables.py:76`), unlike the same-named column on notes and walk records, which is `unique=True`.

### Open question: whether the printed code is padded

The animal schema documents the id as an `A-00000` shape (`packages/schema/src/evermore_schema/animal.py:73`). A live read of the aggregator's stats report on 2026-09-06 found the same code printed as a plain unpadded integer on 96 of 96 rows: three to five digits, range 532 to 56205, unique per row.

Whether the shelter system emits the code padded or prefixed is open and unanswered. Both branches carry work:

- If it does emit a padded or prefixed form, a canonical normalization is required on both sides (ingest and engagement) before any join is relied on.
- If it does not, the `A-00000` comment in the schema is stale and should be corrected.

This has to be settled by reading a real shelter-system extract, not inferred from how the aggregator renders the value. Until it is settled, no code should assume either form.

### Open question: nothing populates the identifier yet

No production path writes an Animal Record today. `parse_animal_response` maps the reference code into `Animal.id` (`services/petdata/src/petdata/modules/api/parser.py:68`) and is exported from `petdata.modules.api`, but its only callers in the repo are unit tests, and its field mapping carries an in-code warning that the field names are placeholders pending verification against the real API (`parser.py:64`). Any join that depends on the canonical identifier therefore waits on ingest landing.

## Alternatives considered

- **The aggregator listing id as the canonical key.** Rejected: it is channel-scoped, it changes when a listing is recreated (for example when a returned animal is relisted), and it does not exist for an animal that is not yet listed.
- **An Evermore-issued surrogate key with the reference code as an attribute.** Rejected for now: it would insert a resolution table between every external stream and the Animal Record, and both external streams (the shelter system and the aggregator) already carry the reference code. Multi-shelter collisions, the usual reason to reach for a surrogate, are already handled by tenancy: `petdata_animals` carries `tenant_id` (`001_initial_schema.py:87`).
- **`source_record_id`, the shelter system's internal record id.** Rejected: the aggregators do not carry it, so it cannot join engagement to the Animal Record.
