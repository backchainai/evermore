"""Phrase lexicons for the deterministic scoring pass.

Each list backs a specific rubric dimension or compliance flag. Matching is
case-insensitive on word boundaries. Keep entries lowercase.
"""

# Dimension 4: social / humanizing words. Markowitz (2019) found these correlate
# with *un*-adopted pets; adopters may read them as compensation for hidden problems.
# The bio template calls these out explicitly ("buddy," "sweetheart," "best friend").
SOCIAL_WORDS: list[str] = [
    "buddy",
    "best friend",
    "bestie",
    "companion",
    "sweetheart",
    "sweetie",
    "fur baby",
    "furbaby",
    "fur-baby",
    "baby boy",
    "baby girl",
    "soulmate",
    "soul mate",
    "cuddle bug",
    "cuddlebug",
    "snuggle bug",
    "lifelong friend",
    "forever friend",
    "little angel",
    "angel",
    "princess",
    "prince charming",
    "gentleman",
    "lady",
    "old soul",
    "love bug",
    "lovebug",
    "velcro dog",
    "shadow",
]

# Dimension 5 splits in two. Kelling et al. (2024) found that elimination criteria in a
# listing lengthen stay, and the mechanism is that a constraint shrinks the pool of
# eligible adopters. That mechanism only applies to a condition the listing itself
# invents. A constraint that is true of the animal shrinks the pool whether or not the
# copy mentions it, because ShelterLuv already carries it as a structured attribute and
# pushes it to Petfinder and Adopt-a-Pet, where it drives the search filters. Scoring the
# two the same way penalizes accurate disclosure and rewards a body that disagrees with
# the attribute panel printed beside it.

# Scored. Conditions the listing places on the applicant. Removing one costs no adopter a
# good match, because it says nothing about the animal.
ADOPTER_CONDITION_PHRASES: list[str] = [
    "must have a fenced yard",
    "must have a fenced-in yard",
    "fenced yard required",
    "fenced-in yard required",
    "requires a fenced",
    "needs a fenced",
    "qualified adopters only",
    "experienced owners only",
    "experienced adopters only",
    "experienced home only",
    "no apartments",
    "serious inquiries only",
    "not for first-time owners",
    "must apply",
]

# Counted and reported, never scored. Attributes of the animal that determine which homes
# fit. Omitting one does not widen the funnel; it only hides the reason from the adopter
# and desynchronizes the prose from the structured attributes. The useful question about
# one of these is whether the record supports it, which is provenance, not presence.
PLACEMENT_CONSTRAINT_PHRASES: list[str] = [
    "only dog",
    "only pet",
    "no children",
    "no kids",
    "no cats",
    "no other dogs",
    "adult-only home",
    "adults-only home",
    "without young children",
    "without small children",
    "without children",
]

# Dimension 3 assist: narrative future-promise / absolute-compatibility guarantees.
# These are prose guarantees, distinct from the structured temperament tags (which are
# graded via tag-vs-body contradiction, handled by the judge). "Good with X" alone is
# not listed here because it is the tag label; the phrases below are unambiguous
# narrative over-claims.
ABSOLUTE_CLAIM_PHRASES: list[str] = [
    "great with all",
    "good with everyone",
    "loves everyone",
    "loves all",
    "gets along with all",
    "gets along with everyone",
    "guaranteed",
    "will love your",
    "will be great with",
    "perfect with kids",
    "perfect family dog",
    "the perfect",
    "will do great with",
    "always friendly",
    "never aggressive",
    "100%",
]
