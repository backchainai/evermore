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
Method: import each module's committed tree as a clean snapshot (`git archive HEAD | tar -x`), not `git subtree`. The repo is public-bound and FOHA is woven through module code and history; a snapshot keeps the monorepo history clean from commit one, avoids a future `git filter-repo` rewrite before going public, and removes the merge-method constraint that subtree merge commits impose under branch protection. The granular pre-consolidation history is preserved in the archived `ckrough/*` origin repos.

1. Snapshot each module into the monorepo, excluding monorepo-redundant paths (`.beads`, `.claude`, `.github`, `.vscode`, `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `CITATION.cff`, module `.gitignore`/`.gitattributes`):
   - `petbio` -> `services/petdata`
   - `retriever` -> `services/retriever` (flatten the inner `backend/` up to the service root)
   - `stacker` -> `apps/stacker`
   - `platform`: copy `platform/docs/*` into `docs/` (architecture, auth-flow, subscriptions, module-template), then retire the repo.
2. Remove the now-unused top-level module directories and drop their ignore entries. (Confirm the `ckrough/*` origins are intact as the history archive first; `platform` has no remote, so deleting it drops its 2-commit history, though its docs are preserved in `docs/`.)

### Phase 3 (done, 2026-06-19): rename petbio -> petdata (code-level) + FOHA scrub
Done: Python package `petbio` -> `petdata`, all imports, the FastAPI app (title "Pet Data"), config env prefix `PETBIO_` -> `PETDATA_`, `pyproject.toml` name, `uv.lock`, database references, tests, and docs. The stacker portal renamed in lockstep: module id, `/app/petdata` route, `PUBLIC_PETDATA_API_URL`, the `PetDataApi` client. FOHA scrubbed from the working tree (code, tests, docs) to generic "Shelter Management System (SMS)", including the design partner's leaked SMS URL and the `"FOHA ID"` parser field key (-> `"Animal ID"`). Gates green: petdata pytest (248)/ruff/mypy, stacker svelte-check (0 errors).

### Phase 4: GitHub setup and issue migration
1. Labels, milestones, Project board, templates, branch protection (see "GitHub structure").
2. Migrate the ~32 epic-children + standalone Evermore issues from the consulting Beads db to GitHub Issues with mapped labels/milestones; close `prof-iqb` and `prof-0e1` as "migrated to GitHub."
3. File the new backlog (requirements from the design conversation) under module milestones and the `v1` wedge milestone:
   - Provenance on every Package item; typed highlights mapped to template sections; the highlighter over Docling output; Package builder UI; Composition + live lint/score editor; hover-to-see-evidence; Export (PDF/Word/Drive, re-import deferred); org/user model + magic-link auth + provisioning; subscription gating; one-command local stack; rename `docs/research/extractions` -> `distilled`; distill behavior/welfare papers; time-online metric.

### Phase 5: aggressive tech-stack conformance (ADR 0003)
Recommended order (petdata gates the schema work):
1. **petdata:** SQLite -> Supabase Postgres + pgvector; SQLAlchemy 2.0 async + Alembic; Supabase auth; OTel/structlog/Sentry; Python 3.14.
2. **packages/schema:** define Animal Record / Package / Composition in Pydantic; generate TS types from OpenAPI.
3. **retriever:** Python 3.14; AI Gateway default; Langfuse v4; Datadog-via-OTel-Collector (superseding ADR 018); Promptfoo, Schemathesis, Sentry.
4. **stacker:** TS 6 strict + shared tsconfig; extract `packages/ui`; entitlements via `+layout.server.ts`.
5. **biowriter:** scaffold greenfield to the standard.

### Phase 6: build the wedge
The research-backed kennel card: generation + live lint/score, on the petdata Package and the distilled template. Validate the highlighter's precision/recall on Sally's real shelter documents before building the full Package-builder UI.

## Doc-update checklist (during consolidation)
- Rewrite the top-level `evermore/CLAUDE.md` (currently describes the polyrepo; must describe the monorepo).
- Fold `platform/CLAUDE.md` and `platform/docs/*` into the monorepo `docs/` and the root `CLAUDE.md`; retire the platform repo.
- Update each module's `CLAUDE.md` for new paths and the `petbio` -> `petdata` rename.

## Open items
- **Repo visibility:** public now vs private until the wedge is demoable. Note the vision spec contains business-model/pricing detail; decide whether that section stays in the public repo or moves to a private planning location before going public.
- **History scrub before public:** the working tree is FOHA-clean as of Phase 3, but the Phase 2 snapshot-import commit still carries FOHA in git history. Decide whether to rewrite history (e.g. squash to a single clean root) before the repo flips public.
- **Docker topology:** `apps/stacker/docker-compose.yml` still references pre-consolidation relative paths (`../petdata`, `../retriever/backend`). Refactor so each service is independently testable or runnable as a suite (tracked separately).

## Resolved
- **History preservation:** resolved as clean-snapshot true monorepo (see Phase 2), superseding the `git subtree` recommendation. Granular history stays in the archived `ckrough/*` origins.
- **FOHA scrub (working tree):** done in Phase 3 (2026-06-19). Code, tests, and docs across `services/petdata` and `apps/stacker` genericized to "Shelter Management System (SMS)"; the design partner's leaked SMS URL and the `"FOHA ID"` field key removed. History scrub is tracked separately under Open items.
