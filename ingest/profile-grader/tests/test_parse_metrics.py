"""Offline tests for parsing + deterministic scoring (no network, no LLM).

These guard the profile-format variants found on foha.org: emoji inside heading
bold, "THINGS I LOVE" vs "THINGS I LIKE", the DISLIKE/LIKE substring trap, and the
no-ABOUT intro-fallback layout.
"""

import json

from profile_grader import record as record_mod
from profile_grader.judge import _coverage_score
from profile_grader.metrics import compute
from profile_grader.parse import parse_age_months, parse_scrape, parse_weight_lbs
from profile_grader.score import apply_cohort_percentiles, combine


# Judge topics stay per-species: coverage is judged from content, not from headings.
_TOPICS = ("about", "dogs", "cats", "kids", "training", "housebreaking", "likes", "struggles")
# Parsed section keys. Dogs, cats, and kids share one heading and one key.
_SECTION_KEYS = ("about", "others", "training", "housebreaking", "likes", "struggles")
_JUDGE_DIM_SCORES = {
    "analytic_language": 2.0,
    "behavioral_concreteness": 3.0,
    "observed_not_promised": 4.0,
    "identity_opening": 2.0,
}


class _FakeJudge:
    """Stands in for JudgeResult. section_completeness is derived from topic_coverage the
    same way judge_profile does, so a partial-coverage fake yields a lower score."""

    tag_body_contradiction = False
    contradiction_note = ""
    max_spread = 0

    def __init__(self, topic_coverage=None):
        self.topic_coverage = topic_coverage or {t: "covered" for t in _TOPICS}
        self.scores = dict(_JUDGE_DIM_SCORES)
        self.scores["section_completeness"] = float(_coverage_score(self.topic_coverage))
        self.score_runs = {k: [int(v)] for k, v in self.scores.items()}
        self.rationales = {k: "because" for k in self.scores}
        self.quotes = {k: "a quote" for k in self.scores}
        self.spread = {k: 0 for k in self.scores}

# ABOUT heading carries an emoji inside the bold; likes uses "THINGS I LOVE".
EMOJI_MD = """# Rex

Male
•
45 lbs

- **Breed** Mixed Breed
- **Age** 3yrs

Kids - Good with Kids
Dogs - To Be Determined
Cats - To Be Determined

### Meet Rex

**🐾 ABOUT THIS ANIMAL:**

Rex walks calmly on a loose leash and knows sit. He is my favorite trail companion.

**HOW AM I WITH DOGS:**

Unknown.

**HOW AM I WITH CATS:**

Unknown.

**HOW AM I WITH KIDS:**

Unknown.

**MY TRAINING:**

Knows sit and down.

**MY HOUSEBREAKING AND/OR CRATING:**

No accidents in two weeks.

**THINGS I LOVE:**

Squeaky toys and treats.

**THINGS I STRUGGLE WITH:**

Counter surfing, but responds to redirection.

**ADOPTION FEE INCLUDES:**

Spay/neuter, vaccines.

![Rex-1](https://foha.org/wp-content/uploads/2024/07/Rex-1-540x720.jpg)![Rex-2](https://foha.org/wp-content/uploads/2024/07/Rex-2-540x720.jpg)![Rex-3](https://foha.org/wp-content/uploads/2024/07/Rex-3-540x720.jpg)
"""

# No ABOUT heading: intro sits under a "**Meet <Name>**" line. Prose contains
# "favorite" (must not be dropped as chrome) and the gatekeeping phrase "only dog".
NO_ABOUT_MD = """# Duke

Kids - To Be Determined
Dogs - To Be Determined
Cats - To Be Determined

### Meet Duke

**Meet Duke**

Duke is a happy-go-lucky companion and his favorite activity is walks. He should be the only dog in the home.

**HOW AM I WITH DOGS:**

Selective.

**THINGS I DISLIKE:**

Loud noises.

**ADOPTION FEE INCLUDES:**

Spay/neuter.
"""


# Some profiles write every section as an ATX heading ("## THINGS I DISLIKE:")
# rather than bold ("**...:**"). Sections and the struggles disclosure must still parse.
ATX_MD = """# Marz

Kids - To Be Determined
Dogs - Good with Dogs
Cats - To Be Determined

### Meet Marz

## ABOUT THIS ANIMAL:

Marz observes the room from a distance before approaching.

## HOW AM I WITH DOGS:

Comfortable around calm dogs.

## HOW AM I WITH CATS:

Untested.

## HOW AM I WITH KIDS:

Untested.

## MY TRAINING:

Knows sit.

## MY HOUSEBREAKING AND/OR CRATING:

Comfortable in a crate.

## THINGS I LIKE:

Peanut butter and sniffing in the yard.

## THINGS I DISLIKE:

Loud noises and unfamiliar people moving too quickly.

**ADOPTION FEE INCLUDES:**

Spay/neuter.
"""


# Bold headings WITHOUT a trailing colon (one real profile style), Title Case labels,
# a "?"-terminated label, and "With Other Dogs" phrasing. All must still resolve, and
# the trailing Disqus / newsletter chrome must never enter a scored section.
VARIANT_MD = """# Sal

### Meet Sal

**About This Animal**

Sal leans in for belly rubs and knows sit.

**How Am I With Other Dogs?**

Enthusiastic player who does well in playgroups.

**How Am I With Cats?**

Has not been tested around cats.

**How Am I With Kids?**

Does best with older, respectful kids.

**Training & Skills**

Knows sit, down, come.

**Housebreaking & Crating**

House-trained, signals at the door.

**Things I Like**

Hiking and fetch.

**Things I Struggle With**

Needs time to settle in new environments.

**FOHA Adoption Policies and Process**

[link]

**ADOPTION FEE INCLUDES:**

Spay/neuter.

### Disqus is a discussion network

Someone in the comments wrote gatekeeping nonsense: only dog, fenced yard required.

## Sign up for updates!
"""


def _profile(md, slug="x"):
    return parse_scrape({"markdown": md, "images": [], "metadata": {}}, slug=slug, species="dog")


def test_heading_variants_and_comment_exclusion():
    p = _profile(VARIANT_MD, "sal")
    # Bold-without-colon, Title Case, "?"-terminated, and "Other Dogs" all resolve.
    for key in _SECTION_KEYS:
        assert p.sections.get(key), f"missing section {key}"
    assert "belly rubs" in p.sections["about"]
    # Three legacy per-species headings merge into one key instead of overwriting.
    assert "playgroups" in p.sections["others"]
    # User-generated Disqus content must not leak into any scored section.
    body = p.body_text.lower()
    assert "disqus" not in body and "comments wrote" not in body
    # ...so the comment's phrases must not be attributed to the animal, in either list.
    m = compute(p)
    assert "only dog" not in m.placement_constraint_hits
    assert not any("fenced yard" in h for h in m.adopter_condition_hits)


def test_atx_heading_sections_parse():
    p = _profile(ATX_MD, "marz")
    # All six narrative sections parse from ATX ("## ...:") headings.
    for key in _SECTION_KEYS:
        assert p.sections.get(key), f"missing section {key}"
    # DISLIKE/LIKE substring trap holds under ATX too.
    assert "Loud noises" in p.sections["struggles"]
    assert "Peanut butter" in p.sections["likes"]
    # The disclosed struggle must not raise a false missing_struggles flag.
    m = compute(p)
    assert "missing_struggles" not in m.flags
    assert m.sections_present == len(_SECTION_KEYS)


def test_emoji_heading_and_love_variant():
    p = _profile(EMOJI_MD, "rex")
    assert p.name == "Rex"
    # ABOUT (emoji heading) and LIKES ("THINGS I LOVE") both parse.
    assert p.sections.get("about", "").startswith("Rex walks calmly")
    assert "Squeaky toys" in p.sections.get("likes", "")
    # DISLIKE/STRUGGLE not stolen by the LIKE matcher.
    assert "Counter surfing" in p.sections.get("struggles", "")
    assert p.photo_count == 3
    # "favorite companion" in prose must not register as a social word here
    # (companion does; that is intended). Just assert struggles present => no false flag.
    m = compute(p)
    assert "missing_struggles" not in m.flags


def test_intro_fallback_and_prose_favorite():
    p = _profile(NO_ABOUT_MD, "duke")
    # Intro captured despite no ABOUT heading; "favorite activity" not dropped.
    assert "happy-go-lucky" in p.sections.get("about", "")
    assert "favorite activity" in p.sections["about"]
    assert p.opening_sentence.startswith("Duke is a happy-go-lucky")


def test_placement_constraint_is_reported_not_scored():
    """A true attribute of the animal must not cost the profile points.

    ShelterLuv already publishes "only dog" as a structured attribute that drives the
    aggregator search filters, so omitting it from the prose widens the funnel by nobody
    and only desynchronizes the copy from the panel beside it.
    """
    duke = compute(_profile(NO_ABOUT_MD, "duke"))
    assert "only dog" in duke.placement_constraint_hits
    assert "only dog" not in duke.adopter_condition_hits
    assert duke.scores["no_gatekeeping"] == 4


def test_adopter_screening_language_is_still_scored():
    """Conditions on the applicant say nothing about the animal and stay penalized."""
    md = NO_ABOUT_MD.replace(
        "He should be the only dog in the home.",
        "He should be the only dog in the home. Qualified adopters only; must have a "
        "fenced yard.",
    )
    m = compute(_profile(md, "duke2"))
    assert "qualified adopters only" in m.adopter_condition_hits
    assert "must have a fenced yard" in m.adopter_condition_hits
    assert m.scores["no_gatekeeping"] == 0
    # The animal's own constraint still rides in the other list, unpenalized.
    assert "only dog" in m.placement_constraint_hits


def test_gatekeeping_and_completeness_scores():
    rex = compute(_profile(EMOJI_MD, "rex"))
    # sections_present stays an informational parse metric.
    assert rex.sections_present == len(_SECTION_KEYS)
    # section_completeness is no longer a deterministic metric: it is judged from content.
    assert "section_completeness" not in rex.scores
    # It arrives via the judge in combine(); full coverage -> 4/4.
    s = combine(_profile(EMOJI_MD, "rex"), rex, _FakeJudge())
    assert s.dim_scores["section_completeness"] == 4.0


def test_completeness_is_content_based_not_label_based():
    # A label-free free-prose profile: no section headings, everything in the intro. The
    # parser recovers only `about`, but the judge assesses coverage from the prose, so a
    # profile whose prose covers dogs and kids still earns section_completeness credit and
    # raises no missing_struggles flag.
    prose = (
        "# Nyx\n\n### Meet Nyx\n\n**Meet Nyx**\n\n"
        "Nyx knows sit and walks on a loose leash. She has played well with the dogs she "
        "has met and is gentle taking treats from the kids next door. She struggles to "
        "settle in a crate and is house-trained. She loves fetch.\n"
    )
    p = _profile(prose, "nyx")
    # Parser is label-blind here: only `about` (the intro) is recovered.
    assert set(p.sections) <= {"about"}
    m = compute(p)
    covered = {t: "covered" for t in _TOPICS}
    covered["cats"] = "absent"  # cats genuinely not mentioned
    s = combine(p, m, _FakeJudge(covered))
    # 6 of 7 required topics covered -> round(4 * 6/7) = 3 (well above a 1/8 label count).
    assert s.dim_scores["section_completeness"] == 3.0
    assert "missing_struggles" not in s.flags


def test_housebreaking_absence_costs_nothing():
    """A shelter rarely knows house-training, so its absence is not a copy defect."""
    p = _profile(EMOJI_MD, "rex")
    m = compute(p)
    no_house = {t: "covered" for t in _TOPICS}
    no_house["housebreaking"] = "absent"
    assert combine(p, m, _FakeJudge(no_house)).dim_scores["section_completeness"] == 4.0
    # ...and knowing it cannot mask a genuine miss on a required topic.
    masked = {t: "covered" for t in _TOPICS}
    masked["struggles"] = "absent"
    assert combine(p, m, _FakeJudge(masked)).dim_scores["section_completeness"] == 3.0


def test_missing_struggles_flag_is_judged():
    p = _profile(EMOJI_MD, "rex")
    m = compute(p)
    # No struggles disclosed anywhere -> the judge marks it absent -> flag raised.
    absent = {t: "covered" for t in _TOPICS}
    absent["struggles"] = "absent"
    s = combine(p, m, _FakeJudge(absent))
    assert "missing_struggles" in s.flags
    # ...and when struggles are disclosed, no flag.
    s2 = combine(p, m, _FakeJudge())
    assert "missing_struggles" not in s2.flags


def test_combine_bounds():
    p = _profile(EMOJI_MD, "rex")
    s = combine(p, compute(p), _FakeJudge())
    assert 0 <= s.raw <= 100


def test_facet_parsing():
    assert parse_age_months("2yrs 7mos") == 31
    assert parse_age_months("3yrs") == 36
    assert parse_age_months("5 months") == 5
    assert parse_age_months("") is None
    assert parse_weight_lbs("55 lbs") == 55.0
    p = _profile(EMOJI_MD, "rex")
    assert p.metadata.get("sex") == "Male"
    assert p.weight_lbs == 45.0
    assert p.age_months == 36


def test_record_and_ledger(tmp_path):
    p = _profile(EMOJI_MD, "rex")
    s = combine(p, compute(p), _FakeJudge())
    apply_cohort_percentiles([s])
    assert s.cohort_key == "species=dog"

    run_ctx = {"model": "claude-sonnet-5", "judge_runs": 3, "run_id": "R", "scored_at": "T"}
    results = tmp_path / "results"
    ledger = tmp_path / "scores.jsonl"
    record_mod.write_run([s], {"rex": p}, run_ctx, results, ledger, {"rex": "S"})

    rec = json.loads((results / "rex.json").read_text())
    # self-contained: identity, facets, content, scores, provenance, outcome stubs
    assert rec["slug"] == "rex" and rec["schema_version"] == "1.0"
    assert rec["age_months"] == 36 and rec["weight_lbs"] == 45.0
    assert len(rec["dimensions"]) == 9
    # novice-facing gloss travels with every dimension (drives dashboard help text)
    assert all(d["plain"] and d["tip"] for d in rec["dimensions"])
    # score interpretation bands travel with the data (server-side scoring semantics)
    assert rec["band"] in ("g", "a", "r")
    assert all(d["band"] in ("g", "a", "r") for d in rec["dimensions"])
    assert rec["raw"] == s.raw and rec["cohort_percentile"] is not None
    assert "days_to_placement" in rec  # outcome placeholder present
    assert "about" in rec["sections"] and "fee" not in rec["sections"]

    index = json.loads((results / "index.json").read_text())
    assert index["profiles"][0]["slug"] == "rex"
    assert index["profiles"][0]["band"] in ("g", "a", "r")
    assert index["bands"]["score"][0]["label"] == "Reference-worthy"
    assert len(index["dimensions"]) == 9

    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["slug"] == "rex" and row["dim_analytic_language"] == 2.0


def test_reserved_slug_rejected(tmp_path):
    import pytest

    p = _profile(EMOJI_MD, "index")  # would clobber index.json in the flat namespace
    s = combine(p, compute(p), _FakeJudge())
    apply_cohort_percentiles([s])
    run_ctx = {"model": "m", "judge_runs": 1, "run_id": "R", "scored_at": "T"}
    with pytest.raises(ValueError, match="Reserved slug"):
        record_mod.write_run([s], {"index": p}, run_ctx, tmp_path / "results", tmp_path / "l.jsonl")


# The third-person KNOWN vocabulary that replaced the first-person headings in
# the adoption-profile-writing skill. Live profiles still carry the old headings, so the parser
# has to answer to both; this guards the new set.
KNOWN_MD = """# Moose

**ABOUT THIS ANIMAL:**

Moose chases the ball down and brings it straight back.

**KNOWN WITH DOGS, CATS, AND KIDS:**

Dogs: plays well in playgroup. Reacts to dogs he passes on leash.
Cats: untested.
Kids: no young children.

**KNOWN TRAINING:**

Knows sit, down, paw, and touch.

**KNOWN IN THE HOME:**

Housetrained. Sleeps through the night.

**KNOWN LIKES:**

Tennis balls and swimming.

**KNOWN SENSITIVITIES:**

Guards food and high-value chews. One bite on record.

![Animal image](https://x/1.jpg)
"""


def test_known_heading_vocabulary_parses():
    p = _profile(KNOWN_MD, "moose-known")
    for key in _SECTION_KEYS:
        assert p.sections.get(key), f"missing section {key}"
    # KNOWN IN THE HOME carries the housebreaking topic.
    assert "Housetrained" in p.sections["housebreaking"]
    # KNOWN SENSITIVITIES carries struggles, so the disclosure flag stays clear.
    assert "Guards food" in p.sections["struggles"]
    # KNOWN LIKES must not be stolen by the struggles matcher.
    assert "Tennis balls" in p.sections["likes"]
    # All three species lines land in the one combined section.
    others = p.sections["others"]
    assert "plays well in playgroup" in others
    assert "Cats: untested" in others
    assert "no young children" in others
    m = compute(p)
    assert "missing_struggles" not in m.flags
    assert m.sections_present == len(_SECTION_KEYS)


# The four-heading template: likes fold into ABOUT THIS PET, dogs/cats/kids share HOME
# FIT, and GOOD TO KNOW carries the disclosures. Trailing program boilerplate (Senior
# Care Plan, Grey Muzzle) is identical across every eligible animal and is not body copy.
FOUR_HEADING_MD = """# Moose

Male
•
64 lbs

Kids - To Be Determined
Dogs - To Be Determined
Cats - To Be Determined

**ABOUT THIS PET:**

Moose is the king of fetch. He likes tennis balls, swimming, and working for treats.

**HOME FIT:**

Moose has lived with other dogs and plays well with the dogs at the shelter. He would do best as the only dog at home. Moose hasn't reacted to cats he has come across at FOHA. He does well with older teens and adults, and is best in a home without young children.

**TRAINING:**

Moose knows sit, down, paw, spin, and touch.

**GOOD TO KNOW:**

Moose guards his food and his high-value chews. Thunderstorms frighten him.

Moose is eligible for the FOHA Senior Care Plan that helps to cover any unexpected costs if they arise. FOHA waives the adoption fee on eligible pets and reimburses up to $1,500 in qualifying medical expenses or pet insurance premiums.

Moose is supported by a grant from Grey Muzzle Organization.

![Animal image](https://x/1.jpg)
"""


def test_four_heading_template_parses():
    p = _profile(FOUR_HEADING_MD, "moose-4")
    assert p.sections["about"].startswith("Moose is the king of fetch")
    # HOME FIT resolves to the combined dogs/cats/kids key.
    assert "only dog at home" in p.sections["others"]
    assert "hasn't reacted to cats" in p.sections["others"]
    # GOOD TO KNOW resolves to struggles, so the disclosure floor is met.
    assert "guards his food" in p.sections["struggles"]
    m = compute(p)
    assert "missing_struggles" not in m.flags
    # Two placement constraints, reported and unscored; no adopter screening.
    assert "only dog" in m.placement_constraint_hits
    assert "without young children" in m.placement_constraint_hits
    assert m.adopter_condition_hits == []
    assert m.scores["no_gatekeeping"] == 4


def test_program_boilerplate_excluded_from_body():
    """Senior Care Plan and Grey Muzzle copy is identical across profiles and is about
    FOHA's offer, not the animal, so it must not inflate the word count."""
    p = _profile(FOUR_HEADING_MD, "moose-4")
    body = p.body_text.lower()
    assert "senior care plan" not in body
    assert "grey muzzle" not in body
    assert "reimburses up to" not in body
    # The animal's own copy in the same section survives.
    assert "thunderstorms frighten him" in body


def test_four_heading_label_variants():
    """"HOUSEHOLD FIT" must resolve like "HOME FIT". Prefix matching means the longer
    label is not caught by the shorter one, so it needs its own entry or the section
    silently merges into whatever preceded it."""
    p = _profile(FOUR_HEADING_MD.replace("**HOME FIT:**", "**HOUSEHOLD FIT:**"), "moose-hf")
    assert "only dog at home" in p.sections["others"]
    assert "only dog" not in p.sections["about"]


def test_good_to_know_sibling_label():
    """"THINGS TO KNOW" resolves to struggles like "GOOD TO KNOW"."""
    p = _profile(FOUR_HEADING_MD.replace("**GOOD TO KNOW:**", "**THINGS TO KNOW:**"), "moose-tk")
    assert "guards his food" in p.sections["struggles"]
    assert "missing_struggles" not in compute(p).flags


# --- rubric 1.3: markup-free word counts, brevity floor, photo target ----------------


def test_word_count_ignores_image_and_link_markup():
    """Gallery markup is not prose.

    Moose scored 523 body words against a 190-word narrative because his 33 gallery
    images trail the struggles section, and every URL path segment counted as a word.
    That cost him full marks on brevity while he was the highest-scoring profile in the
    cohort.
    """
    from profile_grader.metrics import word_count

    prose = "Moose is the king of fetch."
    gallery = "".join(
        f"![Animal image](https://foha.org/wp-content/uploads/2023/06/photo-{i}-540x720.jpg)"
        for i in range(33)
    )
    assert word_count(prose) == 6
    assert word_count(prose + " " + gallery) == 6
    # A bare URL is markup too.
    assert word_count(prose + " https://foha.org/pet/moose2025/") == 6
    # Link *text* is prose the writer chose and survives; the target does not.
    assert word_count("See [our adoption policies](https://foha.org/policies/)") == 4


def test_lexicon_hits_ignore_words_buried_in_urls():
    """A URL slug must not register as a social word."""
    from profile_grader.metrics import lexicon_hits, strip_markup

    text = strip_markup("Rex is calm. ![x](https://foha.org/img/best-buddy-companion.jpg)")
    assert lexicon_hits(text, ["buddy", "companion"]) == []


def test_brevity_floor_catches_empty_profiles():
    """175-word floor replaces the old rule that gave 4/4 to anything over 50 words."""
    from profile_grader.metrics import _brevity_score

    assert _brevity_score(40) == 1
    assert _brevity_score(174) == 1  # short because empty, not because tight
    assert _brevity_score(175) == 4  # floor is inclusive
    assert _brevity_score(190) == 4  # Moose, four sections plus a full disclosure
    assert _brevity_score(250) == 4
    assert _brevity_score(251) == 3
    assert _brevity_score(551) == 0


def test_photo_score_targets_three_to_five():
    """Volume was the wrong target: Petfinder syndicates five slides."""
    from profile_grader.metrics import _photo_score

    assert _photo_score(0) == 0
    assert _photo_score(2) == 2
    assert _photo_score(3) == 4
    assert _photo_score(5) == 4
    assert _photo_score(6) == 3
    assert _photo_score(10) == 3
    assert _photo_score(33) == 2  # Moose's gallery: gentle taper, not a cliff


def test_dimension_weights_still_total_100():
    from profile_grader.score import DIMENSIONS

    assert sum(w for w, _, _ in DIMENSIONS.values()) == 100
    assert DIMENSIONS["brevity"][0] == 2
    assert DIMENSIONS["behavioral_concreteness"][0] == 18


# --- rubric 1.3: the injected volunteer carousel is not the editorial gallery ---------

# Mirrors a real page: two campaign banners linked off-site, one unlinked featured photo,
# a linked editorial gallery, a sponsor badge, footer furniture, then the injected
# `<div class="foha-gallery">` carousel of volunteer uploads.
CAROUSEL_MD = """
[![SP26-Website-Banner-2-scaled](https://foha.org/wp-content/uploads/2020/05/SP26-Website-Banner-2-scaled.jpg)](https://foha.app.neoncrm.com/forms/2026-summer-appeal-online)
[![3-scaled](https://foha.org/wp-content/uploads/2020/05/3-scaled.jpg)](https://foha.cbo.io/)
![featured](https://foha.org/wp-content/uploads/2026/03/Polly-1-1024x683.jpg)

# Polly

- **Breed** Terrier Mix
- **Age** 3yrs 1mo

Kids - No Kids

Dogs - Good with Dogs

Cats - No Cats

### Meet Polly

ABOUT THIS PET

Polly retrieves a thrown ball and returns it to hand.

HOUSEHOLD FIT

Polly has played with the dogs at the shelter. She has not been tested with cats.

TRAINING

Polly knows sit and down.

GOOD TO KNOW

Polly guards her food bowl.

[![gallery-a](https://foha.org/wp-content/uploads/2026/03/Polly-2-540x720.jpg)](https://foha.org/pet/polly/attachment/polly-2/)
[![gallery-b](https://foha.org/wp-content/uploads/2026/03/Polly-3-540x720.jpg)](https://foha.org/pet/polly/attachment/polly-3/)
![Grant-recipient-logo](https://foha.org/wp-content/uploads/2021/08/Grant-recipient-logo-629x720.png)
![Animal image](https://adalo-uploads.imgix.net/aaa.jpg)![Animal image](https://adalo-uploads.imgix.net/bbb.jpg)![Animal image](https://adalo-uploads.imgix.net/ccc.jpg)![Animal image](https://adalo-uploads.imgix.net/ddd.jpg)
![smart-dog](https://foha.org/wp-content/uploads/2020/06/smart-dog.jpg)
"""


def test_injected_carousel_excluded_from_photo_count():
    """The foha-gallery carousel is a volunteer upload feed, not the editorial gallery.

    It accumulates roughly a shot per walk, so counting it scored long-stay animals on
    how long they had been waiting: Polly Pocket showed 54 carousel images against one
    editorial photo, and none of them syndicate to Petfinder or Adopt-a-Pet.
    """
    p = _profile(CAROUSEL_MD, "polly")
    # featured + two gallery images. Banners, sponsor badge, footer, carousel all out.
    assert p.photo_count == 3
    # The carousel is still reported, so "no photos" stays distinguishable.
    assert p.carousel_count == 4
    assert compute(p).scores["photos"] == 4  # 3 lands in the 3-5 target band


def test_campaign_banner_excluded_by_its_offsite_link():
    """Banners are site uploads; the off-site link target is what marks them as chrome.

    Matching the link rather than the filename survives FOHA reskinning the banner,
    which it does seasonally.
    """
    md = CAROUSEL_MD.replace("SP26-Website-Banner-2-scaled", "FA27-Website-Banner-9-scaled")
    assert _profile(md, "polly").photo_count == 3


def test_single_photo_profile_is_not_credited_for_its_carousel():
    """37 of 62 cohort profiles have exactly one editorial photo."""
    md = CAROUSEL_MD.replace(
        "[![gallery-a](https://foha.org/wp-content/uploads/2026/03/Polly-2-540x720.jpg)](https://foha.org/pet/polly/attachment/polly-2/)\n", ""
    ).replace(
        "[![gallery-b](https://foha.org/wp-content/uploads/2026/03/Polly-3-540x720.jpg)](https://foha.org/pet/polly/attachment/polly-3/)\n", ""
    )
    p = _profile(md, "polly")
    assert p.photo_count == 1
    assert p.carousel_count == 4
    assert compute(p).scores["photos"] == 2  # 1-2 photos: too few
