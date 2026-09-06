# /// script
# requires-python = ">=3.11"
# ///
"""
Regenerate the FOHA Weekly Stats Dashboard from data/aap-stats/history.json.

Run after each weekly extraction:
    uv run analytics/aap_pet_stats.py
    uv run analytics/build_dashboard.py

The dashboard is a self-contained HTML file with the data embedded (browsers
block fetch() of local files under file://), so it is rebuilt in place.

Design:
  - CTR is the emphasized hero chart (the headline listing-quality signal:
    how often a search impression becomes a profile open).
  - Detail-page views and search appearances are shown as their own charts too
    (nothing hidden behind toggles) so the page exports cleanly to PDF.
  - The trend x-axis is weekly, anchored to Mondays. Weeks with no capture are
    estimated and clearly denoted (hollow, dashed). Gap estimates are grounded
    in the later real week's 30-day counter where available, else linearly
    interpolated between captured weeks. Estimates are never written to
    history.json, which stays observed-only.
  - A print stylesheet switches to a compact light theme, drops interactive
    controls, and page-breaks the per-pet table into an appendix.
"""
import datetime as dt
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
HIST = PROJ / "data" / "aap-stats" / "history.json"
OUT = HERE / "FOHA Weekly Stats Dashboard.html"

# The trend charts show a trailing window of history (the goal is a rolling
# 90-day view). KPIs / table / movers remain latest-vs-prior and are unaffected.
TREND_WINDOW_DAYS = 90

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
          "Aug", "Sep", "Oct", "Nov", "Dec"]


def short_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{MONTHS[d.month]} {d.day}"


def long_date(iso):
    """Long form with weekday, e.g. 'Tuesday, June 9, 2026'."""
    d = dt.date.fromisoformat(iso)
    return d.strftime("%A, %B ") + f"{d.day}, {d.year}"


def monday_of(iso):
    d = dt.date.fromisoformat(iso)
    return d - dt.timedelta(days=d.weekday())


def hv(rec):
    """Weekly hits/views for a record (7-day fields, falling back to aliases)."""
    return (rec.get("hits_7d", rec.get("hits")) or 0), (rec.get("views_7d", rec.get("views")) or 0)


def ctr(v, h):
    return round(v / h * 100, 1) if h else 0


def main():
    history = json.loads(HIST.read_text(encoding="utf-8"))

    # Group records by as_of (one bucket per captured week).
    weeks = {}
    for rec in history.values():
        weeks.setdefault(rec["as_of"], []).append(rec)
    week_dates = sorted(weeks)

    # Per-captured-week shelter-wide aggregates, anchored to the week's Monday.
    real = {}
    for as_of in week_dates:
        recs = weeks[as_of]
        H = sum(hv(r)[0] for r in recs)
        V = sum(hv(r)[1] for r in recs)
        real[monday_of(as_of).isoformat()] = {
            "as_of": as_of, "hits": H, "views": V, "ctr": ctr(V, H),
            "h30": sum((r.get("hits_30d") or 0) for r in recs),
            "v30": sum((r.get("views_30d") or 0) for r in recs),
        }

    # Build a continuous weekly Monday series; fill uncaptured Mondays with
    # denoted estimates.
    real_mondays = sorted(dt.date.fromisoformat(m) for m in real)
    trend = []
    if real_mondays:
        m = real_mondays[0]
        end = real_mondays[-1]
        while m <= end:
            key = m.isoformat()
            if key in real:
                r = real[key]
                trend.append({"date": key, "label": short_date(key),
                              "ctr": r["ctr"], "views": r["views"], "hits": r["hits"],
                              "estimated": False})
            else:
                trend.append(estimate_week(m, real, real_mondays))
            m += dt.timedelta(days=7)
        # Window the trend to the trailing 90 days (keep the full history on disk).
        cutoff = end - dt.timedelta(days=TREND_WINDOW_DAYS)
        trend = [t for t in trend if dt.date.fromisoformat(t["date"]) >= cutoff]

    # Latest-vs-prior per-pet view for the KPIs / table / movers.
    latest, prior = week_dates[-1], (week_dates[-2] if len(week_dates) > 1 else None)
    cur = {r["id"]: r for r in weeks[latest]}
    prev = {r["id"]: r for r in weeks[prior]} if prior else {}
    pets = []
    for pid, r in cur.items():
        h, v = hv(r)
        p = prev.get(pid)
        if p:
            ph, pv = hv(p)
            pets.append({**base(r), "hits": h, "views": v, "ctr": r.get("ctr_7d", r.get("ctr")),
                         "phits": ph, "pviews": pv, "pctr": p.get("ctr_7d", p.get("ctr")),
                         "status": "returning", "dviews": v - pv, "dhits": h - ph})
        else:
            pets.append({**base(r), "hits": h, "views": v, "ctr": r.get("ctr_7d", r.get("ctr")),
                         "phits": None, "pviews": None, "pctr": None,
                         "status": "new", "dviews": None, "dhits": None})
    for pid, p in prev.items():
        if pid not in cur:
            ph, pv = hv(p)
            pets.append({**base(p), "hits": None, "views": None, "ctr": None,
                         "phits": ph, "pviews": pv, "pctr": p.get("ctr_7d", p.get("ctr")),
                         "status": "dropped", "dviews": None, "dhits": None})

    latest_rec = weeks[latest][0]
    latest_range = (f"{short_date(latest_rec['period_start'])}&ndash;{short_date(latest)}, "
                    f"{latest[:4]}") if latest_rec.get("period_start") else short_date(latest)
    prior_range = short_date(prior) if prior else None

    # View movers over the past ~2 weeks: compare the latest week to the capture
    # nearest 14 days back (adjusts the timeframe rather than using 1 week back).
    target = dt.date.fromisoformat(latest) - dt.timedelta(days=14)
    cands = [w for w in week_dates if w != latest]
    mref = min(cands, key=lambda w: abs((dt.date.fromisoformat(w) - target).days)) if cands else None
    movers = []
    if mref:
        refv = {r["id"]: hv(r)[1] for r in weeks[mref]}
        for r in weeks[latest]:
            if r["id"] in refv:
                v = hv(r)[1]
                movers.append({"name": r["name"], "pviews": refv[r["id"]],
                               "views": v, "dviews": v - refv[r["id"]]})
    movers_title = ("Biggest movers in detail-page views &mdash; past 2 weeks"
                    + (f" (vs week ending {short_date(mref)})" if mref else "")
                    + "<span class=\"sub2\">Largest week-over-week change in profile opens, across "
                      "all listed dogs and cats. Each row shows prior &rarr; current views.</span>")

    # Header states the timeframe the data covers: earliest captured week start
    # through the latest pull date.
    first_rec = weeks[week_dates[0]][0]
    span_start = first_rec.get("period_start") or week_dates[0]
    header_sub = f"{long_date(span_start)} &ndash; {long_date(latest)}"
    kpi_head = f"Most recent week &mdash; {latest_range}"

    # Roster size at each captured weekly sample, oldest first (population over time).
    roster_series = [{"label": short_date(a), "count": len(weeks[a])} for a in week_dates]

    foot = (
        "<strong>Hits</strong> = search-result appearances. <strong>Views</strong> = "
        "detail-page opens. <strong>CTR</strong> = Views &divide; Hits (capped at 100%), "
        "the headline listing-quality signal. All KPI cards below describe the most recent "
        "captured week only. The trend charts step weekly by Monday; a "
        "<span style=\"opacity:.7\">hollow, dashed</span> point is an <em>estimated</em> "
        "week with no capture (grounded in the following real week's 30-day counter where "
        "available, otherwise interpolated between captured weeks). &Delta; columns and KPI "
        "deltas compare the latest week to the prior <em>captured</em> week"
        + (f" (ending {prior})" if prior else "") + "; pets are matched by I.D.#.<br>"
        "Sources: weeks through 2026-06-22 backfilled from the Adopt-a-Pet weekly email "
        "PDFs; 2026-07-15 onward pulled live from the Adopt-a-Pet Individual Pet Stats "
        "report. Estimated weeks are presentation-only and are never written to the stored "
        "history. Per-pet figures cover Adopt-a-Pet.com only, not partner-site-inclusive "
        "org totals."
    )

    html = (TEMPLATE
            .replace("__WEEKS_JSON__", json.dumps(trend))
            .replace("__PETS_JSON__", json.dumps(pets))
            .replace("__MOVERS_JSON__", json.dumps(movers))
            .replace("__ROSTER_JSON__", json.dumps(roster_series))
            .replace("__MOVERS_TITLE__", movers_title)
            .replace("__HEADER_SUB__", header_sub)
            .replace("__KPI_HEAD__", kpi_head)
            .replace("__FOOT_HTML__", foot)
            .replace("__GENERATED__", dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")))
    OUT.write_text(html, encoding="utf-8")
    print(f"[dashboard] wrote {OUT.name}")
    for t in trend:
        tag = " (est)" if t["estimated"] else ""
        print(f'  {t["label"]:>7}  CTR {t["ctr"]:>4}%  views {t["views"]:>6}  hits {t["hits"]:>7}{tag}')


def estimate_week(m, real, real_mondays):
    """Estimate an uncaptured Monday. Prefer the next real week's 30-day counter
    (it spans the gap); else linearly interpolate between bracketing weeks."""
    prevs = [d for d in real_mondays if d < m]
    nexts = [d for d in real_mondays if d > m]
    key = m.isoformat()
    if prevs and nexts:
        a, b = real[prevs[-1].isoformat()], real[nexts[0].isoformat()]
        gap_days = (nexts[0] - prevs[-1]).days
        if b["h30"] > 0 and gap_days > 7:
            win = 30 - 7 - 7  # days the 30-day window leaves for the gap
            gh, gv = b["h30"] - b["hits"] - a["hits"], b["v30"] - b["views"] - a["views"]
            if gh > 0:
                return {"date": key, "label": short_date(key),
                        "ctr": ctr(gv, gh), "hits": round(gh * 7 / win),
                        "views": round(gv * 7 / win), "estimated": True}
        frac = (m - prevs[-1]).days / gap_days
        lin = lambda k: round(a[k] + frac * (b[k] - a[k]))
        gh, gv = lin("hits"), lin("views")
        return {"date": key, "label": short_date(key), "ctr": ctr(gv, gh),
                "hits": gh, "views": gv, "estimated": True}
    src = real[(prevs[-1] if prevs else nexts[0]).isoformat()]
    return {"date": key, "label": short_date(key), "ctr": src["ctr"],
            "hits": src["hits"], "views": src["views"], "estimated": True}


def base(r):
    return {"id": r["id"], "name": r["name"], "species": r["species"],
            "breed": r["breed"], "date_added": r["date_added"]}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FOHA &middot; Adopt-a-Pet Listing Performance</title>
<style>
:root{
 /* Backchain light theme (brand palette) on a white canvas for efficient printing.
    cream/charcoal/gray/coral-deep + slate, with green/red as the brand status colors. */
 --bg:#ffffff;--panel:#fafaf8;--panel2:#f1ece3;--line:#d7d1c4;
 --txt:#41423d;--mut:#50636f;--accent:#a35945;--dog:#2f455b;--cat:#a35945;
 --dim:#cbc4b6;--up:#27ae60;--down:#c0392b;--new:#2f455b;--drop:#7c8a94;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 font-size:13px;line-height:1.45}
.wrap{max-width:1200px;margin:0 auto;padding:24px 20px 50px}
header h1{font-size:19px;margin:0 0 4px;font-weight:650;letter-spacing:.2px}
header .sub{color:var(--mut);font-size:12px}
.sec{margin:20px 0 8px;font-size:12px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.6px}
.kpigroups{display:flex;gap:22px;margin:8px 0 6px}
.kpigroup{flex:1;min-width:0}
.kpigroup+.kpigroup{border-left:1px solid var(--line);padding-left:22px}
.kpigroup-h{font-size:11px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.6px;margin:0 0 7px}
.kpis3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi .v{font-size:18px;font-weight:680;letter-spacing:.3px}
.kpi .v.accent{color:var(--accent)}
.kpi .l{color:var(--mut);font-size:12px;margin-top:3px}
.kpi .pc{font-size:13px;font-weight:680;margin-top:6px;color:var(--txt);letter-spacing:.2px}
.kpi .pc.lead{font-size:15px;margin-top:0;letter-spacing:.2px}
.kpi .pc.lead.accent{color:var(--accent)}
.kpi .pc .ar{margin:0 4px}
.kpi .pc.lead .ar{margin:0 5px;font-weight:700}
.kpi .d{font-size:11.5px;margin-top:2px;font-weight:600}
.up{color:var(--up)}.down{color:var(--down)}.flat{color:var(--mut)}
.divider{border:0;border-top:1px solid var(--line);margin:22px 0 6px}
.legend{display:flex;gap:16px;justify-content:center;margin-top:8px;font-size:11.5px;color:var(--mut)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h3{margin:0 0 10px;font-size:12px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.6px}
.card h3 .sub2{display:block;text-transform:none;letter-spacing:0;font-weight:400;color:var(--mut);font-size:11.5px;margin-top:3px}
.tall{grid-column:1/-1}
/* hero CTR emphasis */
.hero{border-color:var(--accent);border-width:1px;box-shadow:0 0 0 1px rgba(163,89,69,.28) inset}
.hero h3{color:var(--accent)}
.trend{margin:18px 0 4px}
.trend .charts{margin-top:12px}
.trendchart{width:100%;overflow-x:auto}
.trendchart svg{width:100%;height:auto;display:block;min-width:280px}
.tblhead{margin:24px 0 4px;font-size:15px;font-weight:650}
.tblsub{color:var(--mut);font-size:12px;margin:0 0 12px;max-width:900px}
.tr-axis{stroke:#b0a999;stroke-width:1}
.tr-grid{stroke:var(--line);stroke-width:1;stroke-dasharray:2 4;opacity:.8}
.tr-line{fill:none;stroke:var(--accent);stroke-width:2.5}
.tr-line.est{stroke-dasharray:5 5;opacity:.75}
.tr-line.v{stroke:var(--dog)}.tr-line.h{stroke:var(--cat)}
.tr-dot{fill:var(--accent);stroke:var(--bg);stroke-width:2}
.tr-dot.v{fill:var(--dog)}.tr-dot.h{fill:var(--cat)}
.tr-dot.est{fill:var(--bg);stroke-dasharray:3 3}
.tr-dot.est.ctr{stroke:var(--accent)}.tr-dot.est.v{stroke:var(--dog)}.tr-dot.est.h{stroke:var(--cat)}
.tr-lab{fill:var(--txt);font-size:12px;font-weight:600;text-anchor:middle}
.tr-lab.small{font-size:11.5px;font-weight:500}
.tr-lab.est{fill:var(--mut);font-weight:500}
.tr-x{fill:var(--mut);font-size:11.5px;text-anchor:middle}
.tr-y{fill:var(--mut);font-size:11px;text-anchor:end}
.tr-note{color:var(--mut);font-size:11px;margin-top:8px}
.bars{display:flex;flex-direction:column;gap:8px}
.brow{display:grid;grid-template-columns:130px 1fr 54px;align-items:center;gap:10px}
.brow .lbl{color:var(--mut);font-size:12px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track{background:var(--panel2);border-radius:4px;height:16px;overflow:hidden}
.fill{height:100%;border-radius:4px;min-width:2px}
.brow .val{font-size:12px;font-weight:600;text-align:left}
.dv{display:flex;flex-direction:column;gap:7px}
.dvrow{display:grid;grid-template-columns:120px 1fr 56px;align-items:center;gap:10px}
.dvrow .lbl{color:var(--mut);font-size:12px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dvtrack{position:relative;height:16px}
.dvaxis{position:absolute;left:50%;top:-2px;bottom:-2px;border-left:1px solid var(--line)}
.dvfill{position:absolute;top:0;height:100%;border-radius:3px;min-width:2px}
.dvrow .val{font-size:12px;font-weight:600}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
.controls input[type=search]{flex:1;min-width:200px;background:var(--panel2);border:1px solid var(--line);
 color:var(--txt);padding:9px 12px;border-radius:8px;font-size:13px}
.controls input::placeholder{color:var(--mut)}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{background:var(--panel2);color:var(--mut);border:0;padding:8px 12px;cursor:pointer;font-size:12.5px}
.seg button.on{background:var(--accent);color:#faf7f2;font-weight:600}
.count{color:var(--mut);font-size:12px;margin-left:auto}
.tbl-wrap{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:760px}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{position:sticky;top:0;background:var(--panel2);color:var(--mut);font-size:12px;font-weight:600;cursor:pointer;user-select:none}
th.num,td.num{text-align:right}
th .arr{opacity:.4;font-size:10.5px;margin-left:3px}
th.sort .arr{opacity:1;color:var(--accent)}
tbody tr:hover{background:#f2ede4}
td.name{font-weight:600;white-space:normal}
td.breed{color:var(--mut);white-space:normal;max-width:250px;font-size:12.5px}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}
.pill.dog{background:rgba(47,69,91,.12);color:var(--dog)}
.pill.cat{background:rgba(163,89,69,.13);color:var(--cat)}
.tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px}
.tag.new{background:rgba(47,69,91,.12);color:var(--new)}
.tag.dropped{background:rgba(80,99,111,.14);color:var(--drop)}
.tag.returning{color:var(--mut);opacity:.5}
.delta{font-size:11px;font-weight:600;margin-left:5px}
.muted{color:var(--mut)}
.foot{color:var(--mut);font-size:11px;margin-top:16px;line-height:1.55}
@media(max-width:760px){.charts{grid-template-columns:1fr}
 .kpigroups{flex-direction:column;gap:14px}
 .kpigroup+.kpigroup{border-left:0;border-top:1px solid var(--line);padding-left:0;padding-top:12px}}
@media print{
 /* Base theme is already the Backchain light theme; print only needs to force
    pure-white surfaces (zero background ink), keep the coral chart accents, and
    compact the layout. */
 *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
 body{font-size:10.5px}
 .wrap{max-width:none;padding:0}
 .controls{display:none!important}
 .card,.kpi,.tbl-wrap{background:#fff}
 th{background:#fff}
 .card,.kpi{box-shadow:none;break-inside:avoid}
 .hero{box-shadow:0 0 0 1px var(--accent) inset}
 .charts{gap:8px}
 .kpigroups{gap:14px;margin:6px 0}
 .kpigroup+.kpigroup{padding-left:14px}
 .kpis3{gap:7px}
 .kpi{padding:8px 10px}.kpi .v{font-size:15px}.kpi .pc.lead{font-size:13px}
 .divider{margin:10px 0 4px}
 .trend{margin:8px 0 4px}
 .sec{margin:12px 0 6px}
 table{min-width:0;font-size:9.5px}
 th,td{padding:3px 6px}
 thead{display:table-header-group}
 tr{break-inside:avoid}
 td.breed{max-width:190px}
 .tblhead{break-before:page}
 header h1{font-size:16px}
 .foot{margin-top:10px}
 @page{margin:11mm}
}
</style>
</head>
<body>
<div class="wrap">
<header>
 <h1>Friends Of Homeless Animals &middot; Adopt-a-Pet Listing Performance</h1>
 <div class="sub">__HEADER_SUB__</div>
</header>

<div class="trend">
 <div class="card tall hero">
  <h3>Click-through rate (CTR) = Views &divide; Hits
   <span class="sub2">Across all listed pets, the share of search appearances that led to someone opening a profile.</span></h3>
  <div id="cTrendctr" class="trendchart"></div>
  <div class="tr-note">Solid = captured weeks; hollow &amp; dashed = estimated weeks (no capture).</div>
 </div>
 <div class="charts">
  <div class="card"><h3>Search appearances &mdash; per week
   <span class="sub2">Total times listed pets showed up in search-results lists, summed across the roster.</span></h3>
   <div id="cTrendhits" class="trendchart"></div></div>
  <div class="card"><h3>Detail-page views &mdash; per week
   <span class="sub2">Total times someone opened a listed pet's profile page, summed across the roster.</span></h3>
   <div id="cTrendviews" class="trendchart"></div></div>
 </div>
</div>

<h3 class="sec">__KPI_HEAD__</h3>
<div class="kpigroups" id="kpis"></div>
<hr class="divider">

<div class="charts">
 <div class="card"><h3>Detail-page views by species &mdash; latest vs prior week</h3><div id="cSpecies"></div></div>
 <div class="card"><h3>Pets listed &mdash; week over week
  <span class="sub2">Total roster size at each weekly sample, oldest to newest &mdash; how the listed population changes over time.</span></h3><div id="cRoster"></div></div>
 <div class="card tall"><h3>__MOVERS_TITLE__</h3><div id="cMovers"></div></div>
</div>

<h3 class="tblhead">Where to focus &mdash; carried-over pets, fewest views first</h3>
<div class="tblsub">Defaulted to pets carried over from the prior week, sorted by fewest detail-page views: the long-listed animals getting the least search interest. This is the queue to work first (fresh photos, better descriptions, social pushes) to keep adoptions moving. Adjust the filters or sort to explore.</div>
<div class="controls">
 <input type="search" id="q" placeholder="Search name, breed, or ID&hellip;">
 <div class="seg" id="sp">
  <button data-sp="all" class="on">All</button><button data-sp="dog">Dogs</button><button data-sp="cat">Cats</button>
 </div>
 <div class="seg" id="st">
  <button data-st="all">Any</button><button data-st="returning" class="on">Carried over</button><button data-st="new">New</button><button data-st="dropped">Dropped</button>
 </div>
 <span class="count" id="count"></span>
</div>

<div class="tbl-wrap">
<table>
<thead><tr>
 <th data-k="name">Name<span class="arr">&#9650;</span></th>
 <th data-k="species">Type<span class="arr">&#9650;</span></th>
 <th data-k="breed">Breed(s)<span class="arr">&#9650;</span></th>
 <th class="num" data-k="hits">Hits<span class="arr">&#9650;</span></th>
 <th class="num" data-k="views">Views<span class="arr">&#9650;</span></th>
 <th class="num" data-k="dviews">&Delta; Views<span class="arr">&#9650;</span></th>
 <th class="num" data-k="ctr">CTR<span class="arr">&#9650;</span></th>
 <th data-k="status">Status<span class="arr">&#9650;</span></th>
</tr></thead>
<tbody id="tb"></tbody>
</table>
</div>

<div class="foot">
 __FOOT_HTML__<br>
 <span style="opacity:.7">Generated __GENERATED__ from data/aap-stats/history.json.</span>
</div>
</div>

<script>
const WEEKS=__WEEKS_JSON__;
const PETS=__PETS_JSON__;
const MOVERS=__MOVERS_JSON__;
const ROSTER=__ROSTER_JSON__;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cur=PETS.filter(p=>p.status!=="dropped");
const dropped=PETS.filter(p=>p.status==="dropped");
const ret=PETS.filter(p=>p.status==="returning");
const sum=(a,k)=>a.reduce((s,p)=>s+(p[k]||0),0);
const curViews=sum(cur,"views"),curHits=sum(cur,"hits");
const prevViews=sum(ret,"pviews")+sum(dropped,"pviews");
const prevHits=sum(ret,"phits")+sum(dropped,"phits");
const curCTR=curHits?curViews/curHits*100:0, prevCTR=prevHits?prevViews/prevHits*100:0;
const nNew=PETS.filter(p=>p.status==="new").length;
const nDrop=dropped.length;

function pct(c,p){return p?((c-p)/p*100):0;}
function fmtNum(n){const r=Math.round(n*10)/10;return Number.isInteger(r)?r.toString():r.toFixed(1);}
const F=x=>Number.isInteger(x)?x.toLocaleString():fmtNum(x);
function leadEl(c,p,suffix="",accent=false){
 const cls=c>p?"up":c<p?"down":"flat";
 return `<div class="pc lead${accent?' accent':''}">${F(p)}${suffix}<span class="ar ${cls}">→</span>${F(c)}${suffix}</div>`;
}
function chgEl(c,p,suffix=""){
 const d=Math.round((c-p)*10)/10, r=Math.round(pct(c,p));
 const cls=d>0?"up":d<0?"down":"flat";const ar=d>0?"▲":d<0?"▼":"–";
 return `<div class="d ${cls}">${ar} ${d>0?"+":""}${fmtNum(d)}${suffix} (${r>0?"+":""}${r}%) vs prior wk</div>`;
}
const STLABEL={returning:"Carried over",new:"New",dropped:"Dropped"};
function leadCTR(c,p){
 const cls=c>p?"up":c<p?"down":"flat";
 return `<div class="pc lead">${p.toFixed(1)}%<span class="ar ${cls}">→</span>${c.toFixed(1)}%</div>`;
}
function chgCTR(c,p){
 const cls=c>p?"up":c<p?"down":"flat";const ar=c>p?"▲":c<p?"▼":"–";
 const pp=Math.round((c-p)*10)/10;
 return `<div class="d ${cls}">${ar} ${pp>0?"+":""}${pp}pp vs prior wk</div>`;
}
// Two segments: pet roster (who is listed) and engagement (how listings performed).
const rosterKpis=[
 {v:nNew,l:"New this week"},
 {v:nDrop,l:"Dropped vs prior week"},
 {lead:leadEl(cur.length, ret.length+nDrop),l:"Pets listed",change:chgEl(cur.length, ret.length+nDrop)},
];
const engageKpis=[
 {lead:leadEl(curHits,prevHits),l:"Search appearances",change:chgEl(curHits,prevHits)},
 {lead:leadEl(curViews,prevViews,"",true),l:"Detail-page views",change:chgEl(curViews,prevViews)},
 {lead:leadCTR(curCTR,prevCTR),l:"Avg click-through",change:chgCTR(curCTR,prevCTR)},
];
const kpiCard=k=>{
 const lead=k.lead||`<div class="v">${k.v}</div>`;
 return `<div class="kpi">${lead}<div class="l">${k.l}</div>${k.change||""}</div>`;
};
const kpiGroup=(label,items)=>
 `<div class="kpigroup"><div class="kpigroup-h">${label}</div><div class="kpis3">${items.map(kpiCard).join("")}</div></div>`;
document.getElementById("kpis").innerHTML=
 kpiGroup("Pet roster",rosterKpis)+kpiGroup("Engagement",engageKpis);

// ---- weekly trend charts (inline SVG) ----
const METRIC={ctr:{fmt:v=>v+"%",cls:"ctr"},views:{fmt:v=>v.toLocaleString(),cls:"v"},hits:{fmt:v=>v.toLocaleString(),cls:"h"}};
// Round an axis step up to a 1/1.5/2/2.5/3/4/5/7.5/10 * 10^n value so ticks are clean.
function niceStep(x){const p=Math.pow(10,Math.floor(Math.log10(x)));const f=x/p;
 const n=f<=1?1:f<=1.5?1.5:f<=2?2:f<=2.5?2.5:f<=3?3:f<=4?4:f<=5?5:f<=7.5?7.5:10;return n*p;}
function renderTrend(elId,m,W,H,labelAll){
 const cfg=METRIC[m],padL=52,padR=18,padT=26,padB=30;
 const pts=WEEKS.map(w=>({...w,t:Date.parse(w.date),y:w[m]==null?null:w[m]})).filter(p=>p.y!=null);
 if(!pts.length){document.getElementById(elId).innerHTML="";return;}
 const xs=pts.map(p=>p.t),tmin=Math.min(...xs),tmax=Math.max(...xs);
 const ystep=niceStep((Math.max(...pts.map(p=>p.y))||1)*1.05/4),ymax=ystep*4;
 const X=t=>padL+(tmax===tmin?0.5:(t-tmin)/(tmax-tmin))*(W-padL-padR);
 const Y=v=>padT+(1-v/ymax)*(H-padT-padB);
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${m} over time">`;
 for(let i=0;i<=4;i++){const v=ymax*i/4,y=Y(v);
  svg+=`<line class="tr-grid" x1="${padL}" y1="${y.toFixed(1)}" x2="${W-padR}" y2="${y.toFixed(1)}"/>`
      +`<text class="tr-y" x="${padL-8}" y="${(y+4).toFixed(1)}">${cfg.fmt(Math.round(v*10)/10)}</text>`;}
 svg+=`<line class="tr-axis" x1="${padL}" y1="${padT}" x2="${padL}" y2="${H-padB}"/>`
     +`<line class="tr-axis" x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}"/>`;
 for(let i=0;i<pts.length-1;i++){const a=pts[i],b=pts[i+1];const est=a.estimated||b.estimated;
  svg+=`<line class="tr-line ${cfg.cls}${est?' est':''}" x1="${X(a.t).toFixed(1)}" y1="${Y(a.y).toFixed(1)}" x2="${X(b.t).toFixed(1)}" y2="${Y(b.y).toFixed(1)}"/>`;}
 const step=Math.max(1,Math.ceil(pts.length/9));
 pts.forEach((p,i)=>{const x=X(p.t),y=Y(p.y);
  svg+=`<circle class="tr-dot ${cfg.cls}${p.estimated?' est '+cfg.cls:''}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${p.estimated?4.5:5}"/>`;
  if(labelAll||p.estimated||i===0||i===pts.length-1){
   // Anchor edge labels inward so the first/last value never overlaps the y-axis ticks or the right edge.
   const anc=i===0?"start":i===pts.length-1?"end":"middle";
   const lx=i===0?x+3:i===pts.length-1?x-3:x;
   svg+=`<text class="tr-lab${labelAll?'':' small'}${p.estimated?' est':''}" style="text-anchor:${anc}" x="${lx.toFixed(1)}" y="${(y-11).toFixed(1)}">${cfg.fmt(p.y)}${p.estimated?" est":""}</text>`;}
  if(i%step===0||i===pts.length-1)
   svg+=`<text class="tr-x" x="${x.toFixed(1)}" y="${H-padB+16}">${esc(p.label)}</text>`;});
 svg+=`</svg>`;document.getElementById(elId).innerHTML=svg;
}
// Hero CTR spans the full width (W=900 scales up). The two half-width charts use a
// narrower viewBox (W=440) so their text is not shrunk when the SVG is scaled to the
// card, keeping labels legible on screen and in a 2-up print layout.
renderTrend("cTrendctr","ctr",900,320,true);
renderTrend("cTrendhits","hits",440,200,false);
renderTrend("cTrendviews","views",440,200,false);

function hbars(elId,items){
 const max=Math.max(1,...items.map(i=>i.value));
 document.getElementById(elId).innerHTML='<div class="bars">'+items.map(i=>
  `<div class="brow"><div class="lbl">${esc(i.label)}</div>
    <div class="track"><div class="fill" style="width:${(i.value/max*100).toFixed(1)}%;background:${i.color}"></div></div>
    <div class="val">${i.value.toLocaleString()}</div></div>`).join('')+'</div>';
}
function stackedBars(elId,groups){
 // Narrow viewBox (half-width card) so labels are not shrunk by SVG scaling.
 const W=440,H=230,padL=52,padR=14,padT=20,padB=40;
 const totals=groups.map(g=>g.segs.reduce((s,x)=>s+x.value,0));
 const ystep=niceStep(Math.max(1,...totals)*1.05/4),max=ystep*4;
 const gap=(W-padL-padR)/groups.length,bw=Math.min(150,gap*0.46);
 const Y=v=>padT+(1-v/max)*(H-padT-padB);
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Detail-page views by species, stacked prior vs latest">`;
 for(let i=0;i<=4;i++){const v=max*i/4,y=Y(v);
  svg+=`<line class="tr-grid" x1="${padL}" y1="${y.toFixed(1)}" x2="${W-padR}" y2="${y.toFixed(1)}"/>`
      +`<text class="tr-y" x="${padL-8}" y="${(y+4).toFixed(1)}">${Math.round(v).toLocaleString()}</text>`;}
 svg+=`<line class="tr-axis" x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}"/>`;
 groups.forEach((g,i)=>{const cx=padL+gap*i+gap/2,x=cx-bw/2;let acc=0;
  g.segs.forEach(seg=>{const y0=Y(acc),y1=Y(acc+seg.value),h=y0-y1;acc+=seg.value;
   if(seg.value>0){svg+=`<rect x="${x.toFixed(1)}" y="${y1.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0,h).toFixed(1)}" style="fill:${seg.color}"/>`;
    if(h>15)svg+=`<text class="tr-lab small" x="${cx.toFixed(1)}" y="${(y1+h/2+4).toFixed(1)}" style="fill:#fff">${seg.value.toLocaleString()}</text>`;}});
  const top=Y(acc);
  svg+=`<text class="tr-lab" x="${cx.toFixed(1)}" y="${(top-7).toFixed(1)}">${acc.toLocaleString()}</text>`
      +`<text class="tr-x" x="${cx.toFixed(1)}" y="${H-padB+16}">${esc(g.label)}</text>`;});
 svg+=`</svg><div class="legend"><span><i style="background:var(--dog)"></i>Dogs</span><span><i style="background:var(--cat)"></i>Cats</span></div>`;
 document.getElementById(elId).innerHTML=svg;
}
function spViews(sp,wk){return PETS.filter(p=>p.species===sp).reduce((s,p)=>s+((wk==="cur"?p.views:p.pviews)||0),0);}
stackedBars("cSpecies",[
 {label:"Prior week",segs:[{label:"Dogs",value:spViews("dog","prev"),color:"var(--dog)"},{label:"Cats",value:spViews("cat","prev"),color:"var(--cat)"}]},
 {label:"Latest week",segs:[{label:"Dogs",value:spViews("dog","cur"),color:"var(--dog)"},{label:"Cats",value:spViews("cat","cur"),color:"var(--cat)"}]},
]);
// Roster size per weekly sample, oldest at top → newest at bottom (latest highlighted).
hbars("cRoster",ROSTER.map((r,i)=>({label:r.label,value:r.count,
 color:i===ROSTER.length-1?"var(--accent)":"var(--dog)"})));

function movers(){
 const s=[...MOVERS].filter(p=>p.dviews!=null).sort((a,b)=>a.dviews-b.dviews);
 const sel=[...s.slice(0,6),...s.slice(-6)].filter((v,i,a)=>a.indexOf(v)===i).sort((a,b)=>b.dviews-a.dviews);
 const maxAbs=Math.max(1,...sel.map(p=>Math.abs(p.dviews)));
 document.getElementById("cMovers").innerHTML='<div class="dv">'+sel.map(p=>{
  const w=(Math.abs(p.dviews)/maxAbs*50).toFixed(1);const pos=p.dviews>=0;
  const fill=pos?`<div class="dvfill" style="left:50%;width:${w}%;background:var(--up)"></div>`
   :`<div class="dvfill" style="right:50%;width:${w}%;background:var(--down)"></div>`;
  return `<div class="dvrow"><div class="lbl">${esc(p.name)}</div>
   <div class="dvtrack"><div class="dvaxis"></div>${fill}</div>
   <div class="val ${pos?'up':'down'}">${p.pviews}→${p.views}</div></div>`;
 }).join('')+'</div>';
}
movers();

let sp="all",st="returning",q="",sortK="views",asc=true;
const tb=document.getElementById("tb");
function dCell(d){
 if(d===null||d===undefined)return '<span class="muted">&mdash;</span>';
 if(d===0)return '<span class="flat">0</span>';
 const cls=d>0?"up":"down";const ar=d>0?"▲":"▼";
 return `<span class="${cls}">${ar} ${d>0?"+":""}${d}</span>`;
}
function render(){
 let rows=PETS.filter(p=>(sp==="all"||p.species===sp)&&(st==="all"||p.status===st)&&
  (q===""||(p.name+" "+p.breed+" "+p.id).toLowerCase().includes(q)));
 rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];
  const xn=(x===null||x===undefined),yn=(y===null||y===undefined);
  if(xn&&yn)return 0; if(xn)return 1; if(yn)return -1;
  if(typeof x==="string"){x=x.toLowerCase();y=y.toLowerCase();return asc?(x<y?-1:x>y?1:0):(x>y?-1:x<y?1:0);}
  return asc?x-y:y-x;});
 tb.innerHTML=rows.map(p=>{
  const hits=p.hits===null?'<span class="muted">&mdash;</span>':p.hits+(p.dhits!==null?`<span class="delta ${p.dhits>0?'up':p.dhits<0?'down':'flat'}">${p.dhits>0?'+':''}${p.dhits}</span>`:'');
  const views=p.views===null?'<span class="muted">&mdash;</span>':p.views;
  const c=p.ctr===null?'<span class="muted">&mdash;</span>':p.ctr+'%';
  return `<tr>
   <td class="name">${esc(p.name)} <span class="muted" style="font-weight:400;font-size:11px">#${p.id}</span></td>
   <td><span class="pill ${p.species}">${p.species}</span></td>
   <td class="breed">${esc(p.breed)}</td>
   <td class="num">${hits}</td><td class="num">${views}</td>
   <td class="num">${dCell(p.dviews)}</td><td class="num">${c}</td>
   <td><span class="tag ${p.status}">${STLABEL[p.status]}</span></td>
  </tr>`;}).join("");
 document.getElementById("count").textContent=rows.length+" of "+PETS.length+" pets";
 document.querySelectorAll("th").forEach(th=>{th.classList.toggle("sort",th.dataset.k===sortK);
  const a=th.querySelector(".arr");if(a)a.innerHTML=th.dataset.k===sortK?(asc?"▲":"▼"):"▲";});
}
document.getElementById("q").addEventListener("input",e=>{q=e.target.value.toLowerCase().trim();render();});
function seg(id,setter){document.querySelectorAll("#"+id+" button").forEach(b=>b.addEventListener("click",()=>{
 document.querySelectorAll("#"+id+" button").forEach(x=>x.classList.remove("on"));
 b.classList.add("on");setter(b);render();}));}
seg("sp",b=>sp=b.dataset.sp);
seg("st",b=>st=b.dataset.st);
document.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{
 const k=th.dataset.k;if(k===sortK)asc=!asc;else{sortK=k;asc=(k==="name"||k==="breed"||k==="status");}
 render();}));
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
