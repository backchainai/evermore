# Adoption Profile Grading Rubric

The scoring standard for FOHA adoption profiles. Every dimension traces to the
research in `../../reference/research/shelter-outcomes/` (Markowitz 2019; Kelling et al. 2024) and
the `adoption-profile-writing` skill, which is where the writing rules themselves are
maintained. This file is the scoring source of truth; the judge
prompt in `src/profile_grader/judge.py` implements the judged dimensions (including
topic coverage), `src/profile_grader/metrics.py` implements the deterministic ones, and
`src/profile_grader/score.py` weights and combines them.

## Scoring model

Each dimension is scored `0-4` against the anchors below, then weighted. The weighted
sum is normalized to a **0-100 absolute score** (against the research ideal), reported
alongside a **cohort percentile** (rank within the graded batch).

Three design commitments:

1. **Absolute first, cohort second.** Copy quality is judged against the research
   ideal, not graded on a curve. The FOHA population is adversely selected on
   *outcomes* (age, health, length of stay); that does not excuse the *copy*. The cohort
   percentile is context, not the grade.
2. **Grade the framing, not the facts.** Disclosing a struggle is mandatory (FOHA
   observed-only rule). The rubric never rewards hiding a problem. It rewards stating
   struggles factually and neutrally, and penalizes emotional or screening framing.
3. **Never score the absence of information.** Two dimensions were penalizing profiles
   for facts that do not exist or for constraints the shelter system publishes anyway;
   both were corrected in rubric 1.2 (see dimensions 5 and 7). A profile is graded on the
   quality of what it states, and stating "untested" counts as stating something.

## Dimensions and weights

| # | Dimension | Weight | Method | Backing |
|---|---|---|---|---|
| 1 | Analytic vs. narrative language | 20 | judge | Markowitz: strongest single finding |
| 2 | Behavioral concreteness | 18 | judge | Markowitz: behavior > personality adjectives; Kelling: adopters rank behavior first |
| 3 | Observed, not promised | 15 | judge + flags | Observed-only rule; future-promise finding |
| 4 | No social / humanizing words | 10 | deterministic | Markowitz: social words are red flags |
| 5 | No adopter screening language | 10 | deterministic | Kelling: drop elimination requirements |
| 6 | Identity-forward opening | 5 | judge | Markowitz: open on who, not what |
| 7 | Section completeness | 10 | judge | Skill: 7 scored topics, covered in a section or in prose |
| 8 | Brevity | 2 | deterministic | Markowitz: shorter places faster, but weakly |
| 9 | Photo count | 10 | deterministic | Markowitz Study 2: more photos place faster, to a point |

Total weight = 100.

## Anchors

### 1. Analytic vs. narrative language (judge)
- **4** Consistently concrete and factual; articles/prepositions, specific attributes; no superlatives.
- **3** Mostly factual with occasional narrative flourish.
- **2** Even mix of factual and story/emotional register.
- **1** Predominantly narrative, superlative-heavy ("adorable," "so much love").
- **0** Pure storytelling; little verifiable content.

### 2. Behavioral concreteness (judge)
- **4** Claims are observable behaviors ("knows sit," "pulls slightly on leash," "no accidents in two weeks").
- **3** Mostly behavior, some personality labels.
- **2** Mix of behavior and adjective ("sweet," "gentle") in roughly equal measure.
- **1** Mostly personality adjectives with little observable behavior.
- **0** Adjectives only; nothing an adopter could verify.

### 3. Observed, not promised (judge + deterministic flags)
- **4** Every claim is past/observed; unknowns stated as unknown; no guarantees.
- **3** Observed throughout with one soft generalization.
- **2** Some future promises or absolute claims mixed in.
- **1** Several guarantees ("great with all dogs," "will love your kids").
- **0** Built on promises; contradicts its own disclosures (tag says a trait the body calls unknown).
- **Hard cap:** a temperament tag that contradicts the body (tag "Good with Kids" while the body says "Unknown") caps this dimension at **2** and raises a compliance flag.

### 4. No social / humanizing words (deterministic)
Rate = flagged social words per 100 body words (lexicon in `lexicons.py`: "buddy,"
"companion," "best friend," "sweetheart," "fur baby," etc.).
- **4** rate = 0 | **3** < 1 | **2** 1-2 | **1** 2-3 | **0** > 3

### 5. No adopter screening language (deterministic)
Count of **adopter-condition** phrases (lexicon: "must have a fenced yard," "qualified
adopters only," "experienced owners only," "serious inquiries only," "not for first-time
owners," etc.).
- **4** 0 phrases | **2** 1 phrase | **0** 2+ phrases

**Placement constraints are counted and reported, never scored.** "Only dog," "no cats,"
and "without young children" are attributes of the animal, not conditions on the
applicant. Kelling's finding is that a constraint lengthens stay by shrinking the pool of
eligible adopters, and that shrinking happens because the constraint is true. ShelterLuv
already carries these as structured attributes and pushes them to Petfinder and
Adopt-a-Pet, where they drive the search filters, so deleting the sentence from the prose
widens the funnel by nobody. It only hides the reason from the adopter and makes the copy
disagree with the attribute panel printed beside it, which is the same defect
`tag_body_contradiction` exists to catch.

The scorecard lists the constraints it found so a reviewer can check each one against the
record. The useful question is provenance, not presence: a constraint the file does not
support should come out, and one it does support should stay.

### 6. Identity-forward opening (judge)
Scores the first sentence only.
- **4** Opens on who the animal is / a concrete vivid behavior.
- **2** Opens on a mix, or a generic personality adjective.
- **0** Opens on raw statistics / breed / medical status.

### 7. Section completeness (judge)
Seven scored topics: About, Dogs, Cats, Kids, Training, Likes, Struggles.

The `adoption-profile-writing` skill writes them into four sections, whose headings are third
person and set in full capitals:

| Section | Topics it carries |
|---|---|
| ABOUT THIS PET | About, Likes |
| HOUSEHOLD FIT | Dogs, Cats, Kids |
| TRAINING | Training |
| GOOD TO KNOW | Struggles |

Likes and Struggles are scored independently of the sections holding them, so a profile can
fill all four headings and still lose points by never naming what the animal enjoys or what it
finds hard. Coverage is judged from the profile's **content**, not from whether a labeled
section exists: a hand-authored free-prose profile can cover a topic inside its opening
paragraph, and a labeled section left blank does not cover its topic. The judge assigns
each topic a status from the full staff text: `covered` (substantively addressed; a stated
fact, behavior, or an explicit "untested"/"unknown" disclosure all count), `brief` (touched
only glancingly), or `absent` (not addressed). "Unknown" is complete information, not a gap.
- Per-topic weight: covered = 1.0, brief = 0.5, absent = 0.
- Score = `round(4 * sum(weights) / 7)`, averaged across judge runs.

**Housebreaking/crating is reported but not scored.** A shelter almost never learns an
animal's house-training or crate history, so absence there is the default state of the
record rather than something the writer left out. Scoring it docked every profile in the
cohort for a fact that does not exist, and made the cohort roll-up name it a systemic
template weakness. The judge still reports its coverage status, because a
known-house-trained animal is worth writing down; it earns no points, since covering the
seven required topics already scores 4/4 and an eighth term could only let credit here
paper over a genuine miss elsewhere.

The judge reads only the parsed staff sections and opening sentence, never the raw page, so
user-generated comment content cannot earn coverage credit.

### 8. Brevity (deterministic)
Body word count (narrative sections only). Boilerplate identical across profiles is
excluded so it does not distort length or language scores: the adoption-fee block, and
the program blocks that trail eligible animals (Senior Care Plan, Grey Muzzle grant).
Those describe FOHA's offer rather than the animal, and no writer chose their wording.
Markdown image and link markup is stripped before counting: a gallery of 33 images was
adding roughly 330 phantom words to the profile it trailed.
- **4** 175-250 | **3** 251-350 | **2** 351-450 | **1** 451-550 or < 175 | **0** > 550

The floor at 175 is the part that does work. The old bands gave full marks to anything
from 50 words up, which rewarded profiles that were short because they were empty: apart
from Moose, who covers four sections and a full disclosure in 190 words, the sub-250
band holds the cohort's worst behavioral concreteness. The weight is 2 rather than 5
because measured length carries almost no information about copy quality: across the
62-profile cohort, narrative word count correlates +0.03 with the sum of the other
dimensions, and -0.14 with analytic language. Brevity also remains the one dimension a
writer can improve by deleting content, which design commitment 2 forbids elsewhere, so
it earns the smallest weight that still lets the floor bite.

### 9. Photo count (deterministic)
Count of unique **editorial** photos: images a person chose and placed on the profile,
hosted on `foha.org/wp-content/uploads/`. The target is 3-5.
- **0** 0 | **2** 1-2 | **4** 3-5 | **3** 6-10 | **2** 11+

Three things are excluded, and the first is the one that matters:

1. **The injected volunteer carousel.** A `<div class="foha-gallery">` appended to every
   profile by a volunteer's script, holding photos volunteers upload through FOHA's
   Adalo app. It renders as `![Animal image](https://adalo-uploads.imgix.net/...)`, it
   accumulates roughly a shot per walk, and it syndicates nowhere. Until rubric 1.3 the
   grader counted *only* this and never the editorial photos, so the dimension was
   measuring how long an animal had been waiting. Polly Pocket showed 54 against a
   single editorial photo. `Profile.carousel_count` still reports it, unscored, so a
   profile with no editorial photo stays distinguishable from one with none at all.
2. **Campaign banners**, identified by their off-site link target rather than their
   filename, since FOHA reskins them seasonally.
3. **Sponsor badges, seals, and footer furniture** (`.png` files, plus a short name list).

Counted correctly, the cohort's problem is too few photos, not too many: 37 of 62
profiles carry exactly one editorial photo, only 10 sit in the 3-5 band, and the
richest has 9. The taper above 5 is gentle and rarely binds; the 1-2 band is what the
dimension now actually tests. The research is split on volume in any case: Markowitz
Study 1 found more photos associated with *longer* listings, Study 2 with adoption, and
the author calls the Study 2 direction speculative, since agencies add images to
profiles that are not moving. Five is also roughly what syndication carries: Petfinder
showed 5 slides for Moose.

## Compliance flags (reported, not scored)

Surfaced separately so no one can improve a score by deleting content:
- **missing_struggles** — the copy discloses no struggle, difficulty, or dislike anywhere (disclosure floor); judged from content, not from a missing label.
- **tag_body_contradiction** — a temperament tag asserts a trait the body calls unknown or contradicts.
- **absolute_claim** — narrative guarantees ("great with all dogs," "guaranteed," "will love").

## Normalization

- `raw = sum(weight_i * score_i / 4)` → 0-100.
- `cohort_percentile` = percent of graded profiles with a lower raw score.
- Report both. The fix list ranks edits by recoverable points = `weight_i * (4 - score_i) / 4`.

## Calibration hook

Once ~30-50 profiles are scored, correlate `raw` against actual days-to-placement
(the funnel data keyed on animal ID). Weak correlation is the signal to re-weight. This
converts the rubric from "graded against research" to "graded against FOHA outcomes."
