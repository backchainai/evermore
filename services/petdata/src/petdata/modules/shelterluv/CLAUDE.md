# shelterluv

## Module Overview

This is the ShelterLuv source module: a read-only extraction client for one shelter's animal
records out of the ShelterLuv API, feeding the Animal Record that Pet Data owns.

ShelterLuv is an animal record source and nothing else. It returns demographics, location,
status, photos, videos, microchips, adoption fee and a free-text adopter-facing description.
It returns no volunteer notes, no walks, no activities, no outcome events, no medical data
beyond microchip and altered status, and no listing engagement or analytics of any kind. Do
not plan a feature on this source that needs any of those.

Status: documentation only. No client, parser, settings or tests exist for this source yet.

**Do not reuse `petdata.modules.api` for this source.** That module is a different shelter
system: cookie authentication (`modules/api/auth.py`, `CookieAuth`), a `{"records": [...]}`
envelope (`modules/api/parser.py:47`), and fetch methods for volunteer notes and walk records
(`modules/api/client.py:290`, `:319`) that have no ShelterLuv equivalent. Its field names are
marked in-code as placeholders (`parser.py:1-5`).

## Provenance convention

The vendor's documentation sits behind a time-limited signed URL, so this document is the
durable copy. Every claim below carries one of two markers.

- **(spec)** comes from the vendor's OpenAPI 3.0.0 document.
- **(live 2026-09-09)** was measured against real responses covering three animal records.
  Live measurements override the spec.

## The Publish flag: filter it or you publish bite history

Every entry in `Attributes[]` carries `Publish: "Yes"` or `Publish: "No"` (spec, confirmed
live 2026-09-09). The API returns shelter-internal assessments in the same array as
publishable ones.

**Any code path that produces a kennel card, marketing copy, an aggregator feed, a portal
page, or any other public surface MUST drop every attribute whose `Publish` is not exactly
`"Yes"`.**

On one record inspected on 2026-09-09, these attributes came back with `Publish: "No"`:
Bite History, Stranger Danger, Behavior Assessment Done, Has Been in Playgroup,
Pre-Appointment Call Required, a programme tier level, Cat Test Complete.

Skip the filter and Evermore publishes a bite-history flag and a stranger-danger flag on an
adoptable animal's public card. That is a safety and liability failure for the shelter. The
filter belongs in the parser, at the point the attributes become a `BehaviorProfile`, so no
downstream consumer can forget it. Store the unpublishable attributes if internal tooling
needs them, but store them where a public renderer cannot reach them by accident.

### The filter is necessary and not sufficient: `Publish` gates attributes, not prose

**A third record measured on 2026-09-09 carries `Bite History` with `Publish: "No"` while its
published `Description` discloses the bite in plain language.** The shelter wrote the same
fact into the adopter-facing copy that the flag marks internal.

So filtering `Attributes[]` does not prevent adopter-facing output from carrying the content
the flag was meant to withhold. The flag governs one field.

Treat every path that generates, summarises, rewrites, quotes or excerpts `Description` as
capable of surfacing bite history and other sensitive assessments, regardless of what
`Attributes[]` says. Concretely:

- Do not treat "attributes filtered" as evidence that generated copy is safe to publish.
- A summariser fed the raw `Description` can reproduce or paraphrase the disclosure. Screening
  its output is a separate control from the attribute filter, and this module does not provide
  it.
- The shelter chose to disclose in its own prose. Evermore must not silently strip that when
  regenerating, nor amplify it. Which of those applies is the shelter's editorial decision.

## The two endpoints

The entire API is two GET operations (spec), so this source is read-only by construction.

### `GET /api/v1/animals` (`V1ListAnimals`)

Server `https://new.shelterluv.com` (spec). Returns every animal the shelter ever took in,
not just current inventory.

| Parameter | Type | Constraints | Meaning | Source |
|---|---|---|---|---|
| `status_type` | string enum | `in custody` or `publishable` | `publishable` returns animals whose status is marked publish, which is usually but not always the adoptable set. `in custody` returns current inventory. | spec |
| `sort` | string enum | only value `updated_at` | Switches `since` from create time to last-update time. This description is correct. | spec, confirmed live |
| `since` | integer | Unix timestamp | Filters on last update, not intake. See below. | live 2026-09-09 |
| `limit` | integer | min 1, max 100, default 100 | Page size. | spec |
| `offset` | integer | default 0 | Index of the first record in the page. | spec |

Those five parameters are the whole query surface: no id filter, no name search, no microchip
search, no sort direction control (spec).

Response codes: 200, 401, 429, 422 (spec).

**`since` filters on last update, not intake (live 2026-09-09).** With `sort=updated_at` and a
30-day `since`, every returned record's `LastUpdatedUnixTime` fell inside the window while its
`LastIntakeUnixTime` values were years older. The `since` parameter's own description in the
spec ("records that had an intake occur after the given timestamp") is wrong.

### `GET /api/v1/animals/{id}` (`V1AnimalDetails`)

The path parameter is `Internal-ID`, not `ID` (live 2026-09-09). A detail request using a
record's `ID` value returned 404; the same record requested by its `Internal-ID` returned 200.

**The shelter's short code is not addressable.** The detail route takes only the internal row
id, and the list endpoint has no id filter at all. A lookup by short code means listing the
animals and indexing them locally.

Response codes: 200, 401, 429, 404 (spec). The detail 200 is a bare `V1Animal` object with no
envelope (live 2026-09-09).

## The response envelope

**The list response is an envelope, not the bare array the spec declares (live 2026-09-09).**

```
{
  "animals": [ { "ID": "<short code>", "Internal-ID": "<row id>", "...": "..." } ],
  "has_more": true,
  "success": true,
  "total_count": <integer>
}
```

The keys, types and nesting are the measured shape (live 2026-09-09); the values are
placeholders. For illustrative ids use the vendor's documentation examples, `"ID": "381"` and
`"Internal-ID": "1078738"` (spec), never a value from a real pull.

Records live under `.animals`. The spec's 200 schema for the list route is `type: array` of
`V1Animal` and defines neither `has_more` nor `total_count` anywhere. The vendor's pagination
prose promised both fields and was right; the vendor's schema was wrong.

Paging on `has_more` and `total_count` works (live 2026-09-09): on a shelter whose
`total_count` was a three-digit number, a request at `limit=100` returned `has_more: true`
and the offset walk reached the end.

The detail route returns the object unwrapped, so a parser cannot assume one shape for both
routes.

## Authentication and Worker compatibility

- Scheme `bearerAuth`, declared as `{"type": "http", "scheme": "bearer"}` and applied
  globally (spec).
- Header `Authorization: Bearer <token>` (spec).
- `x-api-scopes: ["animals"]` on both operations. That is the only scope the document names
  (spec).
- Keys are issued per organization from the shelter's own integrations configuration page
  (spec). A second shelter means a second key.
- 401 body: `{"success": 0, "error_message": "Invalid API key"}` (spec).

**Cloudflare Worker compatible (spec).** One static header and nothing that needs Node-only
crypto. A scheduled Worker can be the whole client, which is what hosted-only execution
requires (ADR 0037), with the token stored as a Worker secret in the pattern ADR 0038 uses for
the engagement collector. The token never enters this repo, `wrangler.jsonc`, or a local
`.env` file.

## Rate limits, pagination, and the polling design

- 300 requests per key per minute; over that, 429 (spec). Back off or cache on 429.
- **Rate-limit headers come back on a 200, not only on the documented 429 (live 2026-09-09):**
  `x-ratelimit-limit: 300` and `x-ratelimit-remaining: 299`. The spec attaches
  `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` and `Retry-After` to the
  429 response only. Read the headers off every response and use the remaining count to pace,
  rather than waiting for a 429.
- Offset and limit paging, no cursor (spec). Maximum 100 records per page.
- **Both endpoints read a cache refreshed every 30 minutes (spec).** That is the freshness
  floor. The cache affects updates to animals already cached; an animal never cached before is
  not subject to it.
- No webhooks, no event subscription, no change feed, no ETag, no `If-Modified-Since` (spec).

The polling design follows:

1. Poll `GET /api/v1/animals?sort=updated_at&since=<watermark>&limit=100`, paging on
   `has_more` with `offset`.
2. Set the watermark from the previous run's start time minus a margin, not from the highest
   `LastUpdatedUnixTime` seen. The 30-minute cache means a record can be updated at the source
   before the API will admit it, so a watermark with no overlap drops records.
3. Poll no more often than every 30 minutes. Anything faster re-reads the same cache.
4. A shelter with a three-digit animal count is a handful of requests at `limit=100`, against
   a budget of 300 per minute. Choose page size and request count for clarity.
5. Keep the per-run outcome in `SyncLog` (`packages/schema/src/evermore_schema/animal.py`),
   with `sync_type` `incremental` for the watermark poll and `full` for an unbounded sweep.

`status_type=publishable` narrows the poll to animals the shelter marks publish. Use it for
the marketing pipeline. Use no `status_type` for a complete sweep, because the unfiltered list
includes every animal ever taken in.

## Identity and the crosswalk

Evermore mints its own source-agnostic animal ID as the Animal Record's primary key, and each
source's identifiers are per-source data on the animal rather than keys. ADR 0035 as merged
says otherwise and is being amended: read the amended ADR, and do not treat the shape in
`packages/schema/src/evermore_schema/animal.py` as settled.

What this module contributes under that decision:

| ShelterLuv field | What it is | Role here |
|---|---|---|
| `ID` (string, spec example `"381"`) | The shelter's short code, returned as bare digits inside a JSON string. Not zero-padded and not prefixed. | Per-source attribute. The crosswalk value. Not addressable through either endpoint. |
| `Internal-ID` (string, spec example `"1078738"`) | ShelterLuv's own row id, which does not display on the animal's profile in ShelterLuv. | Per-source attribute and the only value the detail route accepts. Natural fit for `Animal.source_record_id`. |

Both are `type: string` in the schema and both render as bare digits in every example (spec).

**Matching across sources.** The aggregator's own export carries the same short code as a bare
unpadded integer, and one value seen in this API's sample also appears there. So a match
compares the two numbers as integers.

The vendor's Key Terms prose describes a human-facing display code of the form
`<PREFIX>-A-<number>`, where the prefix is the shelter's 3- or 4-letter code (spec). The API
returns neither the prefix nor the assembled code. To render the display form a client must
know the prefix out of band and concatenate it.

## Field mapping to the Animal Record

`V1Animal` has 29 properties (spec). The canonical target is
`packages/schema/src/evermore_schema/animal.py`.

### `Animal`

| Animal Record field | ShelterLuv field | Transform | Source |
|---|---|---|---|
| `id` | none | Evermore mints it. `ID` and `Internal-ID` are per-source attributes, not this key. | owner decision 2026-09-09 |
| `name` | `Name` | Direct. | spec |
| `aka` | none | No source. | spec |
| `breed` | `Breed` | One space-slash string carrying up to two breeds (example `"Chihuahua /Mix"`). Split on `/` and strip if the two values are wanted separately. | spec |
| `species` | `Type` | Enum: `Dog`, `Cat`, `Bird`, `Rabbit`, `Equine`, `Barnyard`, `Small Mammal`, `Large Mammal`, `Exotic/Other`. The schema comment expects `dog`/`cat`, so lowercase and decide what a non-dog, non-cat value means before it reaches the grader. | spec |
| `weight_lbs` | `CurrentWeightPounds` | String to float, up to 4 decimal places. Arrives as a string even when numeric, and as `""` when absent. | spec, live |
| `birth_date` | `DOBUnixTime` | Integer epoch seconds to an ISO date. Estimated, not certified. | spec, live |
| `intake_date` | `LastIntakeUnixTime` | Epoch seconds to an ISO date. Arrives as a string, or `null` when absent. Most recent intake only: there is no intake history. | spec, live |
| `location` | `CurrentLocation` | An object of `Tier1`, `Tier2`, `Tier3` naming the kennel and its parent locations. Flatten to one string. Empty on two records, populated with a `Tier1` string on a third, so handle both. | spec, live |
| `color_category` | none | This is a shelter-local adoptability band (`Green`/`Yellow`/`Orange`/`Senior`/`Designated`) that drives `Animal.is_adoptable`. ShelterLuv has no equivalent. `Color` is coat colour and is not this field. | spec |
| `custody_location` | `InFoster` | `true` maps to `foster`. `false` alone does not prove `kennel`: `CurrentLocation` was empty on two records, including one with `InFoster` true. Where `CurrentLocation.Tier1` is populated and `InFoster` is false, `kennel` is supportable. Otherwise leave `None` rather than guessing. | live |
| `photo_url` | `CoverPhoto` | Direct. Also appears duplicated as the first entry of `Photos[]`. | spec, live |
| `public_profile_url` | none | No field carries it. One record's `Description` opened with such a URL and another opened with a section heading, so the prose is not a dependable source. Leave `None`. | live |
| `source_record_id` | `Internal-ID` | Direct. | live |
| `created_at` | none | The API exposes no record creation timestamp. | spec |
| `updated_at` | `LastUpdatedUnixTime` | Epoch seconds to ISO. Arrives as a string. | spec, live |
| `last_synced_at` | none | Set by ingest. | internal |

### `BehaviorProfile`

Sourced entirely from `Attributes[]`. See the next section.

### `AnimalImage`

`Photos[]` is an array of URLs of all published photos (spec), with the cover photo duplicated
as the first entry (live 2026-09-09). Map each URL to one `AnimalImage`, dedupe the cover, and
use the array position for `display_order`. A photo count is therefore available, which the
grader's photos dimension needs. Nothing distinguishes an editorial photograph from a
volunteer snapshot: see the open questions.

### `VolunteerNote`, `StaffAssessment`, `WalkRecord`

No source. Leave them empty for a ShelterLuv-only shelter.

### ShelterLuv fields with no Animal Record home today

`Campus`, `Sex`, `Status` (free text, no enum given), `Altered` (`Yes`/`No`/`Unknown`), `Age`
(months, integer), `Size` (a banded string, spec example `"Medium (20-59)"`), `Color`,
`Pattern`,
`AdoptionFeeGroup`, `LitterGroupId`, `AssociatedPerson`, `Microchips`, `PreviousIds`,
`Videos`. Four of these matter:

- **`Microchips[]`** does arrive populated, with `Id`, `Issuer` and `ImplantUnixTime`. The
  timestamp is a string on one record and `null` on another, so an implant date is optional
  even when the chip is recorded. It is the only medical-adjacent data the API carries, and
  the schema has no medical model at all, so it currently has nowhere to land.
- **`Sex`, `Status`, `Color`, `Age`** are facets the profile grader reads and the Animal
  Record does not model. This source can supply all four.
- **`AdoptionFeeGroup`** returns one object with `Id`, `Name`, `Price`, `Discount`, `Tax` and
  `IsVariable`. `IsVariable` true means the price may be 0 and a client should consider showing
  `Name` instead.
- **`PreviousIds[]` is opportunistic, not a dependable identifier column.** On one record it
  carried a genuine cross-system id with a source-system type naming another shelter
  management system. On another it carried nothing but the animal's own name, with a null type
  and a null issuing shelter. Never key or join on it.

## `Attributes[]` is the behaviour source

`Attributes[]` is the behaviour profile, not the operational tag list the spec's single example
(`"Foster-to-Adopt"`) implies (live 2026-09-09). It is the only source in this API for
`BehaviorProfile`.

One record carried 16 entries, each shaped `{Internal-ID, AttributeName, Publish}`. The names
seen on that record:

Behavior Assessment Done, Bite History, Dog Fearful, Dog Selective, Experienced Owner, Has
Been in Playgroup, No Condo or Apartment, Pre-Appointment Call Required, No Kids, Cat Test
Complete, Has Met Cats and Done Well, Adult-Only Home Preferred, Housetrained, Stranger
Danger, plus a shelter programme tier and its level.

A third record widens the vocabulary with: No Cats, Dogs - Unknown, Likes water, and again
No Kids, Bite History, Pre-Appointment Call Required and Has Been in Playgroup. It also
carries a shelter programme tier and level, a senior-care programme flag, and a
foster-programme eligibility flag.

**The programme flags are not behaviour.** Tier names, tier levels, senior-care programmes and
foster-programme eligibility name shelter programmes an animal is enrolled in. They belong in
`behavior_mod_tags` at best, as opaque operational labels, and must not be read as
temperament, compatibility or training signals.

| `BehaviorProfile` field | Attribute names seen that bear on it |
|---|---|
| `dogs_compatible` | Dog Fearful, Dog Selective, Has Been in Playgroup, Dogs - Unknown |
| `cats_compatible` | Cat Test Complete, Has Met Cats and Done Well, No Cats |
| `kids_compatible` | No Kids, Adult-Only Home Preferred |
| `housebroken` | Housetrained |
| `things_likes` | Likes water |
| `behavior_mod_tags` | Bite History, Stranger Danger, Behavior Assessment Done, Experienced Owner, No Condo or Apartment, Pre-Appointment Call Required, and the programme flags above as opaque labels |
| `knows_commands` | No attribute seen bears on it. |

Three rules for the mapping code:

1. **Attribute names are shelter-configured, so the mapping is a per-shelter lookup table, not
   a constant.** The lists above are one shelter's vocabulary on one day, and the third record
   already added names the first did not carry. A name that is not in the table is unmapped,
   and an unmapped name must be visible rather than silently dropped.
2. **A missing attribute is not a negative.** "Cat Test Complete" absent means the test was not
   recorded, not that the animal fails with cats. Map absence to `None`, not `False`.
3. **An explicit unknown is not a negative either.** "Dogs - Unknown" states that dog
   compatibility was not established. Map it to `None`, the same as absence.

The `Publish` filter applies to every one of them, and it gates only these attributes: the
`Description` prose can disclose the same fact.

## `Description` is the graded copy

`Description` is the field the profile grader scores. In the owner's words, it is the kennel
card and web site memo used to communicate free-form information about the animal to potential
adopters, it is the content that gets published to aggregators, and it is the content the
profile grader grades.

It publishes automatically, and the API exposes no publication status and no published-at
timestamp, so grading the source text is the correct target.

**The format varies by record, so a parser can assume neither shape (live 2026-09-09).** One
record is unbroken prose: paragraphs separated by `\n\n`, no headings anywhere. Another is
organised under four uppercase section headings, covering the animal generally, household fit,
training, and what an adopter should know. Both are the same field on the same shelter.

Three consequences:

1. An adapter must detect structure per record rather than assume it. Where uppercase headings
   are present it can segment on them; where they are absent it has to judge the scored topics
   (`about`, `dogs`, `cats`, `kids`, `training`, `housebreaking`, `likes`, `struggles`) from
   unstructured prose. Build the unstructured path first, because it is the fallback whenever
   heading detection misses.
2. The prototype grader's section parser keys on heading labels, so it works on some records
   and silently returns nothing on others. Returning no sections must be distinguishable from
   finding empty ones, or a headingless record scores as a zero-coverage profile when it may be
   well written.
3. `Description` arrives as `""` when the shelter has written nothing. An empty string is a
   missing bio, not an empty bio, and must not be scored either.

**The first line is not reliably the public profile URL.** One record opened with a bare URL to
the shelter's own public profile page, whose final path segment matched the name-based slug the
prototype grader keys records on. Another opens with a section heading. So the URL is present
on some records only, and the slug bridge is one record's copy habit rather than a convention.

Grades must key on the animal record. Treat a first-line URL as an opportunistic extra, never
as the source of `public_profile_url`.

## Typing traps

The typing behaviour in each row was measured live on 2026-09-09. Every one of these will
break a naive `model_validate`. Illustrative field values below are the vendor's
documentation examples (spec), not values from a live pull.

| Trap | Detail |
|---|---|
| Timestamps are inconsistently typed | `LastUpdatedUnixTime` and `LastIntakeUnixTime` arrive as strings. `DOBUnixTime` arrives as an integer. `Microchips[].ImplantUnixTime` arrives as a string on one record and `null` on another. The spec types all four as `integer`. Coerce every epoch field through one parser that accepts string, int and null. |
| Two different absences | Missing values arrive as `""` on `Description`, `Color`, `Size` and `CurrentWeightPounds`, and as `null` on `LitterGroupId`, `AdoptionFeeGroup`, `LastIntakeUnixTime` and `Microchips[].ImplantUnixTime`. Normalize both to `None` on the way in, or `weight_lbs` gets a `float("")` and `Description` gets scored as present-but-empty. |
| Numbers arrive as strings | `CurrentWeightPounds` is a string even when numeric. |
| `Age` is months | An integer count of months, not years. `Animal.age_years` derives from `birth_date`, so use `DOBUnixTime` for that and treat `Age` as an independent facet. |
| `Breed` and `Color` are compound single strings | Space-slash separated, up to two values each (spec examples `"Chihuahua /Mix"`, `"Black /White"`). Not arrays. Note the space before the slash. |
| `Size` is a banded string | Spec example `"Medium (20-59)"`. Not a number and not an enum the spec declares. Do not parse a weight out of it; use `CurrentWeightPounds`. |

## Spec versus reality

Every place the vendor's OpenAPI document and the live response disagree, all measured
2026-09-09. Trust the right-hand column.

| Field or behaviour | Spec says | Live response returns |
|---|---|---|
| List 200 body | A bare `array` of `V1Animal`. Neither `has_more` nor `total_count` is defined anywhere. | An envelope: `animals`, `has_more`, `success`, `total_count`, records under `.animals`. |
| Detail path parameter | "The internal id of animal", with a curl example of `/api/v1/animals/1`. | Accepts `Internal-ID` only. A request by `ID` returns 404. |
| Rate-limit headers | Attached to the 429 response only. | `x-ratelimit-limit` and `x-ratelimit-remaining` present on a 200. |
| `since` semantics | "records that had an intake occur after the given timestamp". | Filters on last update. Returned records' `LastIntakeUnixTime` values were years outside the window. |
| Epoch field types | `LastUpdatedUnixTime`, `LastIntakeUnixTime` and `DOBUnixTime` all `integer`. | The first two are strings, the third an integer. |
| `CurrentLocation` | `array` of string. | An object of `Tier1`, `Tier2`, `Tier3`. Empty on two records, including one with `InFoster` true, and populated with a `Tier1` string on a third. So the array typing is a bug and the field does carry data at some shelters. |
| `AssociatedPerson` | An `array` of object. | A single object, not an array. |
| `AdoptionFeeGroup` | An array. | A single object (`Id`, `Name`, `Price`, `Discount`, `Tax`, `IsVariable`). |
| `Videos` | An array of arrays of objects. | A flat array of objects (`VideoId`, `EmbedUrl`, `YoutubeUrl`, `ThumbUrl`). |
| `Attributes[]` meaning | One example, `"Foster-to-Adopt"`: an operational tag. | The behaviour profile. 16 entries on one record, covering dog, cat, kid and housetraining assessments plus bite history, mixed with shelter programme flags. |

## What this API does not have

Verified by a zero-hit search of the whole spec document for `note`, `walk`, `activit`,
`medical`, `vaccin`, `vet` and `treatment`. None of the following exists, in any endpoint or
any field:

- Volunteer notes, staff notes, or free-text observations other than `Description`.
- Walks, activities, events, or any timestamped interaction record.
- Outcome events. Intake is the single scalar `LastIntakeUnixTime`, with no history.
- Medical data beyond `Microchips[]` and `Altered`. No vaccinations, no treatments, no vet
  records, no weight history.
- Listing engagement or analytics of any kind: no views, impressions, favorites, saves,
  inquiries or applications. Engagement comes from the aggregator collector (ADR 0038), never
  from here.
- Publication status or a published-at timestamp for `Description` or anything else.
- Search by name or by microchip. The list endpoint has no search parameter.
- Any people or adopter resource. The only person data is the nested `AssociatedPerson`
  (a single object, not the array the spec declares) with `FirstName`, `LastName`,
  `OutDateUnixTime` and `RelationshipType`. It carries a real person's name, usually a
  foster's, so treat it as personal data: it must not reach a public surface, a log, a
  prompt or a generated document.
- Any resource other than animals. The vendor's Key Terms prose names person and transaction
  id formats, but no such endpoint exists.
- Write operations. Two endpoints, both GET.
- Webhooks, events, or a change feed. Polling is the only mechanism.

## Open questions

1. **How often does `Description` carry section headings, and are the heading labels stable?**
   Of three records, one uses four uppercase headings and one uses none. An adapter needs to
   know whether the heading set is a shelter template worth segmenting on or ad-hoc per writer.
   Settle it by reading a full page of publishable records and tabulating the heading labels.
2. **Can editorial photographs be distinguished from volunteer snapshots?** `Photos[]` gives
   URLs and an order, with the cover duplicated first. The grader's photos dimension is meant
   to reward editorial images, and nothing in the payload separates the two. Settle it by
   checking whether the URL path or filename pattern differs by origin.

## Build and test commands

This module lives inside the petdata service, so its gates are the petdata gates. Run them
from `services/petdata/` with the `uv run` prefix; see `services/petdata/CLAUDE.md` for the
full set. CI runs the `petdata` job for any change under `services/petdata/**`.

When this module grows code, one test is required: a parser test that asserts an attribute
with `Publish: "No"` never reaches a publishable surface.
