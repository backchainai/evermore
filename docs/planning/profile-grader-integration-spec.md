# profile-grader → Evermore: Daedalus Integration Specification

**What this is:** a self-contained specification for integrating the standalone
`profile-grader` prototype into the [Evermore](https://github.com/backchainai/evermore)
platform as a first-class service plus view. It is written to be consumed by the Daedalus
pipeline in a fresh session working in the Evermore repo. It expands
[`MIGRATION.md`](MIGRATION.md) from a handoff note into a decomposed, mechanically-gradable
work plan.

**How to use it with Daedalus:** Sections 1-7 are context (goal, prototype inventory,
the durable contract, target architecture, workflows, constraints). Section 8 is the work
itself: one epic and nine child tickets, each with scope, dependencies, and acceptance
criteria phrased as runnable checks or observable behavior. File Section 8 as GitHub Issues
in `backchainai/evermore` (GitHub-native tracking, ADR 0023: no Beads here), then dispatch
with `/daedalus:run-pipeline`. Each ticket is sized to be a single lead's end-to-end unit
(claim → plan → implement → review → PR). The acceptance criteria are written to satisfy
Daedalus's blueprint-legibility invariant: every criterion reduces to a gate exit code or an
observable behavior, so a Sonnet implementer can build to it and an Opus review-gate can
verify it.

The source prototype (this directory) is the reference implementation. Where this spec says
a file "ports as-is," the intent is to copy it into the Evermore module and adjust imports,
not to rewrite it.

---

## 1. Goal and context

### 1.1 What the tool does

profile-grader scores an animal's adoption copy against research-backed adoption-writing
guidance and returns a normalized 0-100 score plus a per-criterion breakdown, quality flags,
and a ranked fix list. It exists to make a counterintuitive research finding actionable for a
novice profile editor: analytic, factual, behavior-first copy places shelter animals faster
than emotional, anthropomorphizing copy (Markowitz 2019, 680k Petfinder ads; Kelling et al.
2024, *Society & Animals*). The tool turns that finding into a per-profile diagnosis.

The audience is a **novice profile editor**. The product surface answers two questions:
which profiles are written poorly enough to prioritize rewriting, and which are written well
enough to study as examples.

### 1.2 The outcome it serves

Evermore is measured against one outcome: more healthy, safe, and permanent adoptions. The
grader contributes by improving the marketing copy that gates adopter interest. Its long-run
payoff is calibration: once placement outcomes are joined on animal ID, the 0-100 score is
correlated against actual days-to-placement and the rubric weights are re-fit, converting
"graded against research" into "graded against Evermore outcomes" (Section 8, ticket 9 sets
up the data spine for this; the calibration itself is future work, not in this spec).

### 1.3 Placement in the Evermore data spine

Evermore's spine is `Sources → Animal Record → Package → Composition → Export`. The grader is
a **read/scoring consumer**. It never mutates animal data. It scores adoption prose:

- The **prose it scores** is a **Composition** (the generated + human-edited adoption piece)
  or an equivalent draft the editor is working on. The eight narrative sections (About, With
  Dogs, With Cats, With Kids, Training, Housebreaking, Likes, Struggles) are Composition
  content, not raw Animal Record data.
- The **facets it needs** (species, temperament tags for kids/dogs/cats, photo count, breed,
  age, weight, status) come from the **Animal Record** (Pet Data owns it).

So the grader reads from both: structured facets from the Animal Record and narrative prose
from the Composition. This is a change from the prototype, which scraped both out of one FOHA
web page. See Section 4.1 (the input adapter) and Section 9 decision D2.

"Extraction" in Evermore means Pet Data pulling from a shelter system, not this tool crawling
a website. **All scraping is removed** on the port (Section 7).

---

## 2. Source prototype inventory (attributes)

Standalone Python package, `uv`-managed, `hatchling` build backend, flat layout. Console
entry point `grade`. No network in tests; the judge is the only paid dependency at runtime.

### 2.1 Module map

| Module | Lines | Responsibility | Port disposition |
|---|---|---|---|
| `parse.py` | 273 | FOHA WordPress markdown → `Profile` (sections, tags, facets, photos); rubric v1.1 added label-based heading detection and comment-boundary stripping, both FOHA-web-specific | **Replace** with an Animal-Record/Composition adapter (Section 4.1); the heading/boundary logic does not port (Evermore input is structured Composition data, not scraped HTML) |
| `scrape.py` | 95 | Firecrawl crawl of foha.org into a local cache | **Delete** (Pet Data owns extraction) |
| `lexicons.py` | 92 | Social-word, gatekeeping, and absolute-claim phrase lists | Port as-is (domain data) |
| `metrics.py` | 129 | Deterministic pass: social density, gatekeeping, brevity, photos; deterministic compliance flags | Port as-is (rubric v1.1: `section_completeness` and `missing_struggles` are judged now, not computed here, see 2.2) |
| `judge.py` | 210 | LLM-as-judge pass for the four qualitative dimensions plus per-topic `topic_coverage` (rubric v1.1; drives `section_completeness`); run-N-average, spread, tag/body hard cap | Port; route the client through Cloudflare AI Gateway |
| `score.py` | 206 | Weights, band thresholds, `combine`, cohort percentiles, `DIMENSION_HELP` gloss; `RUBRIC_VERSION` 1.1 (`section_completeness` method now judge; `missing_struggles` from `topic_coverage`) | Port as-is |
| `record.py` | 257 | Build self-contained per-profile records + `index.json` + `scores.jsonl`; reserved-slug guard | Port; `write_run` output goes to Postgres, not files |
| `schema.py` | 147 | Pydantic response contract (the durable interface) | Port as-is (Section 3.1) |
| `server.py` | 103 | FastAPI app, `Store` Protocol, `FileStore`, CORS, slug/traversal guard, `/api/docs` | Port; swap `FileStore` for a Supabase store, tighten CORS, add auth |
| `report.py` | 143 | Human-readable markdown scorecard + cohort roll-up | Port as-is (optional CLI/export surface) |
| `cli.py` | 137 | `scrape` / `score` / `run` / `serve` subcommands | Partially port: `serve` becomes the service entrypoint; `scrape` is dropped |
| `dashboard/index.html` | (single file) | Throwaway vanilla-JS hash-routed SPA | **Rebuild** as a SvelteKit view (Section 4.5) |

### 2.2 The scoring pipeline

```
(prototype)   scrape → parse → metrics(deterministic) → judge(LLM) → score → record → serve
(Evermore)    Animal Record + Composition → adapt → metrics → judge(via AI Gateway) → score → store(Postgres) → serve → SvelteKit view
```

- **Deterministic pass** (`metrics.compute`): reproducible, no LLM. Produces four dimension
  scores (no_social_words, no_gatekeeping, brevity, photos) and the deterministic compliance
  flags.
- **Judge pass** (`judge.judge_profile`): scores the four reading-dependent dimensions,
  runs N times (default 3) and averages, reports run-to-run spread so ambiguous profiles get
  a human spot-check, and enforces one hard cap (a temperament tag contradicting the body
  caps *observed-not-promised* at 2 and raises a flag). Rubric v1.1: the same judge call also
  assesses per-topic `topic_coverage` (covered/brief/absent) for all eight topics from the
  full staff text, at no extra API cost. `section_completeness` (dim 7) is derived from it
  (covered=1.0, brief=0.5, absent=0, averaged across runs), and `missing_struggles` fires
  when `struggles` is absent anywhere in the copy.
- **Combine** (`score.combine`): weighted sum normalized to 0-100, plus a ranked fix list
  (edits ordered by recoverable points).
- **Cohort percentile** (`score.apply_cohort_percentiles`): rank within a species cohort;
  the 0-100 raw score is absolute and cohort-independent.

### 2.3 Current tests (the behavior to preserve)

14 tests, all offline (no network, no LLM):

- `tests/test_parse_metrics.py` (7): parsing variants (emoji-in-heading, LOVE/LIKE
  substring trap, no-ABOUT intro fallback), deterministic dimension scores, facet parsing,
  the full record/ledger write, the reserved-slug rejection.
- `tests/test_server.py` (7): both API routes (a 200 also proves the payload validates
  against the pydantic contract), unknown slug → 404, reserved `index` slug → 400, malformed
  slugs → 400, root serves HTML, missing index → 404.

The parsing tests are FOHA-markdown-specific and mostly retire with `parse.py`; the scoring,
record, and server tests port and are the regression floor for the port.

---

## 3. The durable contract (interfaces)

This is the interface that must survive the port unchanged, because the SvelteKit view and
any future consumer bind to it. Authoritative source: `schema.py` and `rubric.md`, which port
verbatim. Reproduced here so this spec is self-contained for a session without the source.

### 3.1 API response models (`schema.py`)

Two routes, both typed with a pydantic `response_model` (validated on the way out, documented
at `/api/docs` as OpenAPI 3.1).

**`GET /api/index` → `IndexResponse`**

```
IndexResponse:
  run_id: str
  scored_at: str
  rubric_version: str
  schema_version: str
  bands: dict[str, list[ScoreBand]]        # keys: "score" (0-100), "dimension" (0-4)
  dimensions: list[RubricDimension]         # rubric metadata, no per-profile scores
  profiles: list[IndexProfile]              # one row per animal, the cohort table

ScoreBand:       { key: str, label: str|None, min: float }
RubricDimension: { id, label, plain, tip, weight: int, method: str }
IndexProfile:    { slug, name, url?, species, raw: float, band: str, cohort_key,
                   cohort_percentile?, age_months?, weight_lbs?, status?,
                   foster_eligible?, photo_count: int, body_word_count: int,
                   scored_at, flags: list[str] }
```

**`GET /api/profile/{slug}` → `ProfileRecord`** (self-contained: everything to render one
detail page without a second fetch)

```
ProfileRecord:
  # provenance
  schema_version, grader_version, rubric_version, model, judge_runs: int, run_id, scored_at
  # identity / facets
  slug, name, url?, species, breed?, age_raw?, age_months?, sex?, weight_raw?,
  weight_lbs?, color?, status?, foster_eligible?, location?,
  tags: dict[str, str]                      # kids/dogs/cats -> raw temperament label
  photo_count: int, body_word_count: int, scraped_at?
  # content
  opening_sentence: str, sections: dict[str, str]
  # scores
  raw: float, max_raw: int, band: str, cohort_key, cohort_size: int, cohort_percentile?
  dimensions: list[Dimension]
  flags: list[Flag]
  fix_list: list[FixItem]
  # outcome placeholders (null until funnel data is joined; keep schema stable)
  adopted?, adopted_at?, days_to_placement?, length_of_stay_days?, intake_date?

Dimension: { id, label, plain, tip, weight: int, method, score: float, band,
             weighted_points: float, recoverable_points: float, detail: dict }
Flag:      { code, label, severity, detail }
FixItem:   { dimension, label, recoverable_points: float, current: float }
```

Contract note that already caught a real bug: `tags` is `dict[str, str]`
(kids/dogs/cats → label), not a list. The response_model boundary is what surfaces drift
between what the record builder writes and what the contract promises, as a failing test
rather than a broken frontend. Keep it.

### 3.2 The rubric (`rubric.md`)

Nine dimensions, weights sum to 100. Each dimension scored 0-4 against fixed anchors, then
weighted: `raw = sum(weight_i * score_i / 4)`.

| # | Dimension (`id`) | Weight | Method | Backing |
|---|---|---|---|---|
| 1 | Analytic vs. narrative language (`analytic_language`) | 20 | judge | Markowitz: strongest single finding |
| 2 | Behavioral concreteness (`behavioral_concreteness`) | 15 | judge | Markowitz: behavior > adjectives |
| 3 | Observed, not promised (`observed_not_promised`) | 15 | judge + flags | Observed-only rule |
| 4 | No social / humanizing words (`no_social_words`) | 10 | deterministic | Markowitz |
| 5 | No gatekeeping language (`no_gatekeeping`) | 10 | deterministic | Kelling |
| 6 | Identity-forward opening (`identity_opening`) | 5 | judge | Markowitz: open on who |
| 7 | Section completeness (`section_completeness`) | 10 | judge (`topic_coverage`) | Template: 8 topics, judged covered/brief/absent |
| 8 | Brevity (`brevity`) | 5 | deterministic | Markowitz: shorter places faster |
| 9 | Photo count (`photos`) | 10 | deterministic | Kelling/Markowitz |

Full 0-4 anchors per dimension live in `rubric.md` (ports verbatim; `RUBRIC_VERSION` is 1.1). Two design commitments
bind any change: (1) absolute score first, cohort percentile second (copy is judged against
the research ideal, not curved); (2) grade the framing, not the facts (disclosing a struggle
is mandatory and never penalized; emotional or gatekeeping framing is).

### 3.3 Score bands (single source of truth, emitted in `index.json`)

The view renders bands from data, never hardcodes thresholds.

```
SCORE_BANDS (0-100 raw):  g "Reference-worthy" ≥65 | a "Needs work" ≥45 | r "Needs rewrite" ≥0
DIM_BANDS   (0-4 dim):    g ≥3.0 | a ≥2.0 | r ≥0.0
```

### 3.4 Compliance flags (reported, never scored into the total)

Surfaced independent of the score so no one can raise a score by deleting content. A flag
shows on the landing page regardless of score, so a high scorer with a contradiction is not
blindly copied.

- `missing_struggles` (high): the copy discloses no struggle anywhere (rubric v1.1: judged from `topic_coverage`, not from an empty labeled section), the disclosure floor.
- `tag_body_contradiction` (high): a temperament tag asserts a trait the body calls unknown.
- `absolute_claim` (medium): narrative guarantee language ("great with all dogs," "will love").

---

## 4. Target architecture in Evermore

Conforms to `~/.claude/standards/tech-stack-standard.md` and Evermore ADR 0024 (nothing
grandfathered). This section states the target; Section 8 sequences the work.

### 4.1 Module shape and placement

A new service, `services/grader/`, following the `services/petdata/` pattern: Python package
under `src/grader/`, env prefix `GRADER_`, FastAPI title "Profile Grader", its own `CLAUDE.md`
with build/test commands. See Section 9 decision D1 (standalone service vs. a capability
inside `services/biowriter`).

- **Backend:** FastAPI on Cloud Run, `uv`-managed, `src/` layout.
- **Deploy:** `gcloud run deploy --source .`.
- **Dev:** Docker Compose + Dev Containers, one-command `docker compose up`.

### 4.2 The input adapter (replaces `parse.py`)

The prototype's `Profile` dataclass is the internal input to the whole pipeline
(`metrics.compute` and `judge.judge_profile` both take a `Profile`). Preserve `Profile` as
the internal seam and write one adapter that builds it from Evermore data instead of scraped
markdown:

```
adapt(animal_record, composition) -> Profile
```

`Profile` fields the adapter must populate: `slug`, `url`, `name`, `species`, `metadata`
(breed/age/sex/weight/color/status/location), `tags` (kids/dogs/cats → label), `sections`
(the 8 narrative keys), `photo_count`. The derived properties (`body_text`,
`opening_sentence`, `age_months`, `weight_lbs`) stay as-is. Keeping `Profile` as the boundary
means `metrics`, `judge`, `score`, and `record` port with zero changes.

Rubric v1.1 relaxes the section-mapping burden: the judge assesses topic coverage from the
full staff text (`Profile.body_text`), so `section_completeness` no longer depends on every
topic landing in its own labeled `sections` key. The adapter must supply the complete prose;
it populates `sections` where the Composition exposes labeled content, but scoring does not
require a perfect eight-key split. This is the practical resolution of decision D2's 8-vs-5
section question: coverage is content-judged, not label-counted.

### 4.3 Data access (the `Store` seam → Supabase)

`server.py` already isolates data access behind a `Store` Protocol
(`get_index() -> dict|None`, `get_record(slug) -> dict|None`), with `FileStore` as the local
implementation. The routes bind to the Protocol, not the store. The port:

- Implement a `SupabaseStore` (SQLAlchemy async / asyncpg, per ADR 0025) that reads the
  records `record.write_run` produced, now persisted to Postgres.
- Alembic migration for the results tables (an index/cohort table and a per-profile record
  table, or a single JSONB record table plus a materialized index view).
- Scope every read to the shelter/org via Supabase Auth + RLS.
- Cloud Run's filesystem is ephemeral; `FileStore` is dev/test-only after the port.

### 4.4 LLM plumbing

- Route `judge.py`'s Anthropic client through **Cloudflare AI Gateway** (base URL and key
  from config). Keep run-N-average, spread reporting, and the tag/body hard cap unchanged.
- **Promptfoo** eval suite for the judge in CI from day one (anchor cases that pin the
  counterintuitive finding: a known-emotional profile must score low on `analytic_language`).

### 4.5 The view (rebuild in SvelteKit)

`dashboard/index.html` is a throwaway refinement surface. Rebuild it as a SvelteKit route
(SvelteKit + Svelte 5 runes + Skeleton UI v4), consuming `/api/*` and the shared
design-system tokens from `packages/design-system/` so it reads as one product with the rest
of the suite. See Section 9 decision D3 (a route inside `apps/stacker` vs. a new app). The
behavior to reproduce:

- **Landing page:** every profile ranked by score, highest first, as a color-banded bar
  chart (green/amber/red from `bands.score`). A flag marker (⚑) on any flagged profile
  regardless of score. A "study these" strip of the top unflagged greens. Clicking an animal
  name anywhere, or selecting it from a top jump-to dropdown (sorted alphabetically; the ranked
  bar list stays by score), navigates to that profile's detail.
- **Detail page:** the flags block; a "fix this first" callout (top recoverable-points item);
  the nine criteria ordered by recoverable points, each leading with a left color-banded
  **percentage grade** (points earned vs. possible), then label + plain-language question,
  then points; each row expands to the grader's rationale, the verbatim driving quote, and
  the plain-language fix (`tip`). A per-criterion score bar is not used; the banded percentage
  is the at-a-glance signal. The `section_completeness` row expands to the per-topic coverage
  map (each of the eight topics marked covered/brief/absent).
- **Security:** the copy being rendered is untrusted shelter content. Preserve the
  prototype's defenses: HTML/attribute escaping on all interpolated content, and http(s)
  scheme validation on any URL before it becomes an `href`.

### 4.6 Conformance (tech-stack standard, add at integration)

- **Auth:** Supabase Auth + RLS; records scoped to the org.
- **Observability:** structlog JSON logging; OpenTelemetry API instrumentation (API only, no
  vendor SDKs).
- **Ops endpoints:** health check; `/llms.txt` via `fast-llms-txt`.
- **CORS:** tighten `allow_origins` from `*` (prototype default, local-dev only) to the app
  origin(s). `create_app` already takes `cors_origins`; pass real origins from config.
- **CI/CD:** GitHub Actions; `anthropics/claude-code-action@v1` for `@claude` PR workflows;
  Workload Identity Federation for GCP auth (no long-lived keys).
- **Tool schemas / docs:** expose the OpenAPI 3.1 spec (already at `/api/docs`); optionally
  convert to Anthropic tool-use definitions via `openapi-llm` if the grader becomes callable
  by another module.

---

## 5. Workflows

### 5.1 Novice editor (the primary product workflow)

1. Opens the grader view for the shelter. Lands on the ranked cohort chart.
2. Reads top-down: red bars are rewrite candidates, the "study these" strip is the example
   set. A ⚑ warns that a high scorer still has a disclosure or contradiction problem.
3. Clicks an animal to open its detail. Reads the "fix this first" callout, then works down
   the criteria ordered by recoverable points.
4. Expands a criterion to see why it scored as it did (rationale), the exact sentence in the
   copy that drove it (quote), and how to improve it (plain-language tip framed as what the
   research prefers).
5. Edits the Composition elsewhere in Evermore; re-scoring reflects the improvement.

### 5.2 Scoring run (the operator/system workflow)

Triggered per-animal on Composition change, or as a batch. Adapter builds a `Profile` from
the Animal Record + Composition → deterministic metrics → judge (N runs via AI Gateway) →
combine → cohort percentiles across the batch → persist records to Postgres → available at
`/api/*`. No scraping step.

### 5.3 Calibration (future payoff, spine set up now)

Records carry null outcome fields keyed to the animal. Once ~30-50 profiles are scored and
placement data is joined on animal ID, correlate `raw` against days-to-placement and re-weight
the rubric. `scores.jsonl` (prototype) becomes an append-only scoring time series in Postgres
so runs stay joinable as the rubric version advances.

---

## 6. Non-goals and constraints

- **Observed-only claims.** The rubric grades framing, never rewards hiding a problem, and
  treats "Unknown" as a valid complete answer. Do not add any dimension that would reward
  omitting a disclosed struggle.
- **No scraping.** The grader does not crawl any site. Input is Evermore data.
- **No animal-data mutation.** The grader is read-only against the Animal Record and
  Composition; it writes only its own score records.
- **User-visible content avoids em-dashes** (colons, parentheses, commas), matching Evermore's
  convention and this project's writing rules.
- **Licensing:** Apache-2.0, copyright Backchain LLC (repo-wide posture).
- **Tracking:** GitHub-native (Issues + Projects + PRs). Do not `bd init` in Evermore.
- **No design-partner or branded SMS names** in code, tests, or docs; refer to shelter
  systems generically as "Shelter Management System (SMS)".

---

## 7. Ported / swapped / added (summary)

| Ports as-is | Swapped at integration | Added at integration |
|---|---|---|
| `schema.py` (contract) | `parse.py` → Animal-Record/Composition adapter | Supabase Auth + RLS |
| `metrics.py`, `lexicons.py` | `FileStore` → `SupabaseStore` (asyncpg + Alembic) | structlog JSON logging |
| `score.py` (weights, bands, gloss) | Firecrawl scraping → deleted (Pet Data extracts) | OpenTelemetry API instrumentation |
| `record.py` (record shapes) | HTML dashboard → SvelteKit view | health check + `/llms.txt` |
| `judge.py` logic (spread, hard cap) | Anthropic direct → Cloudflare AI Gateway | Promptfoo evals in CI |
| `rubric.md`, score bands, flags | `grade serve` (uvicorn) → Cloud Run service app | tightened CORS (app origins) |
| Server routes + slug/traversal guard | Local files → Postgres persistence | GitHub Actions CI/CD |

---

## 8. Work decomposition (Daedalus tickets)

One epic, nine child tickets. Dependencies are noted; where none, tickets can run in parallel
leads. Complexity is a hint for the designer-escalation triage (S = mechanical, M = normal,
L = design pass warranted). Acceptance criteria are written to be mechanically gradable.

### EPIC: Integrate profile-grader as the Evermore `grader` service and view

**Success criteria:** an animal's adoption Composition is scored through the ported pipeline,
persisted to Postgres scoped by org, served over the typed API behind auth, and rendered in a
SvelteKit view on the design-system tokens; the judge runs through the AI Gateway with
Promptfoo evals in CI; `docker compose up` brings the service up clean and the ported test
floor is green.

---

**T1. Scaffold `services/grader/` to the tech-stack standard.** (Complexity: M)
- Scope: greenfield FastAPI service, `uv`, `src/grader/` layout, Dockerfile, Compose wiring,
  config module (env prefix `GRADER_`), health endpoint, structlog JSON logging, OTel API
  instrumentation, `/llms.txt` via `fast-llms-txt`, a `CLAUDE.md` with build/test commands.
- Out of scope: any domain logic (T2), data layer (T4), auth (T6).
- Dependencies: none.
- Acceptance criteria:
  - `docker compose up` starts the service; `GET /health` returns 200.
  - `GET /llms.txt` returns 200 with a non-empty body.
  - `uv run pytest` collects and passes (a smoke test asserting the app boots).
  - `ruff check`, `ruff format --check`, `bandit -r src/`, `mypy src/` all exit 0.
  - Logs emit as single-line JSON (a captured log record parses as JSON).

**T2. Port the pipeline core (parse-independent).** (Complexity: M; depends on T1)
- Scope: copy `lexicons.py`, `metrics.py`, `judge.py`, `score.py`, `record.py`, `schema.py`,
  `rubric.md` into `src/grader/`; adjust imports; keep `Profile` as the internal input type
  (a thin dataclass, temporarily constructed by test fixtures until T3). Port the scoring,
  record, and server-contract tests. Do not port `scrape.py` or `parse.py`.
- Dependencies: T1.
- Acceptance criteria:
  - `sum(weight for _,(weight,_,_) in DIMENSIONS.items()) == 100` (asserted in a test).
  - Ported unit tests for `metrics.compute`, `score.combine` bounds (0 ≤ raw ≤ 100),
    `apply_cohort_percentiles`, and `record.write_run` pass.
  - `record.write_run` raises `ValueError` for a slug in `RESERVED_SLUGS` (`index`).
  - Every dimension record carries non-empty `plain` and `tip`; `band` ∈ {g,a,r} on records
    and dimensions (asserted).
  - `pydantic` import of all `schema.py` models succeeds; a fixture record validates against
    `ProfileRecord` and a fixture index against `IndexResponse`.

**T3. Input adapter: Animal Record + Composition → `Profile`.** (Complexity: L; depends on T2)
- Scope: implement `adapt(animal_record, composition) -> Profile`, replacing `parse.py`.
  Populate `name`, `species`, `metadata` facets, `tags` (kids/dogs/cats → label), the 8
  `sections`, and `photo_count` from Evermore's normalized data. Resolve decision D2 (does
  the grader score a Composition, a draft, or Animal Record narrative fields) before building.
- Out of scope: the persistence of scores (T4).
- Dependencies: T2; decision D2 resolved.
- Acceptance criteria:
  - Given a fixture Animal Record + Composition, `adapt(...)` returns a `Profile` whose
    `sections` has the expected 8 keys, `tags` is a `dict[str,str]`, and `photo_count`,
    `species`, `age_months`, `weight_lbs` match the fixture (asserted field-by-field).
  - The full pipeline runs on the adapter output with a stubbed judge and produces a record
    that validates against `ProfileRecord` (integration test, no network).
  - No module under `src/grader/` imports Firecrawl or performs an HTTP fetch (grep-asserted
    in a test or a CI check).

**T4. Supabase-backed `Store` + Alembic migration + org scoping.** (Complexity: L; depends on T2)
- Scope: `SupabaseStore` implementing the `Store` Protocol against Postgres (SQLAlchemy async
  / asyncpg); Alembic migration for the results schema; write path from `record.write_run`
  output into Postgres; RLS policy scoping records to the org.
- Dependencies: T2.
- Acceptance criteria:
  - Alembic `upgrade head` applies cleanly on a fresh test database and `downgrade` reverses it.
  - `SupabaseStore.get_index()` and `get_record(slug)` return the same shapes `FileStore` does
    (a contract test runs the same assertions against both stores over identical seed data).
  - An RLS policy exists on the results table(s); a query as org A cannot read org B's record
    (integration test against the test db).
  - Writing a scored batch then reading it back reproduces the records byte-for-equivalent at
    the contract level (round-trip test).

**T5. Route the judge through Cloudflare AI Gateway.** (Complexity: M; depends on T2)
- Scope: construct the Anthropic client with the AI Gateway base URL + key from config; keep
  run-N-average, spread, and the tag/body hard cap. Model id from config.
- Dependencies: T2.
- Acceptance criteria:
  - The judge client's base URL is read from config; a test with a mocked gateway asserts the
    request is issued against the configured base URL, not the default Anthropic endpoint.
  - Existing judge unit tests (spread computation, hard-cap capping `observed_not_promised` at
    2 on majority contradiction) pass unchanged against the mocked client.
  - No API key is present in the diff (security-review + a secret-scan CI check).

**T6. Port the API routes with auth, tightened CORS, typed responses.** (Complexity: M; depends on T4)
- Scope: port `/api/index` and `/api/profile/{slug}` with `response_model`; back them with
  `SupabaseStore`; add Supabase Auth; pass real `cors_origins` from config; retain the slug
  regex + reserved-slug 400 guard.
- Dependencies: T4 (store), T1 (auth/config scaffolding).
- Acceptance criteria:
  - `GET /api/index` and `GET /api/profile/{slug}` with a valid token return 200 and payloads
    that validate against `IndexResponse` / `ProfileRecord` (a 200 through `response_model`
    proves validation).
  - Unauthenticated request → 401.
  - Reserved slug `index` → 400; malformed slugs (`Rex`, `a.b`, `a_b`, `a..b`) → 400; unknown
    valid-shaped slug → 404.
  - Preflight from a non-allowed origin is rejected; from an allowed origin, permitted
    (CORS test).
  - Ported `tests/test_server.py` assertions pass against the new app.

**T7. SvelteKit grader view on design-system tokens.** (Complexity: L; depends on T6)
- Scope: rebuild the dashboard as a SvelteKit route (Svelte 5 runes, Skeleton v4) consuming
  `/api/*` and `packages/design-system/` tokens. Reproduce the landing (ranked banded bars +
  study-these + flag markers + name-click and dropdown navigation) and the detail (flags,
  fix-first callout, criteria ordered by recoverable points, banded percentage grade,
  expandable rationale/quote/tip). Resolve decision D3 (stacker route vs. new app) first.
- Dependencies: T6; decision D3 resolved.
- Acceptance criteria:
  - Rendered against a fixture API response, the landing lists profiles in descending `raw`
    order and the band color matches `bands.score` (component test asserts order + class).
  - A flagged profile shows the ⚑ marker regardless of its band (test).
  - Clicking an animal name and selecting it from the dropdown both navigate to the same
    detail route (test).
  - Interpolated copy is HTML-escaped and any URL is http(s)-validated before use (a test
    feeds a `<script>`/`javascript:` payload and asserts it is neutralized).
  - The page makes no request to an external host (design-system tokens are vendored; a build
    or test check asserts no external asset URLs).

**T8. Promptfoo eval suite for the judge in CI.** (Complexity: M; depends on T5)
- Scope: a Promptfoo config with anchor cases pinning the rubric's counterintuitive core, wired
  into GitHub Actions.
- Dependencies: T5.
- Acceptance criteria:
  - `promptfoo eval` runs in CI on the judge.
  - At least one anchor case asserts a known-emotional, superlative-heavy profile scores ≤ 2 on
    `analytic_language`, and one asserts a concrete behavior-first profile scores ≥ 3.
  - At least one case asserts the tag/body contradiction caps `observed_not_promised` at 2.
  - The CI job fails if an anchor assertion regresses.

**T9. Fold `DIMENSIONS` + `DIMENSION_HELP` into one registry.** (Complexity: S; pre-port cleanup, depends on T2)
- Scope: collapse the two parallel structures in `score.py` into a single dataclass registry
  (id, label, weight, method, plain, tip) so adding a dimension is a one-place change. Update
  `record.py`, `judge.py`, and `schema` consumers.
- Dependencies: T2.
- Acceptance criteria:
  - A single registry is the only definition of dimension metadata (grep asserts
    `DIMENSION_HELP` is gone).
  - Weights still sum to 100; all ported tests pass unchanged.
  - Adding a tenth dimension in a scratch test requires editing exactly one structure
    (demonstrated by the diff in the PR description; reviewer-verified).

---

## 9. Decisions to resolve before or during the pipeline

These are architectural forks the pipeline should not guess. Recommended answers given; the
operator confirms.

**D1. Standalone `services/grader/` vs. a capability inside `services/biowriter`.**
Recommendation: **standalone service.** The grader has a distinct API contract and scores
adoption copy regardless of who wrote it (human or Biowriter), so coupling it to the generator
narrows its use. Biowriter can call the grader's API. Revisit only if the two share so much
data-loading that a split doubles the Animal-Record plumbing.

**D2. What the grader scores: a Composition, an in-progress draft, or Animal Record narrative
fields.** Recommendation: **a Composition (or a draft in the same shape).** The rubric scores
marketing prose, which is Composition content in the spine, not raw Animal Record data. The
adapter (T3) pulls facets from the Animal Record and prose from the Composition. Confirm the
Composition data model exposes the eight narrative sections (or map its fields to them).

**D3. The view: a route inside `apps/stacker` vs. a new SvelteKit app.** Recommendation:
**a route inside the existing portal** (`apps/stacker`) so the grader shares navigation, auth,
and the Skeleton theme mapping, unless the platform's app-boundary conventions call for a
separate app.

**D4. Module and env naming.** Recommendation: package `grader`, env prefix `GRADER_`, FastAPI
title "Profile Grader", following the `petdata` precedent. Confirm the name does not collide
with an existing or planned module.

---

## 10. Reference pointers

- Prototype source: this directory (`adoption-profiles/profile-grader/`).
- Rubric detail (anchors, normalization, calibration hook): `rubric.md`.
- Contract: `schema.py`. Server + `Store` seam: `server.py`. Records: `record.py`.
- Migration summary this expands: `MIGRATION.md`.
- Evermore canon: `docs/evermore-vision-and-architecture.md`; ADRs 0022 (monorepo), 0023
  (GitHub-native tracking), 0024 (tech-stack standard), 0025 (petdata Postgres+pgvector), 0031
  (shared design system).
- Research backing: Markowitz (2019), *J. Applied Social Psychology*; Kelling et al. (2024),
  *Society & Animals*.
