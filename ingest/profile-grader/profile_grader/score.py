"""Combine deterministic + judge scores into the normalized 0-100 result.

See rubric.md for weights and rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .judge import JudgeResult
from .metrics import Metrics
from .parse import Profile

# Bump when the weights or anchors below change, so records carry the rubric they
# were scored under and the dashboard can flag cross-version comparisons.
# 1.1: section_completeness moved from deterministic label-counting to judged topic
# coverage (content-based); missing_struggles now judged from topic_coverage.
# 1.2: no_gatekeeping scores adopter-screening language only; placement constraints
# ("only dog", "no cats") are reported, not scored. Housebreaking became a credit-only
# topic in section_completeness. Both changes stop the rubric penalizing a profile for
# the absence of information rather than the quality of what it states.
# 1.3: word_count strips markdown image/link markup (a 33-image gallery was adding ~330
# phantom words); brevity gains a 175-word floor and drops 5 -> 2 weight, the freed
# points going to behavioral_concreteness; photos target 3-5 editorial images instead of
# rewarding raw volume, and no longer count the injected volunteer carousel, which was
# the only thing the dimension had ever counted. Brevity correlated +0.03 with the other dimensions across the
# 62-profile cohort, so it was buying almost nothing at weight 5, and it is the one
# dimension a writer can improve by deleting content.
RUBRIC_VERSION = "1.3"

# Dimension id -> (weight, human label, method). Weights sum to 100.
DIMENSIONS: dict[str, tuple[int, str, str]] = {
    "analytic_language": (20, "Analytic vs. narrative language", "judge"),
    "behavioral_concreteness": (18, "Behavioral concreteness", "judge"),
    "observed_not_promised": (15, "Observed, not promised", "judge"),
    "no_social_words": (10, "No social / humanizing words", "deterministic"),
    # Key kept stable so stored records and the dashboard keep resolving; the label and
    # the lexicon behind it now cover adopter screening only.
    "no_gatekeeping": (10, "No adopter screening language", "deterministic"),
    "identity_opening": (5, "Identity-forward opening", "judge"),
    "section_completeness": (10, "Section completeness", "judge"),
    "brevity": (2, "Brevity", "deterministic"),
    "photos": (10, "Photo count", "deterministic"),
}

DETERMINISTIC_DIMS = tuple(d for d, (_, _, m) in DIMENSIONS.items() if m == "deterministic")

# Score interpretation bands. Single source of truth: emitted into index.json so the
# dashboard (and the future SvelteKit platform view) render bands from data rather than
# hardcoding thresholds. `score` bands apply to the 0-100 raw total; `dimension` bands
# apply to a 0-4 per-dimension score. Ordered high to low; first matching `min` wins.
SCORE_BANDS: list[dict] = [
    {"key": "g", "label": "Reference-worthy", "min": 65},
    {"key": "a", "label": "Needs work", "min": 45},
    {"key": "r", "label": "Needs rewrite", "min": 0},
]
DIM_BANDS: list[dict] = [
    {"key": "g", "min": 3.0},
    {"key": "a", "min": 2.0},
    {"key": "r", "min": 0.0},
]


def score_band(raw: float) -> str:
    """Band key ('g'/'a'/'r') for a 0-100 raw score."""
    for b in SCORE_BANDS:
        if raw >= b["min"]:
            return str(b["key"])
    return "r"


def dim_band(score: float) -> str:
    """Band key ('g'/'a'/'r') for a 0-4 dimension score."""
    for b in DIM_BANDS:
        if score >= b["min"]:
            return str(b["key"])
    return "r"

# Novice-facing gloss for each dimension: (plain, tip). `plain` says what the dimension
# measures in one plain-language question; `tip` says how to improve it, framed as what
# the research prefers rather than what the writer did wrong. Kept parallel to DIMENSIONS
# (not folded into the tuple) so the positional unpacks above stay stable.
DIMENSION_HELP: dict[str, tuple[str, str]] = {
    "analytic_language": (
        "Does it read like a factual profile or an emotional story?",
        "Trade adjectives and feelings for observed facts. The research finds "
        "“knows sit and walks on a loose leash” places faster than "
        "“a sweet, loving soul looking for her person.”",
    ),
    "behavioral_concreteness": (
        "Are traits shown through specific behavior, or just asserted?",
        "Replace personality labels with what the animal actually does. "
        "“Settles on his bed when guests arrive” beats “well-mannered.”",
    ),
    "observed_not_promised": (
        "Does it stick to what has been seen, or promise the future?",
        "State observations, not guarantees. “Has played well with the dogs he has "
        "met” beats “great with all dogs.” Unknowns are fine: say "
        "“Unknown,” not a promise.",
    ),
    "no_social_words": (
        "Does it lean on humanizing pet-words?",
        "Cut words like “buddy,” “sweetheart,” “best friend,” "
        "“companion.” Name the behavior instead of the sentiment.",
    ),
    "no_gatekeeping": (
        "Does it put conditions on the adopter?",
        "Drop screening language like “fenced yard required,” “experienced owners "
        "only,” “serious inquiries only.” State the observation behind the rule "
        "instead: “jumped a 4-foot fence in the yard” beats “fenced yard required.” "
        "Constraints that are true of the animal (“only dog,” “no cats”) are not "
        "screening language and are not penalized: keep them so adopters can find the "
        "right fit.",
    ),
    "identity_opening": (
        "Does the first line say who this animal is?",
        "Open on identity and behavior, not stats or a plea. Lead with the dog, "
        "not “This 3-year-old is looking for a forever home.”",
    ),
    "section_completeness": (
        "Does the copy cover the seven expected topics?",
        "Cover every topic: About, Dogs, Cats, Kids, Training, Likes, Struggles. It "
        "counts whether the topic is addressed in a labeled section or in plain prose. "
        "Where a compatibility fact is unknown, write “Unknown” rather than omitting "
        "it; “Unknown” is complete information, not a gap. Housebreaking is scored as "
        "credit only: a shelter rarely knows it, so its absence costs nothing, and a "
        "known-house-trained animal earns the mention.",
    ),
    "brevity": (
        "Is it tight, or padded?",
        "Aim for 175 to 250 words: that range earns full marks. Cut repetition and "
        "filler, but keep the concrete behavioral details; a profile under 175 words "
        "scores as low as a padded one, because short here usually means empty.",
    ),
    "photos": (
        "Are there the right number of photos?",
        "Aim for three to five clear, well-lit shots on the profile itself: that range "
        "earns full marks. One or two is too few to reduce an adopter's uncertainty. "
        "The volunteer photo carousel does not count and does not syndicate, so a full "
        "carousel is not a substitute for putting photos on the profile.",
    ),
}


@dataclass
class FixItem:
    dimension: str
    label: str
    recoverable: float  # points recoverable if lifted to 4
    current: float


@dataclass
class ProfileScore:
    slug: str
    name: str
    url: str
    species: str
    dim_scores: dict[str, float]  # 0-4 per dimension
    raw: float  # 0-100
    flags: list[str]
    judge: JudgeResult
    metrics: Metrics
    cohort_key: str = ""
    cohort_size: int = 0
    cohort_percentile: float | None = None
    fix_list: list[FixItem] = field(default_factory=list)


def combine(profile: Profile, metrics: Metrics, judge: JudgeResult) -> ProfileScore:
    dim_scores: dict[str, float] = {}
    for dim in DIMENSIONS:
        if dim in metrics.scores:
            dim_scores[dim] = float(metrics.scores[dim])
        else:
            dim_scores[dim] = float(judge.scores[dim])

    raw = sum(DIMENSIONS[d][0] * dim_scores[d] / 4 for d in DIMENSIONS)

    flags = list(metrics.flags)
    if judge.tag_body_contradiction and "tag_body_contradiction" not in flags:
        flags.append("tag_body_contradiction")
    # missing_struggles is judged from content: the profile discloses no struggle anywhere,
    # not merely that a labeled "Struggles" section is absent.
    if judge.topic_coverage.get("struggles") == "absent" and "missing_struggles" not in flags:
        flags.append("missing_struggles")

    fixes = [
        FixItem(
            dimension=d,
            label=DIMENSIONS[d][1],
            recoverable=DIMENSIONS[d][0] * (4 - dim_scores[d]) / 4,
            current=dim_scores[d],
        )
        for d in DIMENSIONS
    ]
    fixes = sorted((f for f in fixes if f.recoverable > 0), key=lambda f: -f.recoverable)

    return ProfileScore(
        slug=profile.slug,
        name=profile.name,
        url=profile.url,
        species=profile.species,
        dim_scores=dim_scores,
        raw=round(raw, 1),
        flags=flags,
        judge=judge,
        metrics=metrics,
        fix_list=fixes,
    )


def apply_cohort_percentiles(scores: list[ProfileScore]) -> None:
    """Set cohort_key/size/percentile in place, ranking within species cohorts.

    Copy quality norms and the temperament-tag structure differ by species, so a dog's
    percentile is computed only against other dogs. The 0-100 raw score is absolute and
    unaffected; the percentile is context.
    """
    by_species: dict[str, list[ProfileScore]] = {}
    for s in scores:
        by_species.setdefault(s.species, []).append(s)

    for species, group in by_species.items():
        n = len(group)
        for s in group:
            s.cohort_key = f"species={species}"
            s.cohort_size = n
            if n <= 1:
                s.cohort_percentile = 100.0
            else:
                lower = sum(1 for o in group if o.raw < s.raw)
                s.cohort_percentile = round(100 * lower / (n - 1), 0)
