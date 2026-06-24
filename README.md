# Evermore

An AI platform for nonprofit animal shelters. Evermore ingests animal data from whatever system a shelter already uses, generates research-backed adoption marketing, answers staff questions, and is measured against one outcome: more healthy, safe, and permanent adoptions for homeless animals.

It rides on top of the Shelter Management System (SMS) a shelter already runs rather than replacing it. The initial design partner is a nonprofit animal shelter served pro bono.

Built and maintained by Backchain LLC.

## Start here

- **Run it locally:** [`docs/local-development.md`](docs/local-development.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Vision and architecture:** [`docs/evermore-vision-and-architecture.md`](docs/evermore-vision-and-architecture.md)
- **Decisions:** [`docs/adr/`](docs/adr/)
- **Restructure plan:** [`docs/plans/repo-restructure-and-rename.md`](docs/plans/repo-restructure-and-rename.md)
- **Research corpus:** [`docs/research/README.md`](docs/research/README.md)

## Quick start

Bring up the portal with the Retriever module on your machine. Two commands are
not enough on their own: between them you add an LLM gateway token and copy the
Supabase anon key into the portal, or login and chat fail. Follow the ordered
sequence in [`docs/local-development.md`](docs/local-development.md):

```
make env          # create .env files from examples
                  # then add your LLM gateway config to services/retriever/.env
make supabase-up  # start Supabase
                  # then copy the Supabase anon key into apps/stacker/.env
make dev          # pgvector + retriever, then stacker in the foreground
```

Then open http://localhost:5173/login. Prerequisites, full topology, and
troubleshooting live in [`docs/local-development.md`](docs/local-development.md).

## Structure (target monorepo)

```
apps/stacker         SvelteKit portal: SSO, subscription gating, module registry
services/petdata     Animal data: connectors, canonical Animal Record, Package builder
services/biowriter   Generation: kennel cards, social posts, the lint/score editor (planned)
services/retriever   RAG: shelter-ops chat, and the research-corpus index for citations
packages/            Shared contracts (schema), auth, and UI (planned)
docs/                Vision, ADRs, plans, and the research corpus
infra/               One-command local stack (planned)
```

> This is the target layout, not the current one. Built today: `apps/stacker`, `services/petdata`, `services/retriever`, and `docs/`. Not yet built: `services/biowriter` holds design and docs only (no service code), and `packages/` and `infra/` do not exist yet. The repository is consolidating from four separate repositories into a single monorepo; see the restructure plan for current state and sequencing.

## License

Apache License 2.0. See [LICENSE](LICENSE) for the full text.

Copyright (C) 2026 Backchain LLC
