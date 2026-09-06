"""API response contract for the dashboard.

These pydantic models are the durable interface. `server.py` uses them as
`response_model` so the shapes are validated on the way out and documented at
`/api/docs` (OpenAPI). When profile-grader folds into the Evermore platform these
models port as-is into the `services/` module and generate the client-facing schema
the SvelteKit view consumes. `record.py` still builds plain dicts; validation happens
at the boundary here (and in `tests/test_server.py`), so a drift between what
`write_run` writes and what the contract promises fails a test rather than the frontend.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Dimension(BaseModel):
    """One scored rubric dimension inside a per-profile record."""

    id: str
    label: str
    plain: str
    tip: str
    weight: int
    method: str
    score: float
    band: str
    weighted_points: float
    recoverable_points: float
    detail: dict[str, Any]


class Flag(BaseModel):
    code: str
    label: str
    severity: str
    detail: str


class FixItem(BaseModel):
    dimension: str
    label: str
    recoverable_points: float
    current: float


class ProfileRecord(BaseModel):
    """Self-contained per-profile record: everything to render one profile's detail."""

    # provenance
    schema_version: str
    grader_version: str
    rubric_version: str
    model: str
    judge_runs: int
    run_id: str
    scored_at: str
    # identity / facets
    slug: str
    name: str
    url: str | None = None
    species: str
    breed: str | None = None
    age_raw: str | None = None
    age_months: int | None = None
    sex: str | None = None
    weight_raw: str | None = None
    weight_lbs: float | None = None
    color: str | None = None
    status: str | None = None
    foster_eligible: bool | None = None
    location: str | None = None
    tags: dict[str, str] = {}  # temperament tags: kids/dogs/cats -> raw label
    photo_count: int
    body_word_count: int
    scraped_at: str | None = None
    # content
    opening_sentence: str
    sections: dict[str, str]
    # scores
    raw: float
    max_raw: int
    band: str
    cohort_key: str
    cohort_size: int
    cohort_percentile: float | None = None
    dimensions: list[Dimension]
    flags: list[Flag]
    fix_list: list[FixItem]
    # outcome placeholders (filled when funnel data is joined)
    adopted: bool | None = None
    adopted_at: str | None = None
    days_to_placement: int | None = None
    length_of_stay_days: int | None = None
    intake_date: str | None = None


class RubricDimension(BaseModel):
    """Dimension metadata in the index (no per-profile scores)."""

    id: str
    label: str
    plain: str
    tip: str
    weight: int
    method: str


class ScoreBand(BaseModel):
    key: str
    label: str | None = None
    min: float


class IndexProfile(BaseModel):
    """One row of the cohort table."""

    slug: str
    name: str
    url: str | None = None
    species: str
    raw: float
    band: str
    cohort_key: str
    cohort_percentile: float | None = None
    age_months: int | None = None
    weight_lbs: float | None = None
    status: str | None = None
    foster_eligible: bool | None = None
    photo_count: int
    body_word_count: int
    scored_at: str
    flags: list[str] = []


class IndexResponse(BaseModel):
    """Cohort table + rubric metadata + band legend."""

    run_id: str
    scored_at: str
    rubric_version: str
    schema_version: str
    bands: dict[str, list[ScoreBand]]
    dimensions: list[RubricDimension]
    profiles: list[IndexProfile]
