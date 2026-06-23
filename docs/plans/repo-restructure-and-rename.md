# Plan: Evermore monorepo restructure and rename

Status: ready to execute, 2026-06-19. Companion to `../evermore-vision-and-architecture.md` and ADRs `0001`-`0003`.

This is the post-compaction execution plan. Decisions are settled (see the ADRs); this is the ordered "how."

## Decision quick-reference (for context recovery)

- **Monorepo** rooted at `evermore/`, owner **`github.com/backchainai`**, repo `evermore`.
- **Naming spine:** Sources -> Animal Record -> **Package** -> **Composition** -> **Export**. Package items carry provenance; Composition retains it; Export is flat.
- **Renames:** `petbio` -> `services/petdata`; `retriever` -> `services/retriever`; `stacker` -> `apps/stacker`; `platform` retires (docs fold into `docs/`); new `services/biowriter`.
- **Tracking:** GitHub Issues + Projects + PRs + Claude action. Beads retired for Evermore.
- **Tech stack:** aggressive full conformance to the platform standard; nothing grandfathered.
- **Wedge:** the research-backed kennel card.

## Target layout

```
evermore/
├── apps/
│   └── stacker/                 # SvelteKit portal (Cloudflare Pages)
├── services/
│   ├── petdata/                 # FastAPI (from petbio): connectors, Animal Record, Package, behavior analysis
│   ├── biowriter/               # FastAPI (new): generation, lint/score, Composition, Export
│   └── retriever/               # FastAPI RAG (+ research-corpus index for BioWriter citations)
├── packages/
│   ├── schema/                  # Animal Record, Package, Composition contracts (Pydantic source; TS generated)
│   ├── auth/                    # Supabase JWT/JWKS client + subscription gate
│   └── ui/                      # shared Svelte components (folds in the old prof-1jr shared-component work)
├── docs/
│   ├── evermore-vision-and-architecture.md
│   ├── adr/                     # platform-level ADRs (module ADRs live in each service)
│   ├── plans/
│   └── research/                # the research corpus (already here)
├── infra/                       # docker-compose, dev containers, one-command local stack
├── .github/
│   ├── workflows/               # path-filtered CI, claude.yml, deploy
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── CLAUDE.md                    # monorepo guide (rewrite of the current polyrepo one)
├── README.md
├── LICENSE                      # Apache-2.0, Backchain LLC
└── CONTRIBUTING.md
```

## Phases

### Phase 0 (done): document decisions
Vision spec, ADRs 0001-0003, and this plan written to `docs/`.

### Phase 1: git init and commit documentation (first step)
1. Operator runs `git init` at `evermore/` and sets the default branch to `main`.
2. The four existing module directories stay as their own git repos for now and are git-ignored at the root (see the staged `.gitignore`); they are consolidated with history in Phase 2.
3. Commit the documentation and root scaffold only: `docs/`, `CLAUDE.md`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `.gitignore`.
4. Operator creates the remote at `github.com/backchainai/evermore` and configures it (see "GitHub structure" below); push `main`.

### Phase 2: consolidate the modules (clean-snapshot true monorepo)
Method: import each module's committed tree as a clean snapshot (`git archive HEAD | tar -x`), not `git subtree`. The repo is public-bound and the design partner's name is woven through module code and history; a snapshot keeps the monorepo history clean from commit one, avoids a future `git filter-repo` rewrite before going public, and removes the merge-method constraint that subtree merge commits impose under branch protection. The granular pre-consolidation history is preserved in the archived `ckrough/*` origin repos.

1. Snapshot each module into the monorepo, excluding monorepo-redundant paths (`.beads`, `.claude`, `.github`, `.vscode`, `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `CITATION.cff`, module `.gitignore`/`.gitattributes`):
   - `petbio` -> `services/petdata`
   - `retriever` -> `services/retriever` (flatten the inner `backend/` up to the service root)
   - `stacker` -> `apps/stacker`
   - `platform`: copy `platform/docs/*` into `docs/` (architecture, auth-flow, subscriptions, module-template), then retire the repo.
2. Remove the now-unused top-level module directories and drop their ignore entries. (Confirm the `ckrough/*` origins are intact as the history archive first; `platform` has no remote, so deleting it drops its 2-commit history, though its docs are preserved in `docs/`.)

### Phase 3 (done, 2026-06-19): rename petbio -> petdata (code-level) + client-name scrub
Done: Python package `petbio` -> `petdata`, all imports, the FastAPI app (title "Pet Data"), config env prefix `PETBIO_` -> `PETDATA_`, `pyproject.toml` name, `uv.lock`, database references, tests, and docs. The stacker portal renamed in lockstep: module id, `/app/petdata` route, `PUBLIC_PETDATA_API_URL`, the `PetDataApi` client. The design partner's name scrubbed from the working tree (code, tests, docs) to generic "Shelter Management System (SMS)", including the design partner's leaked SMS URL and the client-specific ID parser field key (-> `"Animal ID"`). Gates green: petdata pytest (248)/ruff/mypy, stacker svelte-check (0 errors).

### Phase 4 (done, 2026-06-19): GitHub setup and issue migration
Done: labels (standard set + per-module, with `module:petbio` -> `module:petdata`), milestones (Portal foundation, Portal MVP, v1 wedge), the Evermore Project board, issue/PR templates, and branch protection (PR required; `ci-success` is a required status check). Path-filtered CI landed in `.github/workflows/ci.yml` (PR #48): per-service gates for petdata (ruff/mypy/bandit/pytest), retriever (ruff/mypy/unit pytest; integration needs Postgres, deferred), and stacker (svelte-check/build), behind a single `ci-success` gate. The ~32 Evermore issues were migrated from the consulting Beads db to GitHub Issues with mapped labels and milestones.

The v1 wedge backlog is filed under the `v1 wedge: research-backed kennel card` milestone (#38-#47), all added to the Project board: provenance on every Package item, typed highlights mapped to template sections, the highlighter over Docling output, the Package builder UI, the Composition + live lint/score editor, hover-to-see-evidence, Export (PDF/Word/Drive; re-import deferred), the `docs/research/extractions` -> `distilled` rename, distilling the behavior/welfare papers, and the time-online metric. Backlog items already covered by existing issues (org/user auth, subscription gating, one-command local stack) were not refiled.

### Phase 5: aggressive tech-stack conformance (ADR 0003)
Tracked under GitHub epic #50, with the conformance work filed as its child issues. The decisions the implementation PRs enact are recorded write-first as ADRs 0004 (petdata SQLite -> Postgres + pgvector), 0005 (retriever Langfuse v3 -> v4), and 0006 (Datadog via the OpenTelemetry Collector, superseding retriever ADR 018).

Recommended order (petdata gates the schema work):
1. **petdata:** SQLite -> Supabase Postgres + pgvector; SQLAlchemy 2.0 async + Alembic; Supabase auth; OTel/structlog/Sentry; Python 3.14. (ADR 0004; issues #9, #29, #16)
2. **packages/schema:** define Animal Record / Package / Composition in Pydantic; generate TS types from OpenAPI. (issues #54, #17)
3. **retriever:** Python 3.14; AI Gateway default; Langfuse v4; Datadog-via-OTel-Collector (superseding ADR 018); Promptfoo, Schemathesis, Sentry. (ADRs 0005, 0006; issues #57, #58, #59, #60, #61)
4. **stacker:** TS 6 strict + shared tsconfig; extract `packages/ui`; entitlements via `+layout.server.ts`. (issues #62, #63, #56, #31)
5. **biowriter:** scaffold greenfield to the standard. (issue #64)

### Phase 6: build the wedge
The research-backed kennel card: generation + live lint/score, on the petdata Package and the distilled template. Validate the highlighter's precision/recall on Sally's real shelter documents before building the full Package-builder UI.

## Doc-update checklist (during consolidation)
- Rewrite the top-level `evermore/CLAUDE.md` (currently describes the polyrepo; must describe the monorepo).
- Fold `platform/CLAUDE.md` and `platform/docs/*` into the monorepo `docs/` and the root `CLAUDE.md`; retire the platform repo.
- Update each module's `CLAUDE.md` for new paths and the `petbio` -> `petdata` rename.

## Open items
- **Repo visibility:** public now vs private until the wedge is demoable. Note the vision spec contains business-model/pricing detail; decide whether that section stays in the public repo or moves to a private planning location before going public.
- **History scrub before public:** the working tree is clean of the design partner's name as of Phase 3, but the Phase 2 snapshot-import commit still carries it in git history. Decide whether to rewrite history (e.g. squash to a single clean root) before the repo flips public.
- **Docker topology:** `apps/stacker/docker-compose.yml` still references pre-consolidation relative paths (`../petdata`, `../retriever/backend`). Refactor so each service is independently testable or runnable as a suite (tracked separately).

## Resolved
- **History preservation:** resolved as clean-snapshot true monorepo (see Phase 2), superseding the `git subtree` recommendation. Granular history stays in the archived `ckrough/*` origins.
- **Client-name scrub (working tree):** done in Phase 3 (2026-06-19). Code, tests, and docs across `services/petdata` and `apps/stacker` genericized to "Shelter Management System (SMS)"; the design partner's leaked SMS URL and the client-specific ID field key removed. History scrub is tracked separately under Open items.
- **GitHub setup and CI:** done in Phase 4 (2026-06-19). Labels/milestones/board/templates/branch-protection in place; path-filtered CI (`ci-success` required check) merged in PR #48; issues migrated and the v1 wedge backlog filed (#38-#47).
