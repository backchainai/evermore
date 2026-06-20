## Project Overview

> **Historical document.** This is the original Phase 1 brief that scoped data
> extraction and storage. The shipped implementation stores data in Supabase
> Postgres (not SQLite) via async SQLAlchemy and Alembic; see
> [architecture.md](architecture.md) for the current design. The text below is
> preserved as the original conception.

petdata is a Python application that extracts animal data from a shelter's
Shelter Management System (SMS), stores it, and will eventually generate
optimized adoption profiles using time-decay behavioral analysis and LLM
synthesis.

This brief covers Phase 1: data extraction and storage design.

---

## Mission

Understand the SMS web application's data structures, API endpoints, and
authentication patterns. Use these findings to design a data extraction system
and a storage schema that captures all relevant animal information.

---

## What This Application Will Do (Phase 1)

### Data extraction
- Authenticate with the SMS backend
- Safely pull complete animal records (use adjustable retrieval rates so as not to overwhelm servers or API rate limits)
- Extract volunteer notes including: volunteer name, date/time, note text, and ratings per behavioral category
- Extract staff behavioral assessments
- Extract kennel card information
- Handle incremental sync (fetch only updated records on subsequent runs)

### Data storage
- Store all extracted data durably
- Preserve full history of behavioral ratings and notes (required for time-decay analysis in Phase 2)
- Track data lineage (when records were synced, from which source)
- Design the schema to be shelter-agnostic where practical (shelter-specific field mappings live in configuration rather than hardcoded constants)

---

## Required Investigation

### 1. SMS API structure

Using an authenticated browser session and DevTools (Network tab), investigate:

**Authentication pattern**
- How does the application obtain and refresh session credentials?
- What is the session lifetime?
- What headers are required for authenticated requests?
- Does session expiry require re-authentication?

**API endpoints**
- What is the base URL pattern for SMS API calls?
- How are collection (table) identifiers structured?
- What endpoints are called when viewing an animal's profile, volunteer notes, and the animal list?

**Query patterns**
- How does the app filter, sort, and paginate data?
- What query parameter syntax does the SMS use?
- Are there batch/bulk fetch capabilities?
- How are related records fetched (e.g. animal -> notes)?

### 2. Data model discovery

Map the complete data model by observing API responses:

**Core entities**
- What fields exist on the animal record?
- What constitutes a "kennel card" and how is it structured?
- How are volunteer notes stored (separate collection or embedded)?
- How are behavioral ratings stored and categorized?

**Relationships**
- How are animals linked to their notes/ratings?
- Are there volunteer/user records, and how do they relate to notes?
- Are there lookup tables (breed lists, behavior categories, color categories)?

**Behavioral categories**
- What specific behavioral categories are tracked (jumpy, mouthy, leash manners, etc.)?
- What is the rating scale?
- Are categories consistent across all animals, or variable?

### 3. Data completeness check

- Can historical notes/ratings be accessed, or only current state?
- Are there fields visible in the UI but not returned in API responses?
- Are there access restrictions on certain record types?
- Is there audit/timestamp data on records (created_at, updated_at)?

---

## Deliverables

After investigation, produce:

1. **API documentation:** discovered endpoints, authentication requirements, and query patterns, with example requests and responses.
2. **Entity-relationship description:** how the SMS structures the data: entities, fields, and relationships.
3. **Schema design:** a table structure that captures all relevant animal data, preserves complete rating/note history with timestamps (required for decay calculations), supports incremental sync, and includes indexes for time-based queries.
4. **Data extraction strategy:** initial full sync, incremental updates, rate-limit and pagination handling, error recovery and retry logic.
5. **Open questions:** ambiguities requiring human decision before implementation.

---

## Technical Context

**Authentication:** design the extraction to work with provided session
credentials initially; credential-refresh automation can be addressed later.

**Storage:** Phase 1 captured data in a simple local store, with the schema
designed to be straightforward to move to Postgres. (The shipped
implementation now runs on Supabase Postgres; see the banner above.)

**Shelter agnosticism:** while building for one shelter initially, prefer
configuration over hardcoding where it does not add complexity. Example:
behavioral category names should come from the data or config, not hardcoded
constants.

**Future phases** (context only):
- Phase 2: time-decay algorithm using exponential decay, with the most recent 3 months weighted heavily before decay applies.
- Phase 3: LLM-generated adoption profiles based on research guidelines.

---

## Constraints (as briefed)

- Focus on research and design before implementation code
- Do not design the decay algorithm or profile generation; those are later phases
- Keep infrastructure minimal for Phase 1 (no Redis, no job queues)
- Prefer simple, obvious solutions over clever ones
