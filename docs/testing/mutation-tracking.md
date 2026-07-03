# Mutation-score tracking

- Status: active
- Issue: #210 (child of epic #205)
- Scope: petdata and retriever critical modules only

## What this is

Mutation testing measures test effectiveness by mutating source and checking
whether the suite notices. A surviving mutant is covered code that no assertion
guards. This doc records the committed harness, the one command per service, the
recorded baselines, and the decision to report (not gate) the score.

The audits in #206 (petdata) and #207 (retriever) produced the first baselines
and named the critical modules. This issue turns those one-time findings into a
runnable, CI-visible metric.

## Harness

Each service carries a committed `[tool.mutmut]` block in its `pyproject.toml`,
scoped to the critical modules. mutmut is intentionally NOT a project dependency:
it is always invoked with `uv run --with mutmut`, so it never enters the service
dependency tree or the lint/test gates. The `mutants/` working directory and
`mutmut-stats.json` are gitignored build artifacts, never committed.

Retriever needed one extra config line. Its default pytest `addopts` carry
`--cov-fail-under=80`; mutmut's clean baseline run collects coverage over the
trampolined `mutants/` tree, which reads near 0% and trips that threshold,
failing the baseline before any mutant runs (the `BadTestExecutionCommandsException`
recorded in the #207 audit). The fix: clear the ini `addopts` with
`--override-ini=addopts=` and re-add only `--cov=src/retriever` (mutmut needs
coverage to decide which files to mutate), enforcing no threshold.

## One command per service

petdata (from `services/petdata`):

```bash
uv run --with mutmut mutmut run \
  "petdata.models.mappers.*" \
  "petdata.modules.api.parser.*" \
  "petdata.modules.api.auth.*"
```

retriever (from `services/retriever`):

```bash
uv run --with mutmut mutmut run \
  "retriever.infrastructure.safety.service.*" \
  "retriever.modules.rag.service.*" \
  "retriever.modules.documents.services.*"
```

View results after either run with `uv run --with mutmut mutmut results`.

## Baselines

petdata (measured in #206, mutmut 3, unit tests only):

| Module | Kill rate |
|---|---|
| models/mappers.py | 47% |
| modules/api/parser.py | 35% |
| modules/api/auth.py | 73% |
| modules/auth/dependencies.py | no mutants (thin wiring) |
| modules/db/repository.py | deferred to CI Postgres (#209) |

retriever: the #207 audit could not produce numbers (the harness was blocked).
The harness is now working (verified locally: clean baseline passes and mutants
execute, producing killed/survived results on rag/safety/document services). The
full numeric baseline is produced by the first CI run and is pending here.
`modules/auth/dependencies.py` is thin FastAPI wiring and yields no mutants, the
same result the petdata audit found for its equivalent module.

## CI: manual, report-only

The `.github/workflows/mutation.yml` workflow runs the scoped suite per service.

- Trigger: `workflow_dispatch` only (run by hand from the Actions tab), with a
  `service` input (petdata, retriever, or both). Mutation runs are too slow for
  push or PR triggers.
- Output: the score is written to the run summary and `mutmut-stats.json` is
  uploaded as an artifact. A surviving mutant does not fail the job.

### Gate-vs-report decision

The score is a report, not a hard gate. Runtime and stability of a full scoped
run have not yet been observed across CI runs, and gating on an unstable or
slow signal would block merges without a reliable basis. Revisit gating once a
few `workflow_dispatch` runs have accumulated runtime and score-stability data;
if the scores hold steady and runtime is acceptable, a floor threshold per
module can be promoted from report to gate at that point.

## How a regression surfaces

Run the workflow from the Actions tab (or the one command per service locally).
Compare the published kill rate against the baselines above. A drop means new or
changed code added covered-but-unguarded paths; add assertions or tests for the
surviving mutants named in the results.
