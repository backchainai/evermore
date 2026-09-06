"""Deterministic scoring pass.

Computes the objective rubric dimensions (no LLM judgment): social-word density,
adopter-screening language, brevity, photo count. Also collects the compliance flags and the
counts that are fed to the judge as context so it never has to guess at a number.
Section completeness is judged from content in the judge pass, not counted here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import lexicons
from .parse import BODY_SECTIONS, Profile


# Markdown image and link syntax, and bare URLs. Stripped before counting words:
# the gallery markup that trails a section is markup, not prose, and every URL token
# ("wp", "content", "uploads", "jpg", each path segment) otherwise counts as a word.
# Moose scored 523 body words against a 190-word narrative on the strength of 33
# gallery images alone, which cost him full marks on brevity.
_IMAGE_MD = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_MD = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_BARE_URL = re.compile(r"https?://\S+|www\.\S+")


def strip_markup(text: str) -> str:
    """Drop image markup and link targets, keeping link text.

    Link *text* is prose the writer chose and stays in the count; the URL behind it
    does not. Images carry no prose, so alt text goes too: it is almost always
    boilerplate ("Animal image") supplied by the gallery rather than by a writer.
    """
    text = _IMAGE_MD.sub(" ", text)
    text = _LINK_MD.sub(r"\1", text)
    text = _BARE_URL.sub(" ", text)
    return text


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", strip_markup(text)))


def lexicon_hits(text: str, phrases: list[str]) -> list[str]:
    """Case-insensitive, word-boundary matches. Returns matched phrases (with repeats)."""
    hits: list[str] = []
    low = text.lower()
    for p in phrases:
        # \b works for alnum edges; phrases here are alnum/space so this is safe.
        for _ in re.finditer(r"\b" + re.escape(p) + r"\b", low):
            hits.append(p)
    return hits


def _social_score(rate_per_100: float) -> int:
    if rate_per_100 == 0:
        return 4
    if rate_per_100 < 1:
        return 3
    if rate_per_100 <= 2:
        return 2
    if rate_per_100 <= 3:
        return 1
    return 0


def _adopter_condition_score(n: int) -> int:
    """Scores adopter-screening phrases only.

    Placement constraints ("only dog", "no cats") are counted separately and never
    scored: they are true attributes the shelter system already publishes as structured
    filters, so stating them in the copy costs the animal nothing. See lexicons.py.
    """
    if n == 0:
        return 4
    if n == 1:
        return 2
    return 0


def _brevity_score(words: int) -> int:
    """250-word target, with a floor at 175.

    The floor is the change that matters. The old bands handed 4/4 to anything from
    50 words up, which rewarded profiles that were short because they were empty: the
    sub-250 band carries the cohort's worst behavioral concreteness (1.67/4) apart
    from Moose, who covers all four sections and a full disclosure in 190 words.
    """
    if words < 175:
        return 1  # too thin to inform a decision
    if words <= 250:
        return 4
    if words <= 350:
        return 3
    if words <= 450:
        return 2
    if words <= 550:
        return 1
    return 0


def _photo_score(n: int) -> int:
    """Targets 3-5 embedded photos rather than rewarding raw volume.

    Volume was the wrong target. Petfinder carries 5 slides and Adopt-a-Pet fewer, so
    a 33-image FOHA gallery is invisible to most adopters, and Markowitz's Study 1
    found more photos associated with *longer* listings (only Study 2 pointed the
    other way). Above the target the taper is gentle: extra photos dilute the set
    without misinforming anyone.
    """
    if n == 0:
        return 0
    if n <= 2:
        return 2
    if n <= 5:
        return 4
    if n <= 10:
        return 3
    return 2


@dataclass
class Metrics:
    body_words: int
    photo_count: int
    sections_present: int
    social_hits: list[str] = field(default_factory=list)
    adopter_condition_hits: list[str] = field(default_factory=list)
    # Reported, not scored. Present so a reviewer can see the constraint set at a glance
    # and ask whether the record supports each one.
    placement_constraint_hits: list[str] = field(default_factory=list)
    absolute_claim_hits: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    # Deterministic dimension scores (0-4), keyed by rubric dimension id.
    scores: dict[str, int] = field(default_factory=dict)

    @property
    def social_rate_per_100(self) -> float:
        return (len(self.social_hits) / self.body_words * 100) if self.body_words else 0.0


def compute(profile: Profile) -> Metrics:
    # Every text dimension reads the same stripped prose, so a phrase buried in an
    # image URL can neither inflate the word count nor register as a lexicon hit.
    body = strip_markup(profile.body_text)
    words = word_count(body)
    present = sum(1 for k in BODY_SECTIONS if profile.sections.get(k))

    social = lexicon_hits(body, lexicons.SOCIAL_WORDS)
    conditions = lexicon_hits(body, lexicons.ADOPTER_CONDITION_PHRASES)
    constraints = lexicon_hits(body, lexicons.PLACEMENT_CONSTRAINT_PHRASES)
    absolute = lexicon_hits(body, lexicons.ABSOLUTE_CLAIM_PHRASES)

    m = Metrics(
        body_words=words,
        photo_count=profile.photo_count,
        sections_present=present,
        social_hits=social,
        adopter_condition_hits=conditions,
        placement_constraint_hits=constraints,
        absolute_claim_hits=absolute,
    )

    m.scores = {
        "no_social_words": _social_score(m.social_rate_per_100),
        "no_gatekeeping": _adopter_condition_score(len(conditions)),
        "brevity": _brevity_score(words),
        "photos": _photo_score(profile.photo_count),
    }

    # section_completeness and the missing_struggles flag are judged from content in the
    # judge pass (see judge.topic_coverage) and applied in score.combine(), not counted
    # from parsed section labels here. sections_present remains as an informational parse
    # metric only. Compliance flags below are reported, not scored into the total.
    if absolute:
        m.flags.append("absolute_claim")

    return m
