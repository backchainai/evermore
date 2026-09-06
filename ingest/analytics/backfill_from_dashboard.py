# /// script
# requires-python = ">=3.11"
# ///
"""
One-time backfill of the two PDF-era weeks into the aap-stats history.

The dashboard (FOHA Weekly Stats Dashboard.html) embeds a `PETS` array parsed
from the two emailed Adopt-a-Pet weekly PDFs:
  - current-week fields  (hits / views / ctr)   -> week ending 2026-06-22
  - previous-week fields (phits / pviews / pctr) -> week ending 2026-06-15

This rebuilds both as snapshots in the aap_pet_stats.py schema and merges them,
plus the existing live snapshot, into a single consistent history.json.

Provenance: PDF weeks carry only the weekly figure (no 30-day, all-time, or
cumulative counters), so those fields are null and source="weekly_email_pdf".
Estimates are never written here; history stays observed-only.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
DASH = HERE / "FOHA Weekly Stats Dashboard.html"
DATA = PROJ / "data" / "aap-stats"

# (as_of end date, period start, hits key, views key, ctr key, status to exclude)
WEEKS = [
    ("2026-06-15", "2026-06-09", "phits", "pviews", "pctr", "new"),     # prev-week fields
    ("2026-06-22", "2026-06-16", "hits", "views", "ctr", "dropped"),    # cur-week fields
]


def load_dashboard_pets():
    html = DASH.read_text(encoding="utf-8")
    m = re.search(r"const PETS=(\[.*?\]);", html, re.S)
    return json.loads(m.group(1))


def record(p, as_of, period_start, period_end, hk, vk, ck):
    h, v, c = p.get(hk), p.get(vk), p.get(ck)
    return {
        "id": p["id"], "name": p["name"], "species": p["species"],
        "breed": p["breed"], "date_added": p["date_added"],
        "as_of": as_of, "source": "weekly_email_pdf",
        "hits": h, "views": v, "ctr": c,
        "hits_7d": h, "hits_30d": None, "hits_all": None,
        "views_7d": v, "views_30d": None, "views_all": None,
        "ctr_7d": c,
        "rank": None,  # web "rank" is display order, not a performance rank
        "period": f"{period_start}/{period_end}",
        "period_start": period_start, "period_end": period_end,
    }


def reconcile_flags(recs):
    flags = []
    for r in recs:
        h, v, c = r["hits_7d"], r["views_7d"], r["ctr_7d"]
        if h and c is not None:
            exp = min(100.0, round(v / h * 100, 1))
            if abs(exp - c) > 0.2:
                flags.append({"id": r["id"], "name": r["name"],
                              "hits_7d": h, "views_7d": v, "ctr_7d": c, "expected": exp})
    return flags


def write_snapshot(as_of, period_start, recs, prev_as_of):
    days = None
    if prev_as_of:
        from datetime import date
        days = (date.fromisoformat(as_of) - date.fromisoformat(prev_as_of)).days
    snap = {
        "meta": {
            "source": "adopt-a-pet weekly email PDF (backfilled from dashboard PETS array)",
            "shelter": "Friends of Homeless Animals",
            "generated_at": None,
            "as_of": as_of,
            "days_since_previous_run": days,
            "period": f"{period_start}/{as_of}",
            "period_start": period_start, "period_end": as_of,
            "window_note": ("Backfill from the emailed weekly PDF: only the weekly figure "
                            "exists (mapped to the 7-day fields). 30-day, all-time, and "
                            "cumulative counters were not in this source and are null."),
            "pet_count": len(recs),
            "totals_listed_pets": {
                "hits_7d": sum(r["hits_7d"] or 0 for r in recs),
                "views_7d": sum(r["views_7d"] or 0 for r in recs),
            },
            "ctr7_reconciliation_flags": reconcile_flags(recs),
        },
        "pets": {str(r["id"]): r for r in recs},
    }
    start_c = period_start.replace("-", "")
    end_c = as_of.replace("-", "")
    (DATA / f"{start_c}_{end_c}.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return snap


def main():
    # Guard: this one-shot SEED rebuilds history.json from scratch, deriving the two
    # PDF weeks from the dashboard's current pet array. Once the dashboard has been
    # rebuilt from live data, that array no longer holds the PDF-week values, so a
    # re-run reconstructs the wrong numbers AND drops every later weekly pull. Any
    # existing history means the seed is already applied — refuse unless forced.
    hist_file = DATA / "history.json"
    if hist_file.exists() and "--force" not in sys.argv:
        existing = sorted({r.get("as_of") for r in json.loads(
            hist_file.read_text(encoding="utf-8")).values() if r.get("as_of")})
        raise SystemExit(
            "[backfill] REFUSING TO RUN. history.json already exists (weeks: "
            f"{existing}). This is a one-time seed; re-running rebuilds history from the "
            "current dashboard and would corrupt the PDF weeks and delete later pulls. "
            "The backfill is already applied; normal weekly operation never needs it. "
            "(Override with --force only to rebuild the seed from scratch.)")

    pets = load_dashboard_pets()
    built = {}  # as_of -> list of records
    prev = None
    for as_of, start, hk, vk, ck, exclude in WEEKS:
        recs = []
        for p in pets:
            if p["status"] == exclude:
                continue
            if p.get(hk) is None and p.get(vk) is None:
                continue
            recs.append(record(p, as_of, start, as_of, hk, vk, ck))
        snap = write_snapshot(as_of, start, recs, prev)
        built[as_of] = recs
        prev = as_of
        print(f"[backfill] week ending {as_of}: {len(recs)} pets, "
              f"CTR flags {len(snap['meta']['ctr7_reconciliation_flags'])}")

    # Patch the existing live snapshot to add source + correct gap, then rebuild history.
    live_recs = []
    live_file = DATA / "20260709_20260715.json"
    if live_file.exists():
        live = json.loads(live_file.read_text(encoding="utf-8"))
        for r in live["pets"].values():
            r.setdefault("source", "view_pet_stats")
            live_recs.append(r)
        live["meta"]["days_since_previous_run"] = (
            (__import__("datetime").date.fromisoformat("2026-07-15")
             - __import__("datetime").date.fromisoformat(prev)).days)
        live_file.write_text(json.dumps(live, indent=2), encoding="utf-8")
        print(f"[backfill] patched live snapshot (source + gap {live['meta']['days_since_previous_run']}d)")

    # Rebuild history.json cleanly: backfill weeks + live, keyed id|as_of.
    history = {}
    for as_of in sorted(built):
        for r in built[as_of]:
            history[f'{r["id"]}|{as_of}'] = r
    for r in live_recs:
        history[f'{r["id"]}|{r["as_of"]}'] = r
    (DATA / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    import collections
    per = collections.Counter(k.split("|")[1] for k in history)
    print(f"[backfill] history.json rebuilt: {len(history)} keys, per as_of {dict(sorted(per.items()))}")


if __name__ == "__main__":
    main()
