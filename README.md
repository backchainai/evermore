# Evermore

An AI platform for nonprofit animal shelters. Evermore ingests animal data from whatever system a shelter already uses, generates research-backed adoption marketing, answers staff questions, and is measured against one outcome: more healthy, safe, and permanent adoptions for homeless animals.

## Start here

- **Run it locally:** [`docs/local-development.md`](docs/local-development.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Vision and architecture:** [`docs/evermore-vision-and-architecture.md`](docs/evermore-vision-and-architecture.md)
- **Decisions:** [`docs/adr/`](docs/adr/)
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

## Structure

This is the module inventory; per-module build and test commands live in each module's own `CLAUDE.md`, not here.

```
apps/stacker         SvelteKit portal: SSO, subscription gating, module registry
services/petdata     Animal data: connectors, canonical Animal Record, Package builder
services/biowriter   Generation: kennel cards, social posts, the lint/score editor (not yet scaffolded)
services/retriever   RAG: shelter-ops chat, and the research-corpus index for citations
packages/            Shared packages: auth, schema, design-system, llm (built; see each package's own README)
docs/                Architecture, ADRs, and the research corpus
tools/               Local dev tooling (the offline LLM stub)
scripts/             Repo-level scripts (e.g. the doc link checker)
```

`services/biowriter` holds design and docs only, no service code yet. `infra/` does not exist as a directory; the local stack is Makefile- and Docker-Compose-driven today (see `docs/local-development.md`).

## License

Apache License 2.0. See [LICENSE](LICENSE) for the full text.

Copyright (C) 2026 Backchain LLC
