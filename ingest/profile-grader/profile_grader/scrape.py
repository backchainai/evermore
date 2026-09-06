"""Firecrawl-backed scraping of FOHA profiles.

Per project policy (`~/.claude/rules/document-ingestion.md`), web fetches go through
Firecrawl, not raw HTTP. We shell out to the installed `firecrawl` CLI. Raw scrapes are
cached to disk so re-scoring never re-bills Firecrawl (1 credit / page).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

LISTINGS = {
    "dog": "https://foha.org/pet-adoption/find-a-dog/",
    "cat": "https://foha.org/pet-adoption/find-a-cat/",
}
_PET_RE = re.compile(r"https?://foha\.org/pet/([^/?#]+)/?")


def _firecrawl(args: list[str]) -> str:
    proc = subprocess.run(
        ["firecrawl", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"firecrawl failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def discover_profiles(species: str, limit: int, max_pages: int = 4) -> list[tuple[str, str]]:
    """Return [(slug, url)] for a species by reading the paginated listing pages."""
    base = LISTINGS[species]
    seen: dict[str, str] = {}
    for page in range(1, max_pages + 1):
        url = base if page == 1 else f"{base}?_paged={page}"
        try:
            out = _firecrawl(["scrape", url, "--format", "links", "--only-main-content", "--json"])
        except RuntimeError:
            break
        try:
            links = json.loads(out).get("links", [])
        except json.JSONDecodeError:
            links = _PET_RE.findall(out)
            links = [f"https://foha.org/pet/{s}/" for s in links]
        found_this_page = False
        for link in links:
            m = _PET_RE.match(link)
            if not m:
                continue
            slug = m.group(1)
            if slug not in seen:
                seen[slug] = f"https://foha.org/pet/{slug}/"
                found_this_page = True
            if len(seen) >= limit:
                return list(seen.items())
        if not found_this_page:
            break
    return list(seen.items())


def scrape_profile(url: str, slug: str, cache_dir: Path, refresh: bool = False) -> Path:
    """Scrape one profile to cache_dir/<slug>.json. Skips if cached (unless refresh)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / f"{slug}.json"
    if out_path.exists() and not refresh:
        return out_path
    _firecrawl(
        [
            "scrape",
            url,
            "--format",
            "markdown,images,links",
            "--only-main-content",
            "--json",
            "-o",
            str(out_path),
        ]
    )
    return out_path


def scrape_batch(
    species: str, limit: int, cache_dir: Path, refresh: bool = False
) -> list[tuple[str, str, Path]]:
    """Discover + scrape up to `limit` profiles. Returns [(slug, url, cached_path)]."""
    profiles = discover_profiles(species, limit)
    results: list[tuple[str, str, Path]] = []
    for slug, url in profiles:
        path = scrape_profile(url, slug, cache_dir, refresh=refresh)
        results.append((slug, url, path))
    return results
