"""LLM-as-judge pass for the qualitative rubric dimensions.

Scores the four dimensions that require reading (analytic language, behavioral
concreteness, observed-not-promised, identity-forward opening) and detects the
tag-vs-body contradiction. The judge is given the deterministic counts so it never
guesses at a number. Runs N times and averages; run-to-run spread is reported so
ambiguous profiles get flagged for human spot-check.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

import anthropic

from .metrics import Metrics
from .parse import BODY_SECTIONS, Profile

# Parsed-section keys whose display name in the judge prompt is not just the key
# uppercased. "others" holds dogs, cats, and kids, which the template puts in one section.
_SECTION_LABEL = {"others": "WITH DOGS, CATS, AND KIDS"}

DEFAULT_MODEL = "claude-sonnet-5"

JUDGE_DIMENSIONS = (
    "analytic_language",
    "behavioral_concreteness",
    "observed_not_promised",
    "identity_opening",
)

# The eight topics an adoption profile should cover. Coverage is judged from the CONTENT,
# not from whether a labeled section exists: a free-prose profile can cover "dogs" inside
# its opening paragraph. section_completeness is derived from these coverage judgments
# rather than counted from parsed section labels.
TOPIC_KEYS = (
    "about",
    "dogs",
    "cats",
    "kids",
    "training",
    "housebreaking",
    "likes",
    "struggles",
)
# Topics whose absence is not a defect in the copy. A shelter almost never learns whether
# an animal is house-trained or crate-trained, so absence is the default state of the
# record rather than something the writer left out. Scoring it against every profile
# docks the whole cohort an eighth of a 10-point dimension for a fact that does not
# exist, and makes cohort_report name it a systemic template weakness. Coverage is still
# reported, because a known-house-trained animal is a selling point worth writing down.
# It earns no points: covering the seven required topics already scores 4/4, so the only
# thing an eighth term could do is let credit here paper over a genuine miss elsewhere.
UNSCORED_TOPIC_KEYS = ("housebreaking",)
REQUIRED_TOPIC_KEYS = tuple(t for t in TOPIC_KEYS if t not in UNSCORED_TOPIC_KEYS)

_COVERAGE_STATUSES = ("covered", "brief", "absent")
_COVERAGE_WEIGHT = {"covered": 1.0, "brief": 0.5, "absent": 0.0}
_TOPIC_LABEL = {
    "about": "About",
    "dogs": "Dogs",
    "cats": "Cats",
    "kids": "Kids",
    "training": "Training",
    "housebreaking": "Housebreaking",
    "likes": "Likes",
    "struggles": "Struggles",
}


def _norm_status(v: object) -> str:
    """Coerce a judge-reported coverage value to a known status; unknown -> 'absent'."""
    s = str(v).strip().lower()
    return s if s in _COVERAGE_WEIGHT else "absent"


def _coverage_score(tc: dict[str, str]) -> int:
    """0-4 section_completeness from per-topic coverage (covered=1, brief=0.5, absent=0).

    Scored over REQUIRED_TOPIC_KEYS only. UNSCORED_TOPIC_KEYS are still reported in
    topic_coverage but contribute nothing either way.
    """
    total = sum(_COVERAGE_WEIGHT[_norm_status(tc.get(t, "absent"))] for t in REQUIRED_TOPIC_KEYS)
    return round(4 * total / len(REQUIRED_TOPIC_KEYS))

_SYSTEM = """You grade shelter-dog adoption profiles against peer-reviewed research \
(Markowitz 2019, 680k Petfinder ads; Kelling et al. 2024). The counterintuitive core \
finding: analytic, factual, behavior-first copy places animals faster than emotional, \
anthropomorphizing copy. You score only the four qualitative dimensions below on a 0-4 \
integer scale, using the anchors exactly. You never reward hiding a problem: disclosing \
a struggle factually is good; the defect is emotional or promissory framing, not the \
disclosure itself. Be a calibrated, consistent grader.

ANCHORS

analytic_language (register): 4 = consistently concrete/factual, articles & prepositions, \
specific attributes, no superlatives. 2 = even mix of factual and story/emotional. \
0 = pure storytelling, superlative-heavy ("adorable," "so much love"), little verifiable content.

behavioral_concreteness: 4 = claims are observable behaviors ("knows sit," "pulls slightly \
on leash," "no accidents in two weeks"). 2 = equal mix of behavior and personality adjectives \
("sweet," "gentle"). 0 = adjectives only, nothing an adopter could verify.

observed_not_promised: 4 = every claim is past/observed, unknowns stated as unknown, no \
guarantees. 2 = some future promises or absolute claims mixed in. 0 = built on promises or \
contradicts its own disclosures. HARD CAP: if a temperament tag asserts a trait the body \
calls unknown or contradicts (e.g. tag "Good with Kids" but body says "Unknown"), this \
dimension is capped at 2.

identity_opening (first sentence only): 4 = opens on who the animal is or a concrete vivid \
behavior. 2 = opens on a generic personality adjective. 0 = opens on raw statistics, breed, \
or medical status.

For each dimension give the integer score, a one-sentence rationale, and the single verbatim \
quote from the profile that most drove the score. Also report whether a temperament tag \
contradicts the body.

TOPIC COVERAGE (separate from the four scores above)

Judge whether the profile's CONTENT addresses each of eight topics, regardless of whether a \
labeled section for it exists. A profile written as free prose can cover a topic inside its \
opening paragraph; a labeled section left blank or filled only with "Unknown" does not cover \
its topic. Base the judgment on what the text actually says about the animal, not on section \
structure. For each topic report a status:
- covered: the text substantively addresses this topic (a stated fact, behavior, or an \
explicit "untested"/"unknown" disclosure all count as covered).
- brief: the topic is touched only glancingly, a fragment with little information.
- absent: the text says nothing about this topic.
The eight topics: about (who the animal is), dogs (behavior with other dogs), cats (behavior \
with cats), kids (behavior with children), training (commands/skills known), housebreaking \
(house-training and crating), likes (what the animal enjoys), struggles (difficulties, \
dislikes, or things being worked on). A factual "unknown"/"untested" disclosure is covered, \
not absent: stating a compatibility is untested is complete information.

Report housebreaking honestly as absent when the copy says nothing about it. A shelter \
rarely knows an animal's house-training history, so absence there is expected and is not \
scored against the profile; do not mark it brief or covered out of charity."""

_TOOL = {
    "name": "record_scores",
    "description": "Record the four dimension scores and the tag/body contradiction check.",
    "input_schema": {
        "type": "object",
        "properties": {
            dim: {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 4},
                    "rationale": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["score", "rationale", "quote"],
            }
            for dim in JUDGE_DIMENSIONS
        }
        | {
            "tag_body_contradiction": {
                "type": "object",
                "properties": {
                    "present": {"type": "boolean"},
                    "note": {"type": "string"},
                },
                "required": ["present", "note"],
            },
            "topic_coverage": {
                "type": "object",
                "description": "For each of the eight topics, whether the CONTENT covers it.",
                "properties": {
                    topic: {"type": "string", "enum": list(_COVERAGE_STATUSES)}
                    for topic in TOPIC_KEYS
                },
                "required": list(TOPIC_KEYS),
            },
        },
        "required": [*JUDGE_DIMENSIONS, "tag_body_contradiction", "topic_coverage"],
    },
}


@dataclass
class JudgeResult:
    scores: dict[str, float]  # averaged across runs
    score_runs: dict[str, list[int]]
    rationales: dict[str, str]
    quotes: dict[str, str]
    tag_body_contradiction: bool
    contradiction_note: str
    spread: dict[str, int]  # max-min per dimension across runs
    topic_coverage: dict[str, str] = field(default_factory=dict)  # topic -> covered/brief/absent

    @property
    def max_spread(self) -> int:
        return max(self.spread.values(), default=0)


def _render_input(profile: Profile, metrics: Metrics) -> str:
    tag_lines = "\n".join(f"  {k}: {v}" for k, v in profile.tags.items()) or "  (none)"
    section_lines = "\n".join(
        f"**{_SECTION_LABEL.get(k, k.upper())}**: {profile.sections.get(k, '(missing)')}"
        for k in BODY_SECTIONS
    )
    return f"""PROFILE: {profile.name} ({profile.slug})

Temperament tags (structured dropdown fields, not prose):
{tag_lines}

Opening sentence (score identity_opening on THIS only):
{profile.opening_sentence or "(none)"}

Narrative sections:
{section_lines}

Deterministic context (already measured; do not re-count):
- body word count: {metrics.body_words}
- photos: {metrics.photo_count}
- social/humanizing words found: {metrics.social_hits or "none"}
- adopter-screening phrases found: {metrics.adopter_condition_hits or "none"}
- placement constraints stated (reported, NOT a defect): {metrics.placement_constraint_hits or "none"}
- narrative absolute-claim phrases found: {metrics.absolute_claim_hits or "none"}

Score the four dimensions, check tag/body contradiction, and assess topic_coverage for all \
eight topics from the content above. Call record_scores."""


def _is_valid(raw: dict) -> bool:
    """The model occasionally deviates from the tool schema; reject malformed runs."""
    for d in JUDGE_DIMENSIONS:
        v = raw.get(d)
        if not isinstance(v, dict) or not isinstance(v.get("score"), (int, float)):
            return False
    tb = raw.get("tag_body_contradiction")
    if not (isinstance(tb, dict) and "present" in tb):
        return False
    tc = raw.get("topic_coverage")
    return isinstance(tc, dict) and all(t in tc for t in TOPIC_KEYS)


def _one_run(client: anthropic.Anthropic, model: str, prompt: str) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "record_scores"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("judge did not return a tool_use block")


def _valid_run(client: anthropic.Anthropic, model: str, prompt: str, retries: int = 3) -> dict:
    """Return one schema-valid run, retrying on the model's occasional malformed output."""
    last = None
    for _ in range(retries):
        last = _one_run(client, model, prompt)
        if _is_valid(last):
            return last
    raise RuntimeError(f"judge returned malformed output after {retries} tries: {last!r}")


def judge_profile(
    profile: Profile,
    metrics: Metrics,
    runs: int = 1,
    model: str = DEFAULT_MODEL,
    client: anthropic.Anthropic | None = None,
) -> JudgeResult:
    client = client or anthropic.Anthropic()
    prompt = _render_input(profile, metrics)

    raw_runs: list[dict] = [_valid_run(client, model, prompt) for _ in range(runs)]

    score_runs: dict[str, list[int]] = {d: [] for d in JUDGE_DIMENSIONS}
    for r in raw_runs:
        for d in JUDGE_DIMENSIONS:
            score_runs[d].append(int(r[d]["score"]))

    contradictions = [bool(r["tag_body_contradiction"]["present"]) for r in raw_runs]
    majority_contra = sum(contradictions) > len(contradictions) / 2

    scores = {d: statistics.mean(score_runs[d]) for d in JUDGE_DIMENSIONS}
    # Enforce the hard cap: contradiction caps observed_not_promised at 2.
    if majority_contra:
        scores["observed_not_promised"] = min(scores["observed_not_promised"], 2.0)

    # Topic coverage: per-topic majority status across runs, and section_completeness
    # derived from it. section_completeness is judged (from content), not counted from
    # parsed labels, so it flows through the judge score dicts like any other judge dim.
    tc_runs = [{t: _norm_status(r["topic_coverage"].get(t)) for t in TOPIC_KEYS} for r in raw_runs]
    topic_coverage = {
        t: statistics.mode([tc[t] for tc in tc_runs]) for t in TOPIC_KEYS
    }
    cov_runs = [_coverage_score(tc) for tc in tc_runs]
    score_runs["section_completeness"] = cov_runs
    scores["section_completeness"] = statistics.mean(cov_runs)

    first = raw_runs[0]
    contra_note = next(
        (r["tag_body_contradiction"]["note"] for r in raw_runs if r["tag_body_contradiction"]["present"]),
        first["tag_body_contradiction"]["note"],
    )

    rationales = {d: first[d]["rationale"] for d in JUDGE_DIMENSIONS}
    quotes = {d: first[d]["quote"] for d in JUDGE_DIMENSIONS}
    rationales["section_completeness"] = _coverage_rationale(topic_coverage)
    quotes["section_completeness"] = ""
    spread = {d: max(score_runs[d]) - min(score_runs[d]) for d in JUDGE_DIMENSIONS}
    spread["section_completeness"] = max(cov_runs) - min(cov_runs)

    return JudgeResult(
        scores=scores,
        score_runs=score_runs,
        rationales=rationales,
        quotes=quotes,
        tag_body_contradiction=majority_contra,
        contradiction_note=contra_note,
        spread=spread,
        topic_coverage=topic_coverage,
    )


def _coverage_rationale(tc: dict[str, str]) -> str:
    """One-line coverage summary for the section_completeness dimension detail."""
    buckets: dict[str, list[str]] = {s: [] for s in _COVERAGE_STATUSES}
    for t in TOPIC_KEYS:
        buckets[_norm_status(tc.get(t, "absent"))].append(_TOPIC_LABEL[t])
    parts = [f"{status}: {', '.join(labels)}" for status in _COVERAGE_STATUSES if (labels := buckets[status])]
    return "Topic coverage: " + "; ".join(parts) + "."
