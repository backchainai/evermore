# profile-grader

Grades FOHA adoption profiles against research-backed adoption-copy guidance and emits a
normalized 0-100 score per profile plus a cohort roll-up.

The scoring standard lives in [`rubric.md`](rubric.md). Every dimension traces to the
research in `../../reference/research/shelter-outcomes/` (Markowitz 2019; Kelling et al. 2024) and
the `adoption-profile-writing` skill at
`../../.claude/skills/adoption-profile-writing/`.

## How it works

```
scrape (Firecrawl) → parse → metrics (deterministic) → judge (LLM) → score → report
```

- **Deterministic pass** (`metrics.py`): social-word density, adopter-screening language, section
  completeness, brevity, photo count. No LLM, fully reproducible.
- **Judge pass** (`judge.py`): the four dimensions that require reading (analytic register,
  behavioral concreteness, observed-not-promised, identity-forward opening). Runs N times
  and averages; run-to-run spread is reported so ambiguous profiles get a human spot-check.
- **Two guardrails**: a temperament tag that contradicts the body caps *observed-not-promised*
  at 2; an empty Struggles section raises a disclosure flag. Neither can be gamed by deleting
  content, because both are reported as flags independent of the score.

## Setup

Requires the [`firecrawl`](https://docs.firecrawl.dev/) CLI on `PATH` and two env vars:

```
export FIRECRAWL_API_KEY=...   # scraping (~1 credit / profile page)
export ANTHROPIC_API_KEY=...   # the judge
```

## Usage

```bash
# Scrape 10 dogs into the local cache (data/raw/<slug>.json)
uv run grade scrape --species dog --limit 10

# Score everything cached, averaging 3 judge runs, into a report
uv run grade score --runs 3 --out data/report.md

# Or both at once
uv run grade run --species dog --limit 10 --runs 3 --out data/report.md

# Browse the scored profiles in the interactive dashboard
uv run grade serve --port 8000        # then open http://127.0.0.1:8000
```

`score` reads the cache, so scraping once lets you re-score for free while tuning the
rubric. Everything under `data/` is git-ignored and regenerated.

## Dashboard

`grade serve` runs a local FastAPI server (the durable API that ports into the Evermore
platform later, see [`MIGRATION.md`](MIGRATION.md)) with the interactive view on top:

| Route | Serves |
|---|---|
| `GET /` | The single-file dashboard (landing + per-profile detail) |
| `GET /api/index` | cohort table + rubric dimensions + band legend |
| `GET /api/profile/{slug}` | one self-contained per-profile record |
| `GET /api/docs` | OpenAPI docs for the two API routes |

Both API routes are typed by the pydantic contract in `schema.py` (used as
`response_model`, so responses are validated on the way out and documented via OpenAPI).
Data access goes through an injectable `Store`; the default `FileStore` reads the JSON
`grade score` wrote. CORS is open by default (read-only public data) so a SvelteKit dev
server works out of the box. Point at a non-default results dir with
`grade serve --data-dir <path>`.

The **landing page** ranks every profile by score, color-banded (green = reference-worthy,
amber = needs work, red = needs rewrite), and surfaces the top unflagged greens as
"study these" examples. A quality flag (⚑) shows on any profile regardless of score, so a
high scorer with a contradiction is not blindly copied. The **detail page** orders the nine
criteria by where the most points are recoverable, and each expands to the grader's
rationale, the verbatim sentence from that profile's own copy that drove the score, and a
plain-language fix. Run `grade score` first so there are records to serve.

## Outputs

Every `score` / `run` writes four things under `data/`:

| Path | What | For |
|---|---|---|
| `report.md` (via `--out`) | Human-readable scorecards + cohort roll-up | Reading |
| `results/<slug>.json` | Self-contained per-profile record: facets, section text, per-dimension scores with evidence, flags, fix list, outcome placeholders | Rendering an interactive dashboard |
| `results/index.json` | Lightweight cohort table (one row per slug) + the rubric's dimension list | The dashboard's cohort view; lazy-load records on drill-down |
| `scores.jsonl` | Append-only time series, one row per profile per run | Calibration against placement outcomes |

Records are versioned (`schema_version`, `rubric_version`) and carry null outcome
fields (`days_to_placement`, `adopted_at`, ...) so runs stay joinable as the rubric
evolves and funnel data arrives. Percentiles are computed within species cohorts
(`cohort_key`); the 0-100 raw score is absolute and cohort-independent.

## Calibration

Once ~30-50 profiles are scored, correlate the 0-100 score against actual days-to-placement
(the funnel data keyed on animal ID). Weak correlation is the signal to re-weight the rubric,
turning "graded against research" into "graded against FOHA outcomes."
