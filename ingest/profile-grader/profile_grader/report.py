"""Render scorecards and the cohort roll-up as markdown."""

from __future__ import annotations

import statistics

from .parse import BODY_SECTIONS
from .score import DIMENSIONS, ProfileScore

FLAG_LABELS = {
    "missing_struggles": "Struggles/Dislikes section empty (disclosure floor)",
    "tag_body_contradiction": "Temperament tag contradicts the body",
    "absolute_claim": "Narrative absolute-claim / guarantee language",
}


def _light(score: float) -> str:
    if score >= 3.5:
        return "🟢"
    if score >= 2:
        return "🟡"
    return "🔴"


def _driver(dim: str, s: ProfileScore) -> str:
    m = s.metrics
    if dim == "no_social_words":
        hits = ", ".join(sorted(set(m.social_hits))) or "none"
        return f"{len(m.social_hits)} hit(s) ({m.social_rate_per_100:.1f}/100w): {hits}"
    if dim == "no_gatekeeping":
        return ", ".join(sorted(set(m.adopter_condition_hits))) or "none"
    if dim == "section_completeness":
        return f"{m.sections_present}/{len(BODY_SECTIONS)} sections"
    if dim == "brevity":
        return f"{m.body_words} words"
    if dim == "photos":
        return f"{m.photo_count} photos"
    # Judge dimensions: quote + rationale.
    quote = s.judge.quotes.get(dim, "").strip()
    rationale = s.judge.rationales.get(dim, "").strip()
    quote_part = f'"{quote}" — ' if quote else ""
    return f"{quote_part}{rationale}"


def profile_scorecard(s: ProfileScore) -> str:
    pct = f"{s.cohort_percentile:.0f}th pct" if s.cohort_percentile is not None else "n/a"
    lines = [
        f"## {s.name or s.slug}  —  {s.raw:.0f}/100  ({pct} in cohort)",
        f"{s.url}",
        "",
    ]

    if s.flags:
        lines.append("**Compliance flags:**")
        for f in s.flags:
            lines.append(f"- ⚠️ {FLAG_LABELS.get(f, f)}")
            if f == "tag_body_contradiction" and s.judge.contradiction_note:
                lines.append(f"  - {s.judge.contradiction_note}")
        lines.append("")

    if s.metrics.placement_constraint_hits:
        stated = ", ".join(sorted(set(s.metrics.placement_constraint_hits)))
        lines.append(
            f"**Placement constraints stated:** {stated}  \n"
            "Not scored. Check each against the record: a constraint the file does not "
            "support should come out, and one it does support should stay."
        )
        lines.append("")

    lines.append("| | Dimension | Score | Wt | What drove it |")
    lines.append("|---|---|---|---|---|")
    for dim, (wt, label, _) in DIMENSIONS.items():
        sc = s.dim_scores[dim]
        spread = s.judge.spread.get(dim)
        spread_note = f" ⚑spread {spread}" if spread and spread >= 2 else ""
        lines.append(
            f"| {_light(sc)} | {label} | {sc:.1f}/4{spread_note} | {wt} | {_driver(dim, s)} |"
        )
    lines.append("")

    if s.fix_list:
        lines.append("**Highest-value fixes** (points recoverable):")
        for f in s.fix_list[:3]:
            lines.append(f"- **+{f.recoverable:.1f}** {f.label} (now {f.current:.1f}/4)")
        lines.append("")

    if s.judge.max_spread >= 2:
        lines.append(
            "> Judge run-to-run spread ≥2 on a flagged dimension: spot-check by hand."
        )
        lines.append("")

    return "\n".join(lines)


def cohort_report(scores: list[ProfileScore]) -> str:
    ordered = sorted(scores, key=lambda s: s.raw)  # weakest first
    lines = [
        f"# FOHA Adoption Profile Grades — {len(scores)} profiles",
        "",
        f"Mean score: {statistics.mean(s.raw for s in scores):.0f}/100  ·  "
        f"Median: {statistics.median(s.raw for s in scores):.0f}/100  ·  "
        f"Range: {min(s.raw for s in scores):.0f}–{max(s.raw for s in scores):.0f}",
        "",
        "## Cohort (weakest first)",
        "",
        "| Profile | Score | Cohort pct | Flags | Top fix |",
        "|---|---|---|---|---|",
    ]
    for s in ordered:
        flags = ", ".join(s.flags) if s.flags else "—"
        top = s.fix_list[0].label if s.fix_list else "—"
        pct = f"{s.cohort_percentile:.0f}" if s.cohort_percentile is not None else "—"
        lines.append(f"| {s.name or s.slug} | {s.raw:.0f} | {pct} | {flags} | {top} |")
    lines.append("")

    # Systemic weakness: mean per dimension across the cohort.
    lines.append("## Systemic weaknesses (cohort mean per dimension)")
    lines.append("")
    lines.append("| | Dimension | Cohort mean /4 |")
    lines.append("|---|---|---|")
    dim_means = {
        dim: statistics.mean(s.dim_scores[dim] for s in scores) for dim in DIMENSIONS
    }
    for dim, mean in sorted(dim_means.items(), key=lambda kv: kv[1]):
        lines.append(f"| {_light(mean)} | {DIMENSIONS[dim][1]} | {mean:.1f} |")
    lines.append("")
    weak = [DIMENSIONS[d][1] for d, mean in dim_means.items() if mean < 2.5]
    if weak:
        lines.append(
            "Systemically weak across the cohort (mean <2.5): "
            + ", ".join(weak)
            + ". These are template/training problems, not individual ones."
        )
        lines.append("")

    exemplars = sorted(scores, key=lambda s: -s.raw)[:2]
    lines.append("## Best-in-class exemplars")
    lines.append("")
    for s in exemplars:
        lines.append(f"- **{s.name or s.slug}** ({s.raw:.0f}/100) — {s.url}")
    lines.append("")

    return "\n".join(lines)


def full_report(scores: list[ProfileScore]) -> str:
    parts = [cohort_report(scores), "", "---", "", "# Per-profile scorecards", ""]
    for s in sorted(scores, key=lambda s: -s.raw):
        parts.append(profile_scorecard(s))
        parts.append("---")
        parts.append("")
    return "\n".join(parts)
