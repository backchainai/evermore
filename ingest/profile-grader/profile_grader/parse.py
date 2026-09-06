"""Turn a scraped FOHA profile page into a structured Profile.

FOHA profile pages (native WordPress) are consistently structured:
  # <Name>
  metadata list: - **Breed** ...  - **Age** ...
  temperament tags: "Kids - Good with Kids" / "Dogs - ..." / "Cats - ..."
  narrative sections as bold-caps headings: **ABOUT THIS ANIMAL:** ... etc.
  an editorial photo or gallery, hosted on foha.org/wp-content/uploads/
  an injected volunteer carousel of ![Animal image](adalo-uploads...) — not editorial
  a fixed **ADOPTION FEE INCLUDES:** boilerplate (identical across profiles)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Canonical section key -> label prefixes that name it, most specific first. A heading
# line is matched by prefix against this vocabulary, so a heading is identified by WHAT
# IT SAYS, not how it is marked up. Order matters: struggles before likes because both
# open "THINGS I", and multi-word prefixes precede their one-word fallbacks.
#
# Three heading vocabularies coexist and all must keep parsing, so add to this table
# rather than replacing entries:
#
#   1. The four-heading set being adopted: ABOUT THIS PET / HOUSEHOLD FIT / TRAINING /
#      GOOD TO KNOW. Dogs, cats, and kids share HOUSEHOLD FIT; likes fold into ABOUT.
#   2. The KNOWN.. prefixes from the adoption-profile-writing skill.
#   3. The first-person headings that live foha.org profiles still carry.
#
# Matching is by prefix, so a longer label is NOT caught by a shorter sibling and needs
# its own entry: "HOUSEHOLD FIT" does not match "HOME FIT", and "KNOWN WITH DOGS" does
# not match the "WITH DOGS" fallback. Getting this wrong fails silently, merging the
# section into whatever preceded it and scoring a wrongly parsed profile.
_LABELS: list[tuple[str, tuple[str, ...]]] = [
    ("about", ("ABOUT THIS PET", "ABOUT THIS ANIMAL", "ABOUT ME", "ABOUT")),
    # One section covers all three. "KNOWN WITH DOGS, CATS, AND KIDS" is caught by the
    # "KNOWN WITH DOGS" prefix; the rest are the legacy per-species headings, which a live
    # profile still carries as three separate blocks that merge into this one key.
    (
        "others",
        (
            "HOUSEHOLD FIT",
            "HOME FIT",
            "KNOWN WITH OTHER DOGS",
            "KNOWN WITH DOGS",
            "KNOWN WITH CATS",
            "KNOWN WITH CHILDREN",
            "KNOWN WITH KIDS",
            "HOW AM I WITH OTHER DOGS",
            "HOW AM I WITH DOGS",
            "HOW AM I WITH CATS",
            "HOW AM I WITH KIDS",
            "WITH OTHER DOGS",
            "WITH DOGS",
            "WITH CATS",
            "WITH CHILDREN",
            "WITH KIDS",
        ),
    ),
    ("training", ("I KNOW THE FOLLOWING COMMANDS", "KNOWN TRAINING", "KNOWN CUES", "MY TRAINING", "COMMANDS I KNOW", "TRAINING", "COMMAND")),
    ("housebreaking", ("KNOWN IN THE HOME", "KNOWN HOUSEBREAKING", "MY HOUSEBREAKING", "IN THE HOME", "HOUSEBREAK", "CRATING", "CRATE")),
    ("struggles", ("GOOD TO KNOW", "THINGS TO KNOW", "KNOWN SENSITIVITIES", "KNOWN DISLIKES", "KNOWN CAUTIONS", "THINGS I STRUGGLE WITH", "THINGS I DISLIKE", "SENSITIVITIES", "STRUGGLE", "DISLIKE")),
    ("likes", ("KNOWN LIKES", "THINGS I LIKE", "THINGS I LOVE", "THINGS I ENJOY", "I LIKE", "I LOVE", "I ENJOY")),
    ("fee", ("ADOPTION FEE",)),
]

# Recognized non-section headings. They bound the preceding section (so its body stops
# cleanly) but hold no scored content. The comment/newsletter markers are the top of the
# page's user-generated Disqus block and the mailing-list widget: staff content ends
# here, so scoring must never reach past them.
_BOUNDARY_LABELS: tuple[str, ...] = (
    "FOHA ADOPTION POLICIES",
    "SPECIAL REQUIREMENTS",
    "DISQUS",
    "LOG IN WITH",
    "LEAVE A COMMENT",
    "STAY IN THE LOOP",
    "SIGN UP FOR UPDATES",
    "THANKS FOR SIGNING UP",
)

# Narrative sections that make up the scored body (fee boilerplate excluded).
BODY_SECTIONS: tuple[str, ...] = (
    "about",
    "others",  # dogs, cats, and kids: one section in the template, one key here
    "training",
    "housebreaking",
    "likes",
    "struggles",
)

# Section headings are detected by their LABEL, not their markup. FOHA profiles are
# authored by hand in WordPress, so the same eight sections appear in inconsistent
# surface forms that vary independently of each other: markup (bold "**...**", ATX
# "## ...", or plain), a trailing colon or none, a leading emoji or none, and casing
# (ALL CAPS or Title Case). Matching the label text (via _LABELS) against a short line,
# after stripping markup and any leading emoji, makes every one of those a no-op instead
# of a silently dropped section. The short-line gate keeps a body sentence that merely
# contains a label word from being mistaken for a heading.
_MAX_LABEL_LEN = 48
_LEADING_MARKUP_RE = re.compile(r"^[\s>*_#]+")
_TRAILING_MARKUP_RE = re.compile(r"[\s*_#:]+$")


def _label_core(line: str) -> str:
    """A heading candidate's bare label: markup, leading emoji, and trailing colon removed."""
    s = _TRAILING_MARKUP_RE.sub("", _LEADING_MARKUP_RE.sub("", line.strip()))
    first = re.search(r"[A-Za-z]", s)  # drop any leading emoji/symbol run
    return s[first.start():].strip() if first else ""


def _classify_heading(line: str) -> tuple[bool, str | None]:
    """(is_heading, canonical_key). key is None for a recognized non-section boundary.

    A heading is a short line whose label prefix-matches the vocabulary, regardless of
    markup, colon, emoji, or case.
    """
    core = _label_core(line)
    if not core or len(core) > _MAX_LABEL_LEN:
        return (False, None)
    up = core.upper()
    for key, prefixes in _LABELS:
        if any(up.startswith(p) for p in prefixes):
            return (True, key)
    if any(up.startswith(p) for p in _BOUNDARY_LABELS):
        return (True, None)
    return (False, None)


def _iter_headings(markdown: str):
    """Yield (line_start, line_end, canonical_key_or_None) for each heading line.

    Boundary headings (e.g. "FOHA ADOPTION POLICIES AND PROCESS") are yielded with
    key=None so they still bound the preceding section but are never stored as content.
    """
    offset = 0
    for line in markdown.splitlines(keepends=True):
        is_head, key = _classify_heading(line)
        if is_head:
            yield offset, offset + len(line), key
        offset += len(line)


_MEET_RE = re.compile(r"^#{2,4}\s+.*\bMeet\b", re.MULTILINE)
_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")

# Chrome phrases that can leak into the intro region and are not profile prose.
# Multi-word only: single common words ("share", "favorite", "status") also occur in
# prose ("favorite activity"), and the UI labels bearing them sit before the Meet marker.
_INTRO_CHROME = (
    "return to search",
    "please review",
    "start an application",
    "come meet me",
    "set an appointment",
    "need more info",
    "get in touch",
    "interested in adopting",
)
_META_RE = re.compile(r"-\s*\*\*\s*([A-Za-z][\w /]*?)\s*\*\*\s*(.+)")
_TAG_RE = re.compile(r"^(Kids|Dogs|Cats)\s*[-–—]\s*(.+?)\s*$", re.MULTILINE)
# The injected volunteer carousel: a `<div class="foha-gallery">` a volunteer's script
# appends to every profile, holding photos volunteers upload through FOHA's Adalo app.
# It renders as ![Animal image](https://adalo-uploads.imgix.net/...). It is not the
# editorial gallery and is never counted: it accumulates a shot per walk, so a long-stay
# animal collects dozens (Polly Pocket had 54 against a single editorial photo), and
# none of it syndicates to Petfinder or Adopt-a-Pet.
_CAROUSEL_RE = re.compile(r"!\[Animal image\]\((https?://[^)]+)\)")

# Editorial photos: WordPress uploads on foha.org.
_ANY_IMG_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+?)\)")
# [![alt](image)](link) -> image, link. A campaign banner is the site's own upload but is
# wrapped in a link to an off-site donation host, which is what distinguishes it from an
# animal photo. Matching the link rather than the filename survives FOHA reskinning the
# banner each season.
_LINKED_IMG_RE = re.compile(r"\[!\[[^\]]*\]\((https?://[^)\s]+?)\)\]\((https?://[^)\s]+?)\)")
_WP_UPLOADS = "foha.org/wp-content/uploads/"
# Unlinked site furniture, which structure alone cannot separate from a photo.
_CHROME_RE = re.compile(r"/(smart-dog|foha-logo|logo-foha|foha-sticky)", re.IGNORECASE)
_SEX_RE = re.compile(r"^(Male|Female)\s*$", re.MULTILINE)
_WEIGHT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*lbs?", re.IGNORECASE)
_AGE_RE = re.compile(r"(?:(\d+)\s*(?:yr|year))?[^\d]*?(?:(\d+)\s*(?:mo|month))?", re.IGNORECASE)


def parse_age_months(age_raw: str) -> int | None:
    """'2yrs 7mos' / '2 years 7 months' -> 31. Returns None if unparseable."""
    if not age_raw:
        return None
    yrs = re.search(r"(\d+)\s*(?:yr|year)", age_raw, re.IGNORECASE)
    mos = re.search(r"(\d+)\s*(?:mo|month)", age_raw, re.IGNORECASE)
    if not yrs and not mos:
        return None
    return (int(yrs.group(1)) * 12 if yrs else 0) + (int(mos.group(1)) if mos else 0)


def parse_weight_lbs(weight_raw: str) -> float | None:
    m = _WEIGHT_RE.search(weight_raw or "")
    return float(m.group(1)) if m else None


@dataclass
class Profile:
    slug: str
    url: str
    name: str
    species: str  # "dog" | "cat" | "unknown"
    metadata: dict[str, str] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)  # kids/dogs/cats -> raw label
    sections: dict[str, str] = field(default_factory=dict)  # canonical key -> text
    photo_count: int = 0
    # Injected volunteer carousel. Reported so "no photos" stays distinguishable from
    # "photos only in the carousel"; never scored.
    carousel_count: int = 0
    raw_markdown: str = ""

    @property
    def body_text(self) -> str:
        parts = [self.sections[k] for k in BODY_SECTIONS if self.sections.get(k)]
        return "\n\n".join(parts).strip()

    @property
    def opening_sentence(self) -> str:
        about = self.sections.get("about", "").strip()
        if not about:
            return ""
        # First sentence: stop at a period/!/? followed by space or end.
        m = re.search(r"^(.*?[.!?])(\s|$)", about, re.DOTALL)
        return (m.group(1) if m else about).strip()

    @property
    def age_months(self) -> int | None:
        return parse_age_months(self.metadata.get("age", ""))

    @property
    def weight_lbs(self) -> float | None:
        return parse_weight_lbs(self.metadata.get("weight", ""))


# Program boilerplate that trails the narrative on eligible animals (Senior Care Plan,
# Grey Muzzle grant). The wording is identical on every profile in the program and
# describes FOHA's offer rather than the animal, so counting it as body text inflates the
# word count and dilutes the language ratios with copy no writer chose. Excluded on the
# same grounds as the adoption-fee boilerplate. Matched anywhere in the line rather than
# at the start, because the sentence usually opens with the animal's name.
_PROGRAM_BOILERPLATE: tuple[str, ...] = (
    "senior care plan",
    "grey muzzle",
    "waives the adoption fee",
    "reimburses up to",
    "qualifying medical expenses",
)


def _clean(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        # Drop the inter-section policy line and any residual link/share chrome.
        if s.upper().startswith("FOHA ADOPTION POLICIES"):
            continue
        low = s.lower()
        if any(marker in low for marker in _PROGRAM_BOILERPLATE):
            continue
        lines.append(s)
    return " ".join(lines).strip()


def _parse_sections(markdown: str) -> dict[str, str]:
    heads = list(_iter_headings(markdown))
    sections: dict[str, str] = {}
    for i, (_line_start, line_end, key) in enumerate(heads):
        if key is None:
            continue
        end = heads[i + 1][0] if i + 1 < len(heads) else len(markdown)
        body = markdown[line_end:end]
        # Stop the last section before the Disqus / comments chrome.
        body = re.split(r"\n\s*Disqus Comments", body)[0]
        text = _clean(body)
        if text:
            # A key can be hit more than once: the current template puts dogs, cats, and
            # kids under one heading, while a live profile still carries three separate
            # headings that all resolve to "others". Append so neither layout drops text.
            sections[key] = f"{sections[key]}\n\n{text}" if key in sections else text
    return sections


def _clean_intro_line(ln: str) -> str:
    s = _IMG_RE.sub("", ln)
    s = _LINK_RE.sub(r"\1", s)
    return s.replace("**", "").strip()


def _extract_intro(markdown: str) -> str:
    """Narrative opening for profiles with no ABOUT section heading.

    Some profiles open under a '**Meet <Name> 💛**' line instead. Capture the prose
    between the 'Meet' marker and the first recognized heading of any kind: a body
    section, the fee boilerplate, or a boundary. For a fully unstructured profile the
    boundary is the Disqus / newsletter chrome, so the intro never swallows comments.
    """
    cut = len(markdown)
    for line_start, _line_end, _key in _iter_headings(markdown):
        cut = line_start
        break
    start = 0
    for mm in _MEET_RE.finditer(markdown):
        if mm.start() >= cut:
            break
        nl = markdown.find("\n", mm.start())
        start = nl + 1 if nl != -1 else mm.end()

    out: list[str] = []
    for ln in markdown[start:cut].splitlines():
        if ln.lstrip().startswith("#"):
            continue
        s = _clean_intro_line(ln)
        if not s:
            continue
        low = s.lower()
        if low.startswith("meet ") or any(c in low for c in _INTRO_CHROME):
            continue
        out.append(s)
    return " ".join(out).strip()


def _parse_metadata(markdown: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    for m in _META_RE.finditer(markdown):
        meta[m.group(1).strip().lower()] = m.group(2).strip()
    status = ""
    ms = re.search(r"\*\*\s*Status\s*\*\*\s*(.+)", markdown)
    if ms:
        status = ms.group(1).strip()
    return meta, status


def _parse_tags(markdown: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for m in _TAG_RE.finditer(markdown):
        tags[m.group(1).lower()] = m.group(2).strip()
    return tags


def _parse_name(markdown: str) -> str:
    m = re.search(r"^#\s+(.+?)\s*$", markdown, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _editorial_photos(markdown: str) -> set[str]:
    """Unique animal photos a person chose to put on the profile.

    Excludes the injected volunteer carousel (off-site Adalo host), the campaign
    banners (site uploads, but linked to an off-site donation host), sponsor badges and
    seals (.png), and unlinked site furniture.
    """
    linked = {m.group(1): m.group(2) for m in _LINKED_IMG_RE.finditer(markdown)}
    out: set[str] = set()
    for _alt, url in _ANY_IMG_RE.findall(markdown):
        if _WP_UPLOADS not in url:
            continue
        target = linked.get(url)
        if target and "foha.org" not in target:
            continue
        if url.lower().endswith(".png") or _CHROME_RE.search(url):
            continue
        out.add(url)
    return out


def _count_photos(markdown: str, images: list[str]) -> int:
    photos = _editorial_photos(markdown)
    if photos:
        return len(photos)
    # Fallback for a scrape whose markdown lost the gallery: same filters, no link
    # context available, so a campaign banner can only be caught by extension.
    return len(
        {
            u
            for u in images
            if _WP_UPLOADS in u and not u.lower().endswith(".png") and not _CHROME_RE.search(u)
        }
    )


def _count_carousel(markdown: str) -> int:
    """Injected volunteer-upload carousel. Reported, never scored."""
    return len(set(_CAROUSEL_RE.findall(markdown)))


def parse_scrape(data: dict, slug: str, species: str = "unknown") -> Profile:
    """Build a Profile from one firecrawl scrape JSON payload."""
    markdown = data.get("markdown", "") or ""
    images = data.get("images", []) or []
    meta_block = data.get("metadata", {}) or {}
    url = meta_block.get("sourceURL") or meta_block.get("url") or ""

    metadata, status = _parse_metadata(markdown)
    if status:
        metadata["status"] = status
    # Sex and weight live in the "Female • 55 lbs" header line, not the bullet list.
    sex_m = _SEX_RE.search(markdown)
    if sex_m and "sex" not in metadata:
        metadata["sex"] = sex_m.group(1)
    wt_m = _WEIGHT_RE.search(markdown)
    if wt_m and "weight" not in metadata:
        metadata["weight"] = wt_m.group(0)

    sections = _parse_sections(markdown)
    if not sections.get("about"):
        intro = _extract_intro(markdown)
        if intro:
            sections["about"] = intro

    return Profile(
        slug=slug,
        url=url,
        name=_parse_name(markdown),
        species=species,
        metadata=metadata,
        tags=_parse_tags(markdown),
        sections=sections,
        photo_count=_count_photos(markdown, images),
        carousel_count=_count_carousel(markdown),
        raw_markdown=markdown,
    )


def load_profile(path: str | Path, species: str = "unknown") -> Profile:
    """Load and parse a cached scrape JSON file (named <slug>.json)."""
    path = Path(path)
    slug = path.stem
    data = json.loads(path.read_text())
    return parse_scrape(data, slug=slug, species=species)
