# Phase 1: Data Extraction and Storage Design

## Summary

Extract animal data from a shelter's Shelter Management System (SMS) and store it in Postgres with full behavioral-rating history, so Phase 2 can run time-decay analysis over the observations.

The SMS is treated as a generic upstream source. Connection details (base URL, table identifiers, session credentials) are supplied through `PETDATA_` environment variables and never hard-coded; see `.env.example`.

---

## Source SMS API

The reference SMS exposes a table-oriented REST API.

**Base URL pattern** (configured via `PETDATA_ADALO_BASE_URL`):
```
https://<sms-host>/databases/{database_id}/tables/{table_id}
```

**Tables consumed** (table identifiers via `PETDATA_ADALO_TABLE_*`):

| Logical table | Purpose |
|---------------|---------|
| Animals | Dog/cat records with basic info |
| Volunteer Notes | Notes with behavioral ratings |
| Walk Records | Walk check-in/out records |

**Query parameters:**
- `column_filter`: Base64-encoded JSON filter array
- `sort`: column id with `-` prefix for descending (e.g. `-created_at`)
- `limit`: pagination limit
- `include`: relationship includes
- `imageMeta=true`, `evaluateBindings=true`: standard flags

**Authentication:** cookie-based session authentication. Session cookies are captured from an authenticated browser session and supplied via `PETDATA_COOKIES`.

---

## Data Model

Field examples below are illustrative placeholders, not real records.

### Animal record
| Field | Example | Notes |
|-------|---------|-------|
| ID | A-00000 | Unique identifier |
| Name | (name) | Display name |
| AKA | (alt name) | Alternate name |
| Breed | (breed) | Breed string |
| Weight | 40 lbs | Numeric with unit |
| Birth Date | 2024-06-24 | Date |
| Intake Date | 2025-12-07 | Date |
| Location | (kennel) | Kennel location |
| Color Category | Green/Yellow/Orange/Senior/Designated | Status tier |
| Behavior Mod Tags | (tag, tag) | List, stored as JSONB |
| In Kennel Status | Boolean | Current presence |
| Foster Care | Boolean | Foster status |
| Photo URL | (url) | Profile image |

### Volunteer note record
| Field | Example | Notes |
|-------|---------|-------|
| Animal ID | A-00000 | Foreign key |
| Volunteer Name | (volunteer) | String |
| Date/Time | 2025-12-23T17:37:00 | Timestamp, key for time-decay |
| Note Text | (free text) | Observation |
| Strong on Leash | 0-5 | Rating |
| Leash Reactivity | 0-5 | Rating |
| Shy / Fearful | 0-5 | Rating |
| Jumpy / Mouthy | 0-5 | Rating |

### Kennel card (structured)
About text, "how am I with dogs/cats/kids" (status + explanation), commands known, housebreaking/crating status, things I like, things I dislike, public profile URL.

### Staff assessment
Structured tags (cat-test complete, good with dogs, good with kids, etc.) plus free-form notes about incidents and observations.

---

## Storage (Postgres)

Phase 1 stores extracted data in Supabase Postgres, accessed through async SQLAlchemy. The schema is owned by Alembic.

- The ORM tables in `src/petdata/models/tables.py` are the canonical definition.
- The initial migration `alembic/versions/001_initial_schema.py` is the schema source of truth; apply it with `uv run alembic upgrade head`.

Schema highlights:

- Every table carries the `petdata_` prefix and a `tenant_id` column for row-level security.
- `petdata_animals` is the parent; child tables (`petdata_volunteer_notes`, `petdata_walk_records`, `petdata_staff_assessments`, `petdata_kennel_cards`, `petdata_animal_images`) reference it with `ON DELETE CASCADE`.
- `petdata_volunteer_notes` carries the decay-critical indexes `idx_volunteer_notes_animal_date` (per-animal recency) and `idx_volunteer_notes_date` (global recency), plus `CHECK` constraints keeping each rating in 0..5.
- List fields (behavior-mod tags, assessment tags) are JSONB; timestamps are timezone-aware.
- `petdata_sync_log` records each extraction run (full/incremental, counts, status).

A `last_synced_at` column on the entity tables and a source record id (for deduplication) support incremental sync.

---

## Data Extraction Strategy

### Initial full sync

1. Authenticate by supplying captured session cookies.
2. Paginate through the animals table.
3. For each animal, fetch volunteer notes (filtered by animal id), walk records, and parse the kennel card from the animal record.
4. Record `last_synced_at` on each stored record.

### Incremental updates

1. Query by `updated_at` when the SMS provides it.
2. Otherwise, compare fetched records against the stored source record id.
3. Notes are append-only: new notes do not modify existing ones.

### Rate limiting

- Default delay 500ms between requests (`PETDATA_REQUEST_DELAY_MS`).
- Exponential backoff on 429/5xx (`PETDATA_RETRY_*`, `PETDATA_API_TIMEOUT_SECONDS`).

### Error recovery

- The sync log records progress so a run can resume after a failure.
- Commit in batches to bound data loss.

---

## Implementation

The extraction client lives in `src/petdata/modules/api/` (`auth.py`, `client.py`, `parser.py`); storage in `src/petdata/models/` (ORM) and `src/petdata/modules/db/` (Pydantic domain models, async repository); the API surface in `src/petdata/modules/web/`.

Verification for an extraction run: confirm API connectivity with a single animal fetch, run a small-limit sync first, verify note counts against the SMS UI, and run the sync twice to confirm no duplicate records.

---

## Related Documents

- [Architecture](architecture.md) - system design and patterns
- [Development Standards](development-standards.md) - git, testing, quality
- [ADR-002: Mutable Models](../adr/002-mutable-pydantic-models.md)
