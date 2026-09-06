"""Command-line entry point.

  grade scrape --species dog --limit 10        # Firecrawl -> data/raw/<slug>.json
  grade score  --runs 3 --out data/report.md   # parse + metrics + judge -> report
  grade run    --species dog --limit 10 --runs 3   # scrape + score in one shot

`score` reads whatever is cached in data/raw, so you can scrape once and re-score for
free while tuning the rubric.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import record as record_mod
from . import report as report_mod
from . import score as score_mod
from .judge import DEFAULT_MODEL, judge_profile
from .metrics import compute
from .parse import Profile, load_profile
from .scrape import scrape_batch

ROOT = Path(__file__).resolve().parents[1]  # profile-grader/ (tool root)
DATA = ROOT / "data"
RAW = DATA / "raw"
RESULTS = DATA / "results"
LEDGER = DATA / "scores.jsonl"


def _cmd_scrape(args: argparse.Namespace) -> int:
    results = scrape_batch(args.species, args.limit, RAW, refresh=args.refresh)
    for slug, url, path in results:
        print(f"  {slug:24} {url}")
    print(f"Scraped {len(results)} {args.species} profile(s) into {RAW}", file=sys.stderr)
    return 0


def _score_cached(
    runs: int, model: str, species: str
) -> tuple[list[score_mod.ProfileScore], dict[str, Profile], dict[str, str]]:
    paths = sorted(RAW.glob("*.json"))
    if not paths:
        raise SystemExit(f"No cached scrapes in {RAW}. Run `grade scrape` first.")
    scores: list[score_mod.ProfileScore] = []
    profiles: dict[str, Profile] = {}
    scraped_at: dict[str, str] = {}
    for path in paths:
        profile = load_profile(path, species=species)
        metrics = compute(profile)
        judged = judge_profile(profile, metrics, runs=runs, model=model)
        scores.append(score_mod.combine(profile, metrics, judged))
        profiles[profile.slug] = profile
        scraped_at[profile.slug] = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()
        print(f"  scored {profile.name or profile.slug}: {scores[-1].raw:.0f}/100", file=sys.stderr)
    score_mod.apply_cohort_percentiles(scores)
    return scores, profiles, scraped_at


def _cmd_score(args: argparse.Namespace) -> int:
    scores, profiles, scraped_at = _score_cached(args.runs, args.model, args.species)

    now = datetime.now().astimezone().isoformat()
    run_ctx = {"model": args.model, "judge_runs": args.runs, "run_id": now, "scored_at": now}
    record_mod.write_run(scores, profiles, run_ctx, RESULTS, LEDGER, scraped_at)
    print(f"Records written to {RESULTS} (index.json + {len(scores)} per-slug); "
          f"ledger appended to {LEDGER}", file=sys.stderr)

    out = report_mod.full_report(scores)
    if args.out:
        Path(args.out).write_text(out)
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    scrape_batch(args.species, args.limit, RAW, refresh=args.refresh)
    return _cmd_score(args)


def _cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve

    results = Path(args.data_dir) if args.data_dir else RESULTS
    if not (results / "index.json").is_file():
        print(f"No records in {results}. Run `grade score` first.", file=sys.stderr)
        return 1
    print(f"Dashboard: http://{args.host}:{args.port}  (records from {results})", file=sys.stderr)
    serve(results, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="grade", description="Grade FOHA adoption profiles.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--species", choices=["dog", "cat"], default="dog")
        sp.add_argument("--limit", type=int, default=10)
        sp.add_argument("--refresh", action="store_true", help="re-scrape even if cached")
        sp.add_argument("--runs", type=int, default=3, help="judge runs to average")
        sp.add_argument("--model", default=DEFAULT_MODEL)
        sp.add_argument("--out", default=None, help="write report here (default: stdout)")

    sp_scrape = sub.add_parser("scrape", help="Firecrawl profiles into the cache")
    sp_scrape.add_argument("--species", choices=["dog", "cat"], default="dog")
    sp_scrape.add_argument("--limit", type=int, default=10)
    sp_scrape.add_argument("--refresh", action="store_true")
    sp_scrape.set_defaults(func=_cmd_scrape)

    sp_score = sub.add_parser("score", help="Score cached scrapes into a report")
    sp_score.add_argument("--species", choices=["dog", "cat"], default="dog")
    sp_score.add_argument("--runs", type=int, default=3)
    sp_score.add_argument("--model", default=DEFAULT_MODEL)
    sp_score.add_argument("--out", default=None)
    sp_score.set_defaults(func=_cmd_score)

    sp_run = sub.add_parser("run", help="Scrape then score in one shot")
    add_common(sp_run)
    sp_run.set_defaults(func=_cmd_run)

    sp_serve = sub.add_parser("serve", help="Run the local dashboard server")
    sp_serve.add_argument("--host", default="127.0.0.1")
    sp_serve.add_argument("--port", type=int, default=8000)
    sp_serve.add_argument("--data-dir", default=None, help="results dir to serve (default: ./data/results)")
    sp_serve.set_defaults(func=_cmd_serve)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
