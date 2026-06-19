# Phase 1: Data Extraction and Storage Design

## Summary

Design and implement a data extraction system for an Adalo-based shelter management system (SMS), storing animal data in SQLite with full behavioral rating history for future time-decay analysis.

---

## API Investigation Findings

### Adalo Database API Structure

**Base URL Pattern:**
```
https://database-red.adalo.com/databases/{database_id}/tables/{table_id}
```

**Discovered Identifiers:**
- Database ID: `bjql6w9oy6hlarewbcr9fwh2i`
- App ID: `f6441ecb-77db-48f5-8f46-eab2faf6520d`

**Table IDs Identified:**
| Table | ID | Purpose |
|-------|-----|---------|
| Animals | `t_0sslo1men4fkuiap2eis82riv` | Dog/cat records with basic info |
| Volunteer Notes | `t_9yomkzwe9lsdlgwvkbwa9uoai` | Notes with behavioral ratings |
| Walk Records | `t_0cd59s41203wo2dbdr8bwtoa4` | Walk check-in/out records |

**Query Parameters:**
- `column_filter`: Base64-encoded JSON array `[[{"field":"column_id","value":"X","type":"=="}]]`
- `sort`: Column ID with `-` prefix for descending (e.g., `-created_at`)
- `limit`: Pagination limit (default 20)
- `include`: Relationship includes like `belongsTo~{column_id}`
- `imageMeta=true`, `evaluateBindings=true`: Standard flags

**Authentication:**
- Cookie-based session authentication
- Extract cookies from authenticated browser session
- No visible JWT tokens in localStorage/sessionStorage

---

## Data Model (Observed from UI)

### Animal Record
| Field | Example | Notes |
|-------|---------|-------|
| ID | A-55833 | Unique identifier |
| Name | Eros | Display name |
| AKA | Dame | Alternate name |
| Breed | Sheep Dog | Breed string |
| Weight | 43 lbs | Numeric with unit |
| Birth Date | 6/24/2024 | Date |
| Intake Date | 12/7/2025 | Date |
| Location | Line 5, 5H | Kennel location |
| Color Category | Green/Yellow/Orange/Senior/Designated | Status tier |
| Behavior Mod Tags | Shy, Jumpy and Mouthy, Touch Sensitivity | Comma-separated |
| In Kennel Status | Boolean | Current presence |
| Foster Care | Boolean | Foster status |
| Photo URL | Adalo imgix URL | Profile image |

### Volunteer Note Record
| Field | Example | Notes |
|-------|---------|-------|
| Animal ID | A-55833 | Foreign key |
| Volunteer Name | Chris Krough | String |
| Date/Time | 12/23/2025 5:37 PM | Timestamp |
| Note Text | "High energy and alert..." | Free text |
| Strong on Leash | 1-5 | Star rating |
| Leash Reactivity | 1-5 | Star rating |
| Shy / Fearful | 1-5 | Star rating |
| Jumpy / Mouthy | 1-5 | Star rating |

### Kennel Card Fields (Structured)
- About This Animal (bio text)
- How Am I With Dogs (status + explanation)
- How Am I With Cats (status + explanation)
- How Am I With Kids (status + explanation)
- Commands Known
- Housebreaking/Crating Status
- Things I Like
- Things I Dislike
- Public Profile URL (example.org/pet/{slug}/)

### Behavioral Staff Notes
- Structured tags: Cat Test Complete, Good with Dogs, Good with Kids, etc.
- Free-form notes about incidents/observations

---

## SQLite Schema Design

### Core Tables

```sql
-- Animals table
CREATE TABLE animals (
    id TEXT PRIMARY KEY,                    -- A-55833
    name TEXT NOT NULL,
    aka TEXT,
    breed TEXT,
    weight_lbs REAL,
    birth_date DATE,
    intake_date DATE,
    location TEXT,
    color_category TEXT,                    -- Green/Yellow/Orange/Senior/Designated
    behavior_mod_tags TEXT,                 -- JSON array
    is_in_kennel BOOLEAN,
    is_foster_care BOOLEAN,
    photo_url TEXT,
    public_profile_url TEXT,
    adalo_record_id TEXT,                   -- Original Adalo ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Kennel card structured data
CREATE TABLE kennel_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    about_text TEXT,
    dogs_compatibility TEXT,                -- Unknown/Good/Bad + explanation
    dogs_compatibility_notes TEXT,
    cats_compatibility TEXT,
    cats_compatibility_notes TEXT,
    kids_compatibility TEXT,
    kids_compatibility_notes TEXT,
    commands_known TEXT,
    housebreaking_status TEXT,
    things_likes TEXT,
    things_dislikes TEXT,
    last_synced_at TIMESTAMP,
    UNIQUE(animal_id)
);

-- Staff behavioral assessments
CREATE TABLE staff_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    assessment_tags TEXT,                   -- JSON array of tags
    notes TEXT,
    recorded_at TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Volunteer notes with ratings (CRITICAL for time-decay)
CREATE TABLE volunteer_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    adalo_record_id TEXT UNIQUE,            -- For deduplication
    volunteer_name TEXT NOT NULL,
    note_date TIMESTAMP NOT NULL,           -- Key for time-decay
    note_text TEXT,
    rating_strong_on_leash INTEGER CHECK (rating_strong_on_leash BETWEEN 0 AND 5),
    rating_leash_reactivity INTEGER CHECK (rating_leash_reactivity BETWEEN 0 AND 5),
    rating_shy_fearful INTEGER CHECK (rating_shy_fearful BETWEEN 0 AND 5),
    rating_jumpy_mouthy INTEGER CHECK (rating_jumpy_mouthy BETWEEN 0 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP
);

-- Walk records
CREATE TABLE walk_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    adalo_record_id TEXT UNIQUE,
    volunteer_name TEXT,
    out_time TIMESTAMP,
    in_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync tracking
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,                -- full/incremental
    table_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',          -- running/completed/failed
    error_message TEXT
);

-- Animal images
CREATE TABLE animal_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL REFERENCES animals(id),
    image_url TEXT NOT NULL,
    display_order INTEGER,
    last_synced_at TIMESTAMP
);
```

### Indexes for Time-Decay Queries

```sql
-- Critical indexes for decay algorithm (Phase 2)
CREATE INDEX idx_volunteer_notes_animal_date
    ON volunteer_notes(animal_id, note_date DESC);

CREATE INDEX idx_volunteer_notes_date
    ON volunteer_notes(note_date DESC);

CREATE INDEX idx_animals_color_category
    ON animals(color_category);

CREATE INDEX idx_animals_last_synced
    ON animals(last_synced_at);

CREATE INDEX idx_volunteer_notes_last_synced
    ON volunteer_notes(last_synced_at);
```

---

## Data Extraction Strategy

### Initial Full Sync

1. **Authenticate**: Capture cookies from browser session
2. **Fetch all animals**: Paginate through animals table (limit=50, offset)
3. **For each animal**:
   - Fetch volunteer notes (filter by animal ID)
   - Fetch walk records
   - Parse kennel card from animal record
4. **Store with timestamps**: Record `last_synced_at` for each record

### Incremental Updates

1. **Query by updated_at**: If Adalo provides `updated_at` field
2. **Fallback**: Compare fetched records against stored `adalo_record_id`
3. **Notes are append-only**: New notes won't modify existing ones

### Rate Limiting

- **Default delay**: 500ms between requests
- **Configurable**: Environment variable `PETDATA_REQUEST_DELAY_MS`
- **Batch size**: 50 records per request (configurable)
- **Retry logic**: Exponential backoff on 429/5xx errors

### Error Recovery

- **Checkpoint system**: Store last successful offset in sync_log
- **Resume capability**: Continue from checkpoint on restart
- **Transaction batches**: Commit every N records to avoid data loss

---

## Implementation Plan

### Files to Create

```
src/petdata/
    __init__.py
    config.py              # Configuration and constants
    db/
        __init__.py
        schema.py          # SQLite schema creation
        models.py          # Data models (dataclasses)
        repository.py      # Database operations
    api/
        __init__.py
        client.py          # Adalo API client
        auth.py            # Cookie-based authentication
        parser.py          # Response parsing
    sync/
        __init__.py
        extractor.py       # Data extraction orchestration
        incremental.py     # Incremental sync logic
    cli.py                 # Command-line interface
```

### Implementation Order

1. **Database Layer** (schema.py, models.py, repository.py)
   - Create SQLite schema
   - Define dataclasses for entities
   - Implement CRUD operations

2. **API Client** (client.py, auth.py, parser.py)
   - Cookie extraction from browser
   - HTTP client with rate limiting
   - Response parsing into models

3. **Sync Engine** (extractor.py, incremental.py)
   - Full sync orchestration
   - Incremental update logic
   - Error handling and recovery

4. **CLI** (cli.py)
   - `petdata sync --full`: Initial sync
   - `petdata sync --incremental`: Update only
   - `petdata status`: Show sync status

---

## Open Questions

1. **Updated timestamps**: Does Adalo provide `updated_at` on records? Need to verify in API response.

2. **Historical notes**: Are all historical volunteer notes accessible, or only recent ones?

3. **Rate limits**: What are Adalo's actual rate limits? Start conservative.

4. **Cookie expiration**: How long do session cookies last? May need refresh mechanism.

5. **Image storage**: Should we download and store images locally, or just URLs?

---

## Verification Plan

1. **Schema creation**: `uv run python -c "from petdata.db.schema import create_tables; ..."`

2. **API connectivity**: Test single animal fetch with captured cookies

3. **Full sync test**: Run against production with small limit first

4. **Data integrity**: Verify note counts match UI

5. **Incremental test**: Run sync twice, verify no duplicates

---

## Success Criteria

- [ ] SQLite schema created and documented
- [ ] API client fetches animal and note data successfully
- [ ] Full sync completes for all dogs
- [ ] Volunteer notes stored with timestamps and ratings
- [ ] Incremental sync identifies new/changed records
- [ ] No duplicate records after multiple syncs
- [ ] Rate limiting prevents API overload

---

## Related Issues

| ID | Title | Priority | Depends On |
|----|-------|----------|------------|
| petdata-11o | Set up SQLite database schema | P1 | - |
| petdata-jf5 | Implement Adalo API client | P1 | petdata-11o |
| petdata-ic4 | Create full sync extraction engine | P2 | petdata-jf5 |
| petdata-ucw | Add incremental sync capability | P2 | petdata-ic4 |
| petdata-w78 | Build CLI interface for sync commands | P3 | petdata-ic4 |
