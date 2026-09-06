"""Server-route tests: the API contract, the slug/traversal guard, and error codes.

No network and no LLM: records are built from a fixture through the real
parse -> metrics -> score -> record pipeline, then served via a FileStore app.
A 200 on a route with a `response_model` also proves the record validates against the
pydantic contract in schema.py (FastAPI validates on the way out).
"""

from fastapi.testclient import TestClient

from profile_grader import record as record_mod
from profile_grader.metrics import compute
from profile_grader.parse import parse_scrape
from profile_grader.score import apply_cohort_percentiles, combine
from profile_grader.server import create_file_app

MD = """# Rex

Male
•
45 lbs

- **Breed** Mixed Breed
- **Age** 3yrs

### Meet Rex

**ABOUT THIS ANIMAL:**

Rex walks calmly on a loose leash and knows sit.

**HOW AM I WITH DOGS:**

Unknown.

**THINGS I STRUGGLE WITH:**

Counter surfing, but responds to redirection.

![Animal image](https://x/1.jpg)![Animal image](https://x/2.jpg)
"""


_TOPICS = ("about", "dogs", "cats", "kids", "training", "housebreaking", "likes", "struggles")


class _FakeJudge:
    scores = {
        "analytic_language": 3.0,
        "behavioral_concreteness": 3.0,
        "observed_not_promised": 4.0,
        "identity_opening": 2.0,
        "section_completeness": 4.0,  # judged from topic_coverage (all covered here)
    }
    score_runs = {k: [int(v)] for k, v in scores.items()}
    rationales = {k: "because" for k in scores}
    quotes = {k: "a quote" for k in scores}
    spread = {k: 0 for k in scores}
    tag_body_contradiction = False
    contradiction_note = ""
    max_spread = 0
    topic_coverage = {t: "covered" for t in _TOPICS}


def _results_dir(tmp_path):
    p = parse_scrape({"markdown": MD, "images": [], "metadata": {}}, slug="rex", species="dog")
    s = combine(p, compute(p), _FakeJudge())
    apply_cohort_percentiles([s])
    run_ctx = {"model": "claude-sonnet-5", "judge_runs": 1, "run_id": "R", "scored_at": "T"}
    results = tmp_path / "results"
    record_mod.write_run([s], {"rex": p}, run_ctx, results, tmp_path / "l.jsonl")
    return results


def _client(tmp_path):
    return TestClient(create_file_app(_results_dir(tmp_path)))


def test_index_ok(tmp_path):
    r = _client(tmp_path).get("/api/index")
    assert r.status_code == 200  # 200 also proves it validates against IndexResponse
    body = r.json()
    assert body["profiles"][0]["slug"] == "rex"
    assert body["bands"]["score"][0]["label"] == "Reference-worthy"
    assert len(body["dimensions"]) == 9


def test_profile_ok(tmp_path):
    r = _client(tmp_path).get("/api/profile/rex")
    assert r.status_code == 200  # validates against ProfileRecord
    assert r.json()["slug"] == "rex"


def test_unknown_slug_404(tmp_path):
    assert _client(tmp_path).get("/api/profile/ghost").status_code == 404


def test_reserved_index_slug_400(tmp_path):
    # `index` matches the slug shape but must not resolve to index.json.
    assert _client(tmp_path).get("/api/profile/index").status_code == 400


def test_bad_slugs_400(tmp_path):
    c = _client(tmp_path)
    for bad in ("Rex", "a.b", "a_b", "a..b"):
        assert c.get(f"/api/profile/{bad}").status_code == 400, bad


def test_root_serves_html(tmp_path):
    r = _client(tmp_path).get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]


def test_missing_index_404(tmp_path):
    c = TestClient(create_file_app(tmp_path / "empty"))
    assert c.get("/api/index").status_code == 404
