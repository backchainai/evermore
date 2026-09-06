# Architectural Decision Records

All of Evermore's ADRs live here in one consolidated, chronologically numbered sequence (0001-0038). They were previously split across three locations (root `docs/adr/`, `services/retriever/docs/decisions/`, `services/petdata/docs/adr/`); the table below maps every old path to its new number. `000-template.md` is the shared ADR template, not a numbered record, and is excluded from the sequence.

## Old to new mapping

| New | Source | Old path | Effective date |
|---|---|---|---|
| 0001 | retriever | `decisions/001-tech-stack.md` | 2024-12-18 |
| 0002 | retriever | `decisions/002-llm-provider-strategy.md` | 2024-12-18 |
| 0003 | retriever | `decisions/003-system-architecture.md` | 2024-12-18 |
| 0004 | retriever | `decisions/004-vector-database.md` | 2024-12-18 |
| 0005 | retriever | `decisions/005-embedding-model.md` | 2024-12-18 |
| 0006 | retriever | `decisions/006-frontend-architecture.md` | 2024-12-18 |
| 0007 | retriever | `decisions/007-authentication-strategy.md` | 2024-12-18 |
| 0008 | retriever | `decisions/008-observability-stack.md` | 2024-12-18 |
| 0009 | retriever | `decisions/009-content-safety.md` | 2024-12-18 |
| 0010 | retriever | `decisions/010-resilience-patterns.md` | 2024-12-18 |
| 0011 | retriever | `decisions/011-development-environment.md` | 2024-12-18 |
| 0012 | retriever | `decisions/012-rate-limiting.md` | 2024-12-18 |
| 0013 | retriever | `decisions/013-semantic-caching.md` | 2024-12-18 |
| 0014 | retriever | `decisions/014-hallucination-detection.md` | 2024-12-18 |
| 0015 | retriever | `decisions/015-prompt-injection-defense.md` | 2024-12-18 |
| 0016 | retriever | `decisions/016-hybrid-retrieval.md` | 2024-12-18 |
| 0017 | retriever | `decisions/017-conversation-history-schema.md` | 2024-12-19 |
| 0018 | petdata | `adr/002-mutable-pydantic-models.md` | 2026-01-12 |
| 0019 | retriever | `decisions/018-gcp-native-observability.md` | 2026-03-13 |
| 0020 | retriever | `decisions/019-docling-document-processing.md` | 2026-03-16 |
| 0021 | retriever | `decisions/019-apache-2.0-licensing.md` | 2026-06-09 |
| 0022 | root | `adr/0001-monorepo-structure.md` | 2026-06-23 |
| 0023 | root | `adr/0002-github-native-project-management.md` | 2026-06-23 |
| 0024 | root | `adr/0003-standardized-tech-stack.md` | 2026-06-23 |
| 0025 | root | `adr/0004-petdata-postgres-pgvector.md` | 2026-06-23 |
| 0026 | root | `adr/0005-retriever-langfuse-v4.md` | 2026-06-23 |
| 0027 | root | `adr/0006-datadog-via-otel-collector.md` | 2026-06-23 |
| 0028 | root | `adr/0007-llm-gateway-consolidation.md` | 2026-06-24 |
| 0029 | root | `adr/0008-all-cloudflare-hosting.md` | 2026-06-25 |
| 0030 | root | `adr/0009-per-service-supabase-projects.md` | 2026-06-29 |
| 0031 | root | `adr/0010-shared-design-system-package.md` | 2026-06-30 |
| 0032 | root | `adr/0011-supabase-auth-cookie-non-httponly.md` | 2026-06-30 |

The duplicate old retriever number `019` resolves deterministically: docling (2026-03-16) becomes 0020, the Apache 2.0 licensing record (2026-06-09) becomes 0021.

## Index

One line per record: number, slug, status. Where a record is superseded, the successor's new number is named.

- `000-template.md`: template, not part of the numbered sequence
- 0001 tech-stack: accepted
- 0002 llm-provider-strategy: superseded (by ADR 0028)
- 0003 system-architecture: accepted
- 0004 vector-database: superseded (by the pgvector migration, no successor ADR)
- 0005 embedding-model: accepted
- 0006 frontend-architecture: superseded (by the SvelteKit migration, no successor ADR)
- 0007 authentication-strategy: superseded (by ADR 0030)
- 0008 observability-stack: superseded (by ADR 0019)
- 0009 content-safety: accepted
- 0010 resilience-patterns: accepted
- 0011 development-environment: accepted
- 0012 rate-limiting: accepted
- 0013 semantic-caching: accepted
- 0014 hallucination-detection: accepted
- 0015 prompt-injection-defense: accepted
- 0016 hybrid-retrieval: accepted
- 0017 conversation-history-schema: accepted
- 0018 mutable-pydantic-models: accepted
- 0019 gcp-native-observability: superseded (by ADR 0027)
- 0020 docling-document-processing: accepted
- 0021 apache-2.0-licensing: accepted
- 0022 monorepo-structure: accepted
- 0023 github-native-project-management: accepted
- 0024 standardized-tech-stack: accepted
- 0025 petdata-postgres-pgvector: accepted
- 0026 retriever-langfuse-v4: accepted
- 0027 datadog-via-otel-collector: accepted (supersedes ADR 0019)
- 0028 llm-gateway-consolidation: accepted (supersedes ADR 0002)
- 0029 all-cloudflare-hosting: accepted (amends ADR 0024, ADR 0027)
- 0030 per-service-supabase-projects: proposed (supersedes ADR 0007)
- 0031 shared-design-system-package: accepted
- 0032 supabase-auth-cookie-non-httponly: accepted
- 0033 listing-sync-verification: proposed
- 0034 invite-only-magic-link-auth: accepted
- 0035 shelter-reference-code-canonical-id: accepted
- 0036 engagement-data-in-petdata: accepted
- 0037 hosted-only-execution: accepted
- 0038 engagement-collector-scheduled-worker: proposed
