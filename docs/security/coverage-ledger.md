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

## Slice: stacker + packages (issue #227)

This slice covers every tracked file under `apps/stacker/` and `packages/` for issue #227's leg of epic #222. The row set below equals `git ls-files apps/stacker packages` exactly (150 files). The issue estimated 152 files (110 stacker + 42 packages); the actual tracked count is 150 (108 stacker + 42 packages), a -2 delta (the estimate ran two high on stacker). Class and depth follow the epic #222 mapping; where a file could fall in two classes the higher-scrutiny class was chosen. Trust-boundary analysis and full finding detail are in `docs/security/stacker-packages-audit.md`; `FINDING-Sxx` verdicts key to that document. Critical/High findings are filed as redacted follow-on issues per public-repo discipline.

Class counts: security-critical 20, boundary-adjacent 72, config-IaC 20, inert 38.

| File | Class | Depth | Verdict |
|---|---|---|---|
| `apps/stacker/.env.example` | config-IaC | full-read | clean |
| `apps/stacker/CLAUDE.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/README.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/docker-compose.yml` | config-IaC | full-read | clean |
| `apps/stacker/package-lock.json` | config-IaC | full-read | clean |
| `apps/stacker/package.json` | config-IaC | full-read | clean |
| `apps/stacker/playwright.config.ts` | config-IaC | full-read | clean |
| `apps/stacker/src/app.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/app.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/app.html` | config-IaC | full-read | clean |
| `apps/stacker/src/hooks.server.ts` | security-critical | line-by-line | FINDING-S2 (Medium): CSP is Report-Only, not enforcing |
| `apps/stacker/src/lib/api/base-client.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/api/client.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/api/types.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/ChatInput.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/ChatMessage.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/ClearHistoryButton.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/ConfidenceBadge.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/DocumentList.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/DocumentUpload.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/ErrorAlert.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/components/SourceCitation.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/petdata/api/client.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/petdata/api/types.generated.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/petdata/api/types.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/petdata/index.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/api/client.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/api/types.generated.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/api/types.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/ChatInput.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/ChatMessage.svelte` | boundary-adjacent | trust-review | FINDING-S1 (High): unsanitized `marked` -> `{@html}` model-output XSS |
| `apps/stacker/src/lib/modules/retriever/components/ClearHistoryButton.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/ConfidenceBadge.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/DocumentList.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/DocumentUpload.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/components/SourceCitation.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/modules/retriever/index.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/AnimalSubjectSelector.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/MobileNav.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/ModuleCard.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/ModuleIcon.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/PortalAppBar.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/PortalShell.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/PortalSidebar.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/SubscriptionGate.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/ThemePicker.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/components/UserMenu.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/config.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/shared/ErrorAlert.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/state/animal-subject.svelte.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/theme/dark.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/lib/portal/theme/fonts.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/lib/portal/theme/light.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/lib/portal/theme/neutral.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/lib/portal/theme/theme-store.svelte.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/theme/tokens.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/src/lib/portal/types.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/portal/user-display.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/server/stripe-webhook.test.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/lib/server/stripe-webhook.ts` | security-critical | line-by-line | FINDING-S5 (Medium): service_role blast radius; FINDING-S6 (Low): no app-level idempotency |
| `apps/stacker/src/lib/server/supabase.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/+error.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/+layout.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/+layout.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/+layout.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/admin/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/admin/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/api/webhooks/stripe/+server.ts` | security-critical | line-by-line | FINDING-S5 (Medium): service_role key handling |
| `apps/stacker/src/routes/app/+layout.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/app/+layout.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/petdata/+layout.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/app/petdata/+layout.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/petdata/animals/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/petdata/animals/[id]/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/petdata/notes/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/retriever/+layout.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/app/retriever/+layout.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/retriever/admin/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/app/retriever/admin/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/app/retriever/chat/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/app/retriever/chat/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/auth/confirm/+server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/auth/error/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/chat/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/chat/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/invite/accept/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/invite/accept/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/login/+page.server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/src/routes/login/+page.svelte` | boundary-adjacent | trust-review | clean |
| `apps/stacker/src/routes/logout/+server.ts` | security-critical | line-by-line | clean |
| `apps/stacker/static/favicon.png` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `apps/stacker/supabase/config.toml` | config-IaC | full-read | FINDING-S4 (Low): minimum_password_length=6 |
| `apps/stacker/supabase/migrations/.gitkeep` | config-IaC | full-read | clean |
| `apps/stacker/supabase/migrations/20260702000000_subscriptions.sql` | config-IaC | full-read | clean |
| `apps/stacker/supabase/seed.sql` | config-IaC | full-read | clean |
| `apps/stacker/supabase/templates/invite.html` | config-IaC | full-read | clean |
| `apps/stacker/supabase/templates/magic_link.html` | config-IaC | full-read | clean |
| `apps/stacker/svelte.config.js` | config-IaC | full-read | clean |
| `apps/stacker/tests/e2e/auth.spec.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/tests/e2e/favicon.spec.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/tests/e2e/home.spec.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/tests/e2e/security-headers.spec.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/tsconfig.json` | config-IaC | full-read | clean |
| `apps/stacker/vite.config.ts` | config-IaC | full-read | clean |
| `apps/stacker/vitest.config.ts` | boundary-adjacent | trust-review | clean |
| `apps/stacker/wrangler.toml` | config-IaC | full-read | clean |
| `packages/auth/README.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/auth/pyproject.toml` | config-IaC | full-read | clean |
| `packages/auth/src/evermore_auth/__init__.py` | security-critical | line-by-line | clean |
| `packages/auth/src/evermore_auth/dependencies.py` | security-critical | line-by-line | clean |
| `packages/auth/src/evermore_auth/jwks.py` | security-critical | line-by-line | FINDING-S3 (Low): issuer (`iss`) not pinned |
| `packages/auth/src/evermore_auth/py.typed` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/auth/src/evermore_auth/schemas.py` | security-critical | line-by-line | clean |
| `packages/auth/tests/test_auth.py` | boundary-adjacent | trust-review | clean |
| `packages/auth/uv.lock` | config-IaC | full-read | clean |
| `packages/design-system/SKILL.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/Inter-OFL.txt` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/Inter-Variable.ttf` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/JetBrainsMono-OFL.txt` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/JetBrainsMono-Variable.ttf` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/Outfit-OFL.txt` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/assets/fonts/Outfit-Variable.ttf` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Badge.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Badge.prompt.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Button.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Button.prompt.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Card.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/Card.prompt.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/SectionLabel.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/core/SectionLabel.prompt.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/forms/TextField.d.ts` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/components/forms/TextField.prompt.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/readme.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/styles.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/tokens/base.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/tokens/colors.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/tokens/fonts.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/tokens/spacing.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/design-system/tokens/typography.css` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/schema/README.md` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/schema/pyproject.toml` | config-IaC | full-read | clean |
| `packages/schema/src/evermore_schema/__init__.py` | boundary-adjacent | trust-review | clean |
| `packages/schema/src/evermore_schema/animal.py` | boundary-adjacent | trust-review | clean |
| `packages/schema/src/evermore_schema/py.typed` | inert | secret-scan + claim-check | inert, secret-scanned only |
| `packages/schema/src/evermore_schema/spine.py` | boundary-adjacent | trust-review | clean |
| `packages/schema/tests/test_animal.py` | boundary-adjacent | trust-review | clean |
| `packages/schema/tests/test_spine.py` | boundary-adjacent | trust-review | clean |
| `packages/schema/uv.lock` | config-IaC | full-read | clean |
