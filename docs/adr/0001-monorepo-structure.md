# ADR 0001: Single monorepo for the Evermore platform

- Status: accepted
- Date: 2026-06-19
- Deciders: project owner

## Context

Evermore is currently four separate git repositories (`stacker`, `retriever`, `petbio`, `platform`) sitting under a non-git `evermore/` parent. The modules are tightly coupled through shared contracts (the Animal Record, Package, and Composition schemas, the Supabase auth/JWKS client, and the subscription gate). The team is 1 to 3 developers. We are assuming open-source growth and outside contribution, and we have chosen GitHub-native project management (see ADR 0002).

Two facts force the decision:
- **GitHub Issues are per-repo.** A polyrepo fragments the backlog across four trackers and gives cross-module work no natural home.
- **Coordination cost dominates at this team size.** Shared contracts change together; in a polyrepo that is four coordinated PRs and internal version bumps, in a monorepo it is one atomic PR.

A consolidation was already in progress (the old `prof-iqb.1` issue, "consolidate under evermore directory"), so staying split is the higher-friction direction.

## Decision

Adopt a **single monorepo** rooted at `evermore/`:

```
evermore/
├── apps/
│   └── stacker/           # SvelteKit portal (Cloudflare Pages)
├── services/
│   ├── petdata/           # FastAPI, renamed from petbio
│   ├── biowriter/         # FastAPI, content generation (new)
│   └── retriever/         # FastAPI RAG
├── packages/
│   ├── schema/            # Animal Record, Package, Composition contracts
│   ├── auth/              # Supabase JWT/JWKS + subscription gate
│   └── ui/                # shared Svelte components
├── docs/                  # research corpus + architecture/ADRs (already here)
├── infra/                 # docker-compose, one-command local stack
└── .github/workflows/     # path-filtered CI, Claude action
```

The standalone `platform` repo retires; its docs fold into `docs/`. Each former repo's history is preserved via `git subtree` merges during consolidation.

## Consequences

- One issue tracker, one CI configuration, one local stack (`docker compose up`), atomic cross-module changes.
- Shared code is imported directly from `packages/` rather than published as internal packages no outsider consumes.
- Per-module repo stars and marketing are lost. Mitigation: one cohesive "Evermore platform" repo tells a stronger story; a read-only showpiece mirror can be split out later if a module earns it.
- Polyglot (TypeScript + Python) kept deliberately simple: per-service `pyproject.toml` (uv), stacker's `package.json`, a root `docker-compose`, an optional `justfile`, and path-filtered GitHub Actions. No Nx, Turborepo, or Bazel at this scale.
- Exit ramp stays cheap: `git subtree split` extracts a module to its own repo if it ever needs independence. Monorepo-now, extract-later is the low-cost direction.

## Alternatives considered

- **Polyrepo (status quo).** Rejected: fragments GitHub Issues, multiplies coordination cost at 1 to 3 devs, and reverses an in-progress consolidation.
