"""Machine-readable result records for the reporting dashboard.

Each scored profile is written as a self-contained per-slug JSON (everything needed to
render one profile's card without loading another file), plus a lightweight index.json
for the cohort table and an append-only scores.jsonl time series for calibration.

Schema is versioned and carries outcome placeholders so records from different runs stay
joinable as the rubric evolves and placement outcomes arrive.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import __version__
from .judge import REQUIRED_TOPIC_KEYS
from .parse import Profile
from .score import (
    DIM_BANDS,
    DIMENSION_HELP,
    DIMENSIONS,
    RUBRIC_VERSION,
    SCORE_BANDS,
    ProfileScore,
    dim_band,
    score_band,
)

SCHEMA_VERSION = "1.0"
MAX_RAW = 100
# Reserved in the flat results/ namespace: index.json is the cohort index, not a profile.
# An animal must not be slugged with a reserved name or its record would clobber it.
RESERVED_SLUGS = frozenset({"index"})

_FLAG_META: dict[str, tuple[str, str]] = {
    "tag_body_contradiction": ("Temperament tag contradicts the body", "high"),
    "missing_struggles": ("Discloses no struggle or difficulty (disclosure floor)", "high"),
    "absolute_claim": ("Narrative absolute-claim / guarantee language", "medium"),
}


def _dim_detail(dim: str, s: ProfileScore) -> dict:
    m, j = s.metrics, s.judge
    if dim == "section_completeness":
        # Judged from content: report the per-topic coverage map plus a covered tally.
        coverage = j.topic_coverage
        # Counted against the required topics only. Housebreaking still appears in
        # `coverage` so a reviewer sees whether it is known, but it is credit-only.
        covered = sum(
            1 for t in REQUIRED_TOPIC_KEYS if coverage.get(t) == "covered"
        )
        return {
            "coverage": coverage,
            "covered": covered,
            "expected": len(REQUIRED_TOPIC_KEYS),
            "rationale": j.rationales.get(dim, ""),
            "runs": j.score_runs.get(dim, []),
            "spread": j.spread.get(dim, 0),
        }
    if DIMENSIONS[dim][2] == "deterministic":
        if dim == "no_social_words":
            return {
                "hits": sorted(set(m.social_hits)),
                "count": len(m.social_hits),
                "rate_per_100w": round(m.social_rate_per_100, 2),
            }
        if dim == "no_gatekeeping":
            # "hits" is what the dashboard highlights as text to cut, so only the scored
            # adopter-screening phrases belong there. Placement constraints ride along
            # under their own key: reported for review, never flagged as a defect.
            return {
                "hits": sorted(set(m.adopter_condition_hits)),
                "count": len(m.adopter_condition_hits),
                "placement_constraints": sorted(set(m.placement_constraint_hits)),
            }
        if dim == "brevity":
            return {"word_count": m.body_words}
        if dim == "photos":
            return {"count": m.photo_count}
        return {}
    return {
        "rationale": j.rationales.get(dim, ""),
        "quote": j.quotes.get(dim, ""),
        "runs": j.score_runs.get(dim, []),
        "spread": j.spread.get(dim, 0),
    }


def _dimensions(s: ProfileScore) -> list[dict]:
    out = []
    for dim, (weight, label, method) in DIMENSIONS.items():
        sc = s.dim_scores[dim]
        plain, tip = DIMENSION_HELP.get(dim, ("", ""))
        out.append(
            {
                "id": dim,
                "label": label,
                "plain": plain,
                "tip": tip,
                "weight": weight,
                "method": method,
                "score": round(sc, 2),
                "band": dim_band(sc),
                "weighted_points": round(weight * sc / 4, 2),
                "recoverable_points": round(weight * (4 - sc) / 4, 2),
                "detail": _dim_detail(dim, s),
            }
        )
    return out


def _flags(s: ProfileScore) -> list[dict]:
    out = []
    for code in s.flags:
        label, severity = _FLAG_META.get(code, (code, "medium"))
        if code == "tag_body_contradiction":
            detail = s.judge.contradiction_note
        elif code == "absolute_claim":
            detail = ", ".join(sorted(set(s.metrics.absolute_claim_hits)))
        elif code == "missing_struggles":
            detail = "The copy discloses no struggle, difficulty, or dislike."
        else:
            detail = ""
        out.append({"code": code, "label": label, "severity": severity, "detail": detail})
    return out


def build_record(s: ProfileScore, p: Profile, run_ctx: dict, scraped_at: str | None) -> dict:
    meta = p.metadata
    return {
        # provenance / run identity
        "schema_version": SCHEMA_VERSION,
        "grader_version": __version__,
        "rubric_version": RUBRIC_VERSION,
        "model": run_ctx["model"],
        "judge_runs": run_ctx["judge_runs"],
        "run_id": run_ctx["run_id"],
        "scored_at": run_ctx["scored_at"],
        # source facets
        "slug": s.slug,
        "name": s.name,
        "url": s.url,
        "species": s.species,
        "breed": meta.get("breed"),
        "age_raw": meta.get("age"),
        "age_months": p.age_months,
        "sex": meta.get("sex"),
        "weight_raw": meta.get("weight"),
        "weight_lbs": p.weight_lbs,
        "color": meta.get("color"),
        "status": meta.get("status"),
        "foster_eligible": _yesno(meta.get("foster eligible")),
        "location": meta.get("location"),
        "tags": p.tags,
        "photo_count": p.photo_count,
        "body_word_count": s.metrics.body_words,
        "scraped_at": scraped_at,
        # content
        "opening_sentence": p.opening_sentence,
        "sections": {k: v for k, v in p.sections.items() if k != "fee"},
        # scores
        "raw": s.raw,
        "max_raw": MAX_RAW,
        "band": score_band(s.raw),
        "cohort_key": s.cohort_key,
        "cohort_size": s.cohort_size,
        "cohort_percentile": s.cohort_percentile,
        "dimensions": _dimensions(s),
        "flags": _flags(s),
        "fix_list": [
            {
                "dimension": f.dimension,
                "label": f.label,
                "recoverable_points": round(f.recoverable, 2),
                "current": round(f.current, 2),
            }
            for f in s.fix_list
        ],
        # outcome placeholders (filled when funnel data is joined; keep schema stable)
        "adopted": None,
        "adopted_at": None,
        "days_to_placement": None,
        "length_of_stay_days": None,
        "intake_date": None,
    }


def _yesno(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.strip().lower().startswith("y")


def _index_row(rec: dict) -> dict:
    return {
        k: rec[k]
        for k in (
            "slug", "name", "url", "species", "raw", "band", "cohort_key",
            "cohort_percentile", "age_months", "weight_lbs", "status", "foster_eligible",
            "photo_count", "body_word_count", "scored_at",
        )
    } | {"flags": [f["code"] for f in rec["flags"]]}


def _ledger_row(rec: dict) -> dict:
    row = {
        "run_id": rec["run_id"],
        "scored_at": rec["scored_at"],
        "slug": rec["slug"],
        "species": rec["species"],
        "raw": rec["raw"],
        "cohort_percentile": rec["cohort_percentile"],
        "rubric_version": rec["rubric_version"],
        "model": rec["model"],
        "flags": [f["code"] for f in rec["flags"]],
    }
    for d in rec["dimensions"]:
        row[f"dim_{d['id']}"] = d["score"]
    return row


def write_run(
    scores: list[ProfileScore],
    profiles: dict[str, Profile],
    run_ctx: dict,
    results_dir: Path,
    ledger_path: Path,
    scraped_at: dict[str, str] | None = None,
) -> Path:
    """Write per-slug records + index.json, and append every profile to the ledger."""
    collisions = sorted(s.slug for s in scores if s.slug in RESERVED_SLUGS)
    if collisions:
        raise ValueError(
            f"Reserved slug(s) {collisions} would collide with index.json in {results_dir}. "
            "Rename the source profile(s)."
        )
    results_dir.mkdir(parents=True, exist_ok=True)
    scraped_at = scraped_at or {}
    index = []
    ledger_lines = []
    for s in scores:
        rec = build_record(s, profiles[s.slug], run_ctx, scraped_at.get(s.slug))
        (results_dir / f"{s.slug}.json").write_text(
            json.dumps(rec, indent=2, ensure_ascii=False)
        )
        index.append(_index_row(rec))
        ledger_lines.append(json.dumps(_ledger_row(rec), ensure_ascii=False))

    (results_dir / "index.json").write_text(
        json.dumps(
            {
                "run_id": run_ctx["run_id"],
                "scored_at": run_ctx["scored_at"],
                "rubric_version": RUBRIC_VERSION,
                "schema_version": SCHEMA_VERSION,
                "bands": {"score": SCORE_BANDS, "dimension": DIM_BANDS},
                "dimensions": [
                    {
                        "id": d,
                        "label": lbl,
                        "plain": DIMENSION_HELP.get(d, ("", ""))[0],
                        "tip": DIMENSION_HELP.get(d, ("", ""))[1],
                        "weight": w,
                        "method": mth,
                    }
                    for d, (w, lbl, mth) in DIMENSIONS.items()
                ],
                "profiles": index,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as fh:
        for line in ledger_lines:
            fh.write(line + "\n")
    return results_dir
