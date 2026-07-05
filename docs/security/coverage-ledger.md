# Coverage Ledger

This is the coverage ledger for issue #224's slice of epic #222 (repo-wide security audit). It seeds one row per file in scope for this slice: every file under `.github/`, every file under `docs/`, and every file at the repo root. Future children of epic #222 append their own slices to this same file rather than starting a new ledger, so this document accumulates the full audit inventory across the epic's lifetime.

Class and Depth are assigned by file type, following the mapping below:

- `.github/workflows/*.yml`: security-critical, audited line-by-line (these execute with repo secrets and write access).
- `.github/dependabot.yml`, root dotfiles (`.gitignore`, `.dockerignore`, etc.), `Makefile`, and other GitHub config (issue templates, PR template): config-IaC, audited full-read.
- `docs/**`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CLAUDE.md`, `LICENSE`, and other prose: inert, audited via secret-scan plus claim-check (verifying documented claims match the actual code and config).

Verdict is `pending audit` for every row in this slice. The lead finalizes verdicts with references to findings issues once the audit for each file completes.

| File | Class | Depth | Verdict |
|---|---|---|---|
| `.dockerignore` | config-IaC | full-read | pending audit |
| `.github/dependabot.yml` | config-IaC | full-read | pending audit |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | config-IaC | full-read | pending audit |
| `.github/ISSUE_TEMPLATE/config.yml` | config-IaC | full-read | pending audit |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | config-IaC | full-read | pending audit |
| `.github/pull_request_template.md` | config-IaC | full-read | pending audit |
| `.github/workflows/ci.yml` | security-critical | line-by-line | pending audit |
| `.github/workflows/claude-code-review.yml` | security-critical | line-by-line | pending audit |
| `.github/workflows/claude.yml` | security-critical | line-by-line | pending audit |
| `.github/workflows/codeql.yml` | security-critical | line-by-line | pending audit |
| `.github/workflows/deploy.yml` | security-critical | line-by-line | pending audit |
| `.github/workflows/mutation.yml` | security-critical | line-by-line | pending audit |
| `.gitignore` | config-IaC | full-read | pending audit |
| `CLAUDE.md` | inert | secret-scan + claim-check | pending audit |
| `CODE_OF_CONDUCT.md` | inert | secret-scan + claim-check | pending audit |
| `CONTRIBUTING.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/000-template.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0001-tech-stack.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0002-llm-provider-strategy.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0003-system-architecture.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0004-vector-database.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0005-embedding-model.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0006-frontend-architecture.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0007-authentication-strategy.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0008-observability-stack.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0009-content-safety.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0010-resilience-patterns.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0011-development-environment.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0012-rate-limiting.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0013-semantic-caching.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0014-hallucination-detection.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0015-prompt-injection-defense.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0016-hybrid-retrieval.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0017-conversation-history-schema.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0018-mutable-pydantic-models.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0019-gcp-native-observability.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0020-docling-document-processing.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0021-apache-2.0-licensing.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0022-monorepo-structure.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0023-github-native-project-management.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0024-standardized-tech-stack.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0025-petdata-postgres-pgvector.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0026-retriever-langfuse-v4.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0027-datadog-via-otel-collector.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0028-llm-gateway-consolidation.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0029-all-cloudflare-hosting.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0030-per-service-supabase-projects.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0031-shared-design-system-package.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/0032-supabase-auth-cookie-non-httponly.md` | inert | secret-scan + claim-check | pending audit |
| `docs/adr/README.md` | inert | secret-scan + claim-check | pending audit |
| `docs/architecture.md` | inert | secret-scan + claim-check | pending audit |
| `docs/auth-flow.md` | inert | secret-scan + claim-check | pending audit |
| `docs/CLAUDE.md` | inert | secret-scan + claim-check | pending audit |
| `docs/cloudflare-ai-gateway-setup.md` | inert | secret-scan + claim-check | pending audit |
| `docs/evermore-vision-and-architecture.md` | inert | secret-scan + claim-check | pending audit |
| `docs/local-development.md` | inert | secret-scan + claim-check | pending audit |
| `docs/module-template.md` | inert | secret-scan + claim-check | pending audit |
| `docs/research/distilled/key-adoption-profile-research-findings-summary.md` | inert | secret-scan + claim-check | pending audit |
| `docs/research/distilled/recommended-adoption-profile-pictures.md` | inert | secret-scan + claim-check | pending audit |
| `docs/research/distilled/recommended-pet-biography-template-format.md` | inert | secret-scan + claim-check | pending audit |
| `docs/research/distilled/shelter-dog-adoption-success-rates.md` | inert | secret-scan + claim-check | pending audit |
| `docs/research/README.md` | inert | secret-scan + claim-check | pending audit |
| `docs/security/coverage-ledger.md` | inert | secret-scan + claim-check | pending audit |
| `docs/security/threat-model.md` | inert | secret-scan + claim-check | pending audit |
| `docs/subscriptions.md` | inert | secret-scan + claim-check | pending audit |
| `docs/testing/mutation-tracking.md` | inert | secret-scan + claim-check | pending audit |
| `docs/testing/petdata-test-audit.md` | inert | secret-scan + claim-check | pending audit |
| `docs/testing/retriever-test-effectiveness-audit.md` | inert | secret-scan + claim-check | pending audit |
| `docs/testing/stacker-test-audit.md` | inert | secret-scan + claim-check | pending audit |
| `LICENSE` | inert | secret-scan + claim-check | pending audit |
| `Makefile` | config-IaC | full-read | pending audit |
| `README.md` | inert | secret-scan + claim-check | pending audit |
| `SECURITY.md` | inert | secret-scan + claim-check | pending audit |

73 files in the slice as of this PR tree; ticket estimated 67, delta +6, per the plan's note that the count is 70-ish today.
