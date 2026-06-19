## Project Overview

petdata is a Python application that extracts animal data from an Adalo-based shelter management system (SMS), stores it in a local SQLite database, and will eventually generate optimized adoption profiles using time-decay behavioral analysis and LLM synthesis.

This prompt covers Phase 1: Data extraction and storage design.

---

## Your Mission

Reverse engineer the shelter management system's web application to understand its data structures, API endpoints, and authentication patterns. Use these findings to design a data extraction system and SQLite schema that captures all relevant animal information.

---

## What This Application Will Do (Phase 1)

### Data Extraction
- Authenticate with the Adalo backend using JWT tokens
- Safely Pull complete animal records from the Adalo database (use safe adjustable retrieval rates to not overwhelm servers or API rate limits)
- Extract volunteer notes including: volunteer name, date/time, note text, and star ratings per behavioral category
- Extract staff behavioral assessments
- Extract kennel card information
- Handle incremental sync (fetch only updated records on subsequent runs)

### Data Storage
- Store all extracted data in SQLite
- Preserve full history of behavioral ratings and notes (required for time-decay analysis in Phase 2)
- Track data lineage (when records were synced, from which source)
- Design schema to be shelter-agnostic where practical (shelter-specific field mappings can be configuration rather than hardcoded)

---

## Required Investigation

### 1. Adalo API Structure

You have access to a JWT authenticated chrome browser session via the . Use browser DevTools (Network tab) to investigate:

**Authentication Pattern**
- How does the application obtain and refresh JWT tokens?
- What is the token lifetime?
- What headers are required for authenticated requests?
- Is there a refresh token mechanism, or does session expiry require re-authentication?

**API Endpoints**
- What is the base URL pattern for Adalo API calls?
- How are collection (table) IDs structured?
- What endpoints are called when viewing an animal's profile?
- What endpoints are called when viewing volunteer notes?
- What endpoints are called when viewing the animal list/grid?

**Query Patterns**
- How does the app filter, sort, and paginate data?
- What query parameter syntax does Adalo use?
- Are there any batch/bulk fetch capabilities?
- How are related records fetched (e.g., animal -> notes relationship)?

### 2. Data Model Discovery

Map the complete data model by observing API responses:

**Core Entities**
- What fields exist on the animal/dog record?
- What constitutes a "kennel card" and how is it structured?
- How are volunteer notes stored (separate collection or embedded)?
- How are behavioral ratings stored and categorized?

**Relationships**
- How are animals linked to their notes/ratings?
- Are there volunteer/user records, and how do they relate to notes?
- Are there any lookup tables (breed lists, behavior categories, color categories)?

**Behavioral Categories**
- What specific behavioral categories are tracked (jumpy, mouthy, leash manners, etc.)?
- What is the rating scale (1-5 stars, other)?
- Are categories consistent across all animals, or variable?

### 3. Data Completeness Check

Determine what data is accessible:

- Can you access historical notes/ratings, or only current state?
- Are there any fields visible in the UI but not returned in API responses?
- Are there any access restrictions on certain record types?
- Is there audit/timestamp data on records (created_at, updated_at)?

---

## Deliverables

After investigation, produce:

### 1. API Documentation
A summary of discovered endpoints, authentication requirements, and query patterns. Include example requests and responses.

### 2. Entity-Relationship Diagram
Visual or textual representation of how Adalo structures the data: entities, their fields, and relationships.

### 3. SQLite Schema Design
Proposed table structure that:
- Captures all relevant animal data
- Preserves complete rating/note history with timestamps (required for decay calculations)
- Supports incremental sync (track what's been fetched and when)
- Uses a normalization level appropriate for the query patterns we'll need
- Includes indexes for time-based queries (decay algorithm will query ratings by animal + date)

### 4. Data Extraction Strategy
Recommended approach for:
- Initial full sync
- Incremental updates
- Handling API rate limits or pagination
- Error recovery and retry logic

### 5. Open Questions
Any ambiguities discovered that require human decision-making before implementation.

---

## Technical Context

**Authentication**: You will be provided a JWT token from an authenticated browser session. Design the extraction to work with provided tokens initially; token refresh automation can be addressed later.

**Target Database**: SQLite only for Phase 1. Schema should be straightforward to migrate to PostgreSQL later if needed, but don't over-engineer for that now.

**Shelter Agnosticism**: While building for one shelter initially, prefer configuration over hardcoding where it doesn't add complexity. Example: behavioral category names should come from the data or config, not be hardcoded constants.

**Future Phases** (context only, don't design these yet):
- Phase 2: Time-decay algorithm using natural exponential decay (Euler's number), with the most recent 3 months weighted heavily before decay applies
- Phase 3: LLM-generated adoption profiles based on research guidelines

---

## How to Investigate

1. Open the shelter management system in Chrome with DevTools Network tab active
2. Navigate through the application: view animal lists, individual animal profiles, volunteer notes sections
3. Observe XHR/Fetch requests to identify API patterns
4. Document request/response structures
5. Look for collection IDs, field names, relationship patterns
6. Test query parameters if the API structure becomes clear

If you encounter authentication issues or need a fresh JWT token, ask.

---

## Constraints

- Do not write implementation code yet; focus on research and design
- Do not design the decay algorithm or profile generation; those are later phases
- Do not add infrastructure beyond SQLite (no Redis, no job queues, no vector databases)
- Prefer simple, obvious solutions over clever ones

---

## Success Criteria

Phase 1 is complete when:
1. We understand exactly what data exists in Adalo and how to fetch it
2. We have a SQLite schema that can store that data with full history
3. We have a clear extraction strategy documented
4. We're confident implementation can proceed without further investigation
