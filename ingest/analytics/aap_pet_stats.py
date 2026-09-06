# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright", "lxml"]
# ///
"""
Adopt-a-Pet.com per-pet stats extractor for Friends of Homeless Animals.

Logs into the FOHA shelter account, reads the Individual Pet Stats report
(view_pet_stats), and writes an append-only weekly snapshot plus a combined
rolling history, so repeated weekly runs accumulate 90-day trends.

READ ONLY: the only POST issued is the login form submission. Every other
request is a GET. The report is paginated (?current_page=N); those are
read-only page loads of the same report, not a crawl to other reports.

Credentials come from AAP_USER / AAP_PASS in the environment. The password is
never printed or written to disk. The authenticated session is persisted with
Playwright storageState so later runs skip re-login.

Windows: the site reports rolling 7-day, 30-day, and all-time (since Jul 1
2008) counts, and a 7-day click-through rate. Data has an ~1-day nightly delay.
Each snapshot stores all three windows; the dashboard-compatible fields
hits/views/ctr alias the 7-day window (the weekly equivalent).

Usage:
    uv run aap_pet_stats.py [--headed] [--project-dir DIR] [--as-of YYYY-MM-DD]
                            [--period-days N] [--dump-html]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

from lxml import html as lh
from playwright.sync_api import sync_playwright

LOGIN_URL = (
    "https://www.adoptapet.com/account/login/as_publicist"
    "?return_url=http%3A%2F%2Fwww.adoptapet.com%2Fshelter%2Fpet-reports%2Fview_pet_stats"
)
STATS_URL = "https://www.adoptapet.com/shelter/pet-reports/view_pet_stats"
FAIL_MARKERS = ("Grrrr! Hisssss!", "does not jibe with our records")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


# ----------------------------- parsing --------------------------------------

def _to_int(s):
    s = (s or "").strip().replace(",", "")
    return int(s) if re.fullmatch(r"\d+", s) else None


def _iso_date(s):
    m = re.search(r"([A-Za-z]{3})\w*\s+(\d{1,2}),\s+(\d{4})", s or "")
    if not m:
        return (s or "").strip() or None
    return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).title()]:02d}-{int(m.group(2)):02d}"


def parse_pets(page_html):
    """Parse one view_pet_stats page into a list of per-pet dicts.

    lxml normalizes the malformed 2008-era table markup into clean
    one-pet-per-<tr> rows. Each data row carries a right_blue count cell; the
    six count cells [hits7, hits30, hits_all, views7, views30, views_all]
    immediately precede the CTR ("N%") cell.
    """
    tree = lh.fromstring(page_html)
    pets = []
    xp = "//tr[td[contains(concat(' ',normalize-space(@class),' '),' right_blue ')]]"
    for tr in tree.xpath(xp):
        tds = tr.xpath("./td")
        texts = [(td.text_content() or "").strip() for td in tds]

        rank = next((int(m.group(1)) for t in texts
                     if (m := re.fullmatch(r"(\d+)\.", t))), None)

        anchors = tr.xpath(".//a[contains(@class,'links-body')]")
        name = anchors[0].text_content().strip() if anchors else None
        pet_id = next((int(a.text_content().strip().replace(",", ""))
                       for a in anchors
                       if a.text_content().strip().replace(",", "").isdigit()), None)
        if pet_id is None:
            continue

        species = breed = date_added = None
        for td in tds:
            txt = td.text_content() or ""
            if re.search(r"[A-Za-z]{3}\s+\d{1,2},\s+\d{4}", txt):
                lines = [re.sub(r"\s+", " ", x).strip()
                         for x in re.split(r"[\n\r]+", txt) if x.strip()]
                if lines:
                    species = lines[0].lower()
                    date_added = _iso_date(lines[-1])
                    breed = " / ".join(lines[1:-1]) if len(lines) > 2 else (
                        lines[1] if len(lines) > 1 else None)
                break

        ctr_idx = next((i for i, t in enumerate(texts) if re.search(r"[\d.]+\s*%", t)), None)
        ctr = None
        counts = [None] * 6
        if ctr_idx is not None:
            m = re.search(r"([\d.]+)\s*%", texts[ctr_idx])
            ctr = float(m.group(1)) if m else None
            block = texts[max(0, ctr_idx - 6):ctr_idx]
            counts = [_to_int(x) for x in block] + [None] * (6 - len(block))
        h7, h30, hall, v7, v30, vall = counts

        pets.append({
            "rank": rank, "id": pet_id, "name": name, "species": species,
            "breed": breed, "date_added": date_added,
            "hits_7d": h7, "hits_30d": h30, "hits_all": hall,
            "views_7d": v7, "views_30d": v30, "views_all": vall, "ctr_7d": ctr,
        })
    return pets


def page_count(page_html):
    """Number of pages in the report, from the ?current_page=N links (>=1)."""
    nums = [int(n) for n in re.findall(r"current_page=(\d+)", page_html)]
    return max(nums) if nums else 1


# ----------------------------- login ----------------------------------------

def _is_login_page(page):
    return page.locator("input#email").count() > 0


def _do_login(page):
    """Single login attempt. Raises SystemExit on failure; never retries twice."""
    print("[login] loading login page", file=sys.stderr)
    page.goto(LOGIN_URL, wait_until="load")
    page.fill("input#email", os.environ["AAP_USER"])
    page.fill("input#password", os.environ["AAP_PASS"])
    print("[login] submitting login form (the only POST this tool issues)", file=sys.stderr)
    page.click("input[name='button']")
    page.wait_for_load_state("load")
    body = page.content()
    for marker in FAIL_MARKERS:
        if marker in body:
            raise SystemExit(
                f"[login] FAILED: '{marker}' present. Stopping without retry "
                "(repeated failures can lock the account). Verify AAP_USER / AAP_PASS."
            )


# ----------------------------- main -----------------------------------------

def build_record(p, as_of, period_start, period_end):
    """One pet's snapshot record: all three windows + dashboard-aliased fields.

    `as_of` (the pull date) is the record's identity. Runs at any cadence each
    produce a distinct as_of sample. The all-time cumulative counters
    (hits_all / views_all) are monotonic, so activity between two irregularly
    spaced runs is exactly their cumulative delta, independent of the gap.
    """
    return {
        "id": p["id"], "name": p["name"], "species": p["species"],
        "breed": p["breed"], "date_added": p["date_added"],
        "as_of": as_of, "source": "view_pet_stats",
        # dashboard-compatible fields (alias the 7-day / weekly window)
        "hits": p["hits_7d"], "views": p["views_7d"], "ctr": p["ctr_7d"],
        # full three-window detail (lossless; remap 'hits'/'views'/'ctr' later if desired)
        "hits_7d": p["hits_7d"], "hits_30d": p["hits_30d"], "hits_all": p["hits_all"],
        "views_7d": p["views_7d"], "views_30d": p["views_30d"], "views_all": p["views_all"],
        "ctr_7d": p["ctr_7d"],
        "rank": p["rank"],
        # 7-day rolling window the sample describes (ends at as_of)
        "period": f"{period_start}/{period_end}",
        "period_start": period_start, "period_end": period_end,
    }


def reconcile_ctr(pets):
    """Flag rows where the 7-day CTR != views7/hits7 (site caps at 100%)."""
    flags = []
    for p in pets:
        h, v, c = p["hits_7d"], p["views_7d"], p["ctr_7d"]
        if h and c is not None:
            exp = min(100.0, round(v / h * 100, 1))
            if abs(exp - c) > 0.2:
                flags.append({"id": p["id"], "name": p["name"],
                              "hits_7d": h, "views_7d": v, "ctr_7d": c, "expected": exp})
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true", help="run the browser headed")
    ap.add_argument("--project-dir", default=".", help="root for .aap-session.json and data/")
    ap.add_argument("--as-of", default=None, help="period end date YYYY-MM-DD (default: today)")
    ap.add_argument("--period-days", type=int, default=7, help="window length for the label")
    ap.add_argument("--dump-html", action="store_true", help="also save raw page HTML")
    ap.add_argument("--allow-count-swing", action="store_true",
                    help="skip the pet-count sanity gate (accept a large change vs the last run)")
    args = ap.parse_args()

    if not os.environ.get("AAP_USER") or not os.environ.get("AAP_PASS"):
        raise SystemExit(
            "AAP_USER and/or AAP_PASS is not set (the Adopt-a-Pet shelter login).\n\n"
            "Run it inline, e.g.:\n"
            "    AAP_USER='shelter-login-email' AAP_PASS='shelter-password' "
            "uv run analytics/aap_pet_stats.py\n\n"
            "The tool never prints or stores the password.")

    root = Path(args.project_dir).resolve()
    state_file = root / ".aap-session.json"
    data_dir = root / "data" / "aap-stats"
    data_dir.mkdir(parents=True, exist_ok=True)

    end = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    start = end - dt.timedelta(days=args.period_days - 1)
    period_start, period_end = start.isoformat(), end.isoformat()

    all_pets = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed,
                                     chromium_sandbox=False, args=["--no-sandbox"])
        ctx_kwargs = {"user_agent": USER_AGENT, "locale": "en-US",
                      "viewport": {"width": 1400, "height": 1000}}
        if state_file.exists():
            ctx_kwargs["storage_state"] = str(state_file)
        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        page.set_default_navigation_timeout(60000)
        page.set_default_timeout(60000)

        # Authenticate (login only if the saved session is missing/expired).
        if state_file.exists():
            page.goto(STATS_URL, wait_until="load")
            if _is_login_page(page):
                print("[session] saved session expired -> logging in", file=sys.stderr)
                _do_login(page)
        else:
            print("[session] no saved session -> logging in", file=sys.stderr)
            _do_login(page)
        if STATS_URL not in page.url:
            page.goto(STATS_URL, wait_until="load")
        if _is_login_page(page):
            raise SystemExit("[session] still on login page after one attempt. Stopping.")
        ctx.storage_state(path=str(state_file))
        print(f"[session] authenticated; state saved -> {state_file}", file=sys.stderr)

        # Page 1 is already loaded; discover total page count, then walk the rest.
        html1 = page.content()
        n_pages = page_count(html1)
        print(f"[report] {n_pages} page(s) detected", file=sys.stderr)
        pages_html = {1: html1}
        for pg in range(2, n_pages + 1):
            time.sleep(0.7)  # polite pacing
            page.goto(f"{STATS_URL}?current_page={pg}", wait_until="load")
            pages_html[pg] = page.content()
            print(f"[report] fetched page {pg}/{n_pages}", file=sys.stderr)

        ctx.close()
        browser.close()

    for pg in sorted(pages_html):
        pets = parse_pets(pages_html[pg])
        print(f"[parse] page {pg}: {len(pets)} pets", file=sys.stderr)
        all_pets.extend(pets)
        if args.dump_html:
            (data_dir / f"_raw_page{pg}_{period_end}.html").write_text(
                pages_html[pg], encoding="utf-8")

    # De-duplicate by id (defensive; a pet appears once per report).
    by_id = {}
    for p in all_pets:
        by_id.setdefault(p["id"], p)
    pets = sorted(by_id.values(), key=lambda p: (p["rank"] is None, p["rank"]))
    print(f"[parse] total distinct pets: {len(pets)}", file=sys.stderr)

    ctr_flags = reconcile_ctr(pets)
    as_of = period_end  # the pull date is the sample's identity

    def wsum(key):
        return sum(p[key] or 0 for p in pets)

    # Load existing history up front to compute the gap since the last run
    # (supports irregular cadence: weekly, 10 days, 2 days, whatever).
    hist_file = data_dir / "history.json"
    history = {}
    if hist_file.exists():
        history = json.loads(hist_file.read_text(encoding="utf-8"))
    prior_as_ofs = sorted({r.get("as_of") for r in history.values()
                           if r.get("as_of") and r["as_of"] < as_of})
    days_since_prev = ((end - dt.date.fromisoformat(prior_as_ofs[-1])).days
                       if prior_as_ofs else None)

    # Parse-sanity gate: a change to the report's markup could make parse_pets return
    # zero or a wildly wrong count. Writing that into history would silently corrupt the
    # longitudinal trend, so stop loudly and write nothing instead.
    if len(pets) == 0:
        raise SystemExit(
            "[abort] parsed 0 pets — the report markup likely changed, or the page did not "
            "load. Nothing written. Re-run with --dump-html to inspect the saved page.")
    if prior_as_ofs:
        prev_count = sum(1 for r in history.values() if r.get("as_of") == prior_as_ofs[-1])
        if prev_count and not (0.5 <= len(pets) / prev_count <= 2.0) and not args.allow_count_swing:
            raise SystemExit(
                f"[abort] parsed {len(pets)} pets, implausible vs the last run ({prev_count} on "
                f"{prior_as_ofs[-1]}). Likely a partial fetch or a markup change. Nothing written. "
                "If this swing is real, re-run with --allow-count-swing.")

    snapshot = {
        "meta": {
            "source": "adoptapet.com — Individual Pet Stats (view_pet_stats)",
            "shelter": "Friends of Homeless Animals",
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "as_of": as_of,
            "days_since_previous_run": days_since_prev,
            "period": f"{period_start}/{period_end}",
            "period_start": period_start, "period_end": period_end,
            "window_note": ("Counts are the site's rolling windows (7-day, 30-day, "
                            "all-time since 2008-07-01); data has an ~1-day nightly delay. "
                            "hits/views/ctr alias the 7-day window. For irregular run "
                            "cadence, use the monotonic all-time counters (hits_all / "
                            "views_all): activity between two runs is their cumulative "
                            "delta, independent of the interval."),
            "pages_fetched": len(pages_html),
            "pet_count": len(pets),
            "totals_listed_pets": {
                "hits_7d": wsum("hits_7d"), "hits_30d": wsum("hits_30d"),
                "views_7d": wsum("views_7d"), "views_30d": wsum("views_30d"),
            },
            "totals_note": ("Sums across the listed Adopt-a-Pet pets only. NOT the "
                            "partner-site-inclusive org-wide totals shown on the Overall "
                            "Pet Stats page / weekly emails."),
            "ctr7_reconciliation_flags": ctr_flags,
        },
        "pets": {str(p["id"]): build_record(p, as_of, period_start, period_end) for p in pets},
    }

    snap_file = data_dir / f"{start:%Y%m%d}_{end:%Y%m%d}.json"
    snap_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"[write] snapshot -> {snap_file}")

    # Append to the combined rolling history, keyed by (id, as_of); idempotent.
    # Re-running for the same pull date overwrites that day's rows (dedup);
    # different pull dates accumulate, so any run cadence >1 day builds history.
    added = 0
    for pid, rec in snapshot["pets"].items():
        key = f"{pid}|{as_of}"
        if key not in history:
            added += 1
        history[key] = rec
    hist_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"[write] history -> {hist_file} (+{added} new, {len(history)} total keys)")

    print(f"[done] {len(pets)} pets, period {period_start}..{period_end}, "
          f"CTR flags: {len(ctr_flags)}")
    if ctr_flags:
        print("[warn] CTR reconciliation flags:", file=sys.stderr)
        for f in ctr_flags:
            print("   ", f, file=sys.stderr)


if __name__ == "__main__":
    main()
