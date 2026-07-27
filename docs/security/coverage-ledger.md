# Coverage Ledger

This is the coverage ledger for issue #224's slice of epic #222 (repo-wide security audit). It seeds one row per file in scope for this slice: every file under `.github/`, every file under `docs/`, and every file at the repo root. Future children of epic #222 append their own slices to this same file rather than starting a new ledger, so this document accumulates the full audit inventory across the epic's lifetime.

Class and Depth are assigned by file type, following the mapping below:

- `.github/workflows/*.yml`: security-critical, audited line-by-line (these execute with repo secrets and write access).
- `.github/dependabot.yml`, root dotfiles (`.gitignore`, `.dockerignore`, etc.), `Makefile`, and other GitHub config (issue templates, PR template): config-IaC, audited full-read.
- `docs/**`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CLAUDE.md`, `LICENSE`, and other prose: inert, audited via secret-scan plus claim-check (verifying documented claims match the actual code and config).

Verdicts for this slice were seeded `pending audit` in PR #242 (the #224 audit results were recorded in the #224 issue comment rather than written back here) and finalized during the epic #222 reconciliation: the two agent-workflow findings map to #263 (`claude.yml`) and #268 (`claude-code-review.yml`); every other row is `clean` with a class-appropriate rationale, grounded in #224's per-workflow audit (C1) and full-history secret scan (C3).

| File | Class | Depth | Verdict |
|---|---|---|---|
| `.dockerignore` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/dependabot.yml` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/ISSUE_TEMPLATE/config.yml` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/pull_request_template.md` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `.github/workflows/ci.yml` | security-critical | line-by-line | clean -- line-by-line: minimal `permissions:`, no `pull_request_target`, no `${{ }}` interpolated into `run:`, actions SHA-pinned (#224 C1) |
| `.github/workflows/claude-code-review.yml` | security-critical | line-by-line | RESOLVED #268 (High): author-association gate restored (OWNER/MEMBER/COLLABORATOR) so untrusted fork-PR authors cannot trigger the workflow; unpinned first-party Anthropic marketplace retained as a documented accepted-risk (trusted-author gate + fork-PR secret withholding bound the residual exposure) (#224 C1) |
| `.github/workflows/claude.yml` | security-critical | line-by-line | FINDING #263 (High): anonymous denial-of-wallet via `@claude` trigger; read-only `permissions:` bound repo mutation (#224 C1) |
| `.github/workflows/codeql.yml` | security-critical | line-by-line | clean -- line-by-line: CodeQL scanning workflow added in #242, minimal `permissions:`, SHA-pinned (#224 C1) |
| `.github/workflows/deploy.yml` | security-critical | line-by-line | clean -- line-by-line: branch-name injection handled deliberately (env var + quoted expansion); fork PRs skip deploy jobs via secret-presence preflight (#224 C1) |
| `.github/workflows/mutation.yml` | security-critical | line-by-line | clean -- line-by-line: SHA-pinned, no fork-secret path (#224 C1) |
| `.gitignore` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `CLAUDE.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `CODE_OF_CONDUCT.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `CONTRIBUTING.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/000-template.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0001-tech-stack.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0002-llm-provider-strategy.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0003-system-architecture.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0004-vector-database.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0005-embedding-model.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0006-frontend-architecture.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0007-authentication-strategy.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0008-observability-stack.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0009-content-safety.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0010-resilience-patterns.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0011-development-environment.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0012-rate-limiting.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0013-semantic-caching.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0014-hallucination-detection.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0015-prompt-injection-defense.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0016-hybrid-retrieval.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0017-conversation-history-schema.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0018-mutable-pydantic-models.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0019-gcp-native-observability.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0020-docling-document-processing.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0021-apache-2.0-licensing.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0022-monorepo-structure.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0023-github-native-project-management.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0024-standardized-tech-stack.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0025-petdata-postgres-pgvector.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0026-retriever-langfuse-v4.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0027-datadog-via-otel-collector.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0028-llm-gateway-consolidation.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0029-all-cloudflare-hosting.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0030-per-service-supabase-projects.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0031-shared-design-system-package.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/0032-supabase-auth-cookie-non-httponly.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/adr/README.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/architecture.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/auth-flow.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/CLAUDE.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/cloudflare-ai-gateway-setup.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/evermore-vision-and-architecture.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/local-development.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/module-template.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/research/distilled/key-adoption-profile-research-findings-summary.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/research/distilled/recommended-adoption-profile-pictures.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/research/distilled/recommended-pet-biography-template-format.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/research/distilled/shelter-dog-adoption-success-rates.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/research/README.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/security/coverage-ledger.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/security/threat-model.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/subscriptions.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/testing/mutation-tracking.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/testing/petdata-test-audit.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/testing/retriever-test-effectiveness-audit.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `docs/testing/stacker-test-audit.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `LICENSE` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `Makefile` | config-IaC | full-read | clean -- full-read: config only, no secret material (#224) |
| `README.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |
| `SECURITY.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: no secrets (#224 C3, full-history gitleaks CLEAN) |

73 files in the slice as of this PR tree; ticket estimated 67, delta +6, per the plan's note that the count is 70-ish today. All 73 verdicts finalized in the epic #222 reconciliation (2 findings: #263, #268; 71 clean).

## petdata (issue #225 slice)

This slice covers every tracked file under `services/petdata` (81 files as of this PR tree), the extraction service that authenticates to a shelter's Shelter Management System (SMS) with cookie credentials, fetches animal/behavior/walk data over HTTP, and persists it to Supabase Postgres behind a FastAPI + Cloudflare Worker/Container boundary. The review ran five axes across the tree: the ingestion boundary (`modules/api/parser.py` turning untrusted SMS JSON into validated models, and `modules/api/client.py`'s lack of a response-size cap), credential handling (`config.py`, `modules/api/auth.py`, `.env.example`, the Worker's secret-forwarding list), outbound egress/SSRF (the `httpx.Client` in `modules/api/client.py`, including its `follow_redirects=True` setting), the mutation surface (`modules/db/repository.py`'s parameterized SQLAlchemy statements, its lack of tenant-id filtering, and its lack of write attributability, plus Alembic's DDL and its inert row-level-security posture), and the API surface (`modules/web/routes.py`'s auth/subscription-gated router, its unbounded pagination parameters, plus the deliberately unauthenticated `/llms.txt` and `/health` endpoints in `main.py`). Findings are tracked as `[F1] (#243)`-`[F6] (#248)`; see the audit notes on issue #225 for per-finding disposition, severity, and redacted detail. No secrets, API keys, or private-key material were found committed anywhere in the tree; hits on credential-shaped grep patterns (`PETDATA_COOKIES`, `PETDATA_DATABASE_URL`, etc.) are all variable names or `.env.example` placeholders, never literal values.

| File | Class | Depth | Verdict |
|---|---|---|---|
| `services/petdata/.dockerignore` | config-IaC | full-read | clean — build-context exclusions only; Docker actually reads the repo-root `.dockerignore` for this image per `CLAUDE.md`, so this file is a secondary safety net, not authoritative |
| `services/petdata/.env.example` | config-IaC | full-read | clean — every value is a placeholder (`your-sms-session-cookies`, `your-project.supabase.co`); no live credential |
| `services/petdata/.pre-commit-config.yaml` | config-IaC | full-read | clean — includes `detect-private-key`; standard ruff/mypy hook wiring, no exclusions that weaken scanning |
| `services/petdata/.python-version` | config-IaC | full-read | clean — single pinned version string |
| `services/petdata/CHANGELOG.md` | inert | secret-scan + claim-check | clean — release notes only, no embedded secrets |
| `services/petdata/CLAUDE.md` | inert | secret-scan + claim-check | clean — module guidance doc; commands and structure match the tree |
| `services/petdata/Dockerfile` | security-critical | line-by-line | clean — explicit `COPY` paths only (no `COPY . .`), non-root `USER petdata`, no secret build args or `ARG`/`ENV` leaking credentials into layers |
| `services/petdata/README.md` | inert | secret-scan + claim-check | clean — project overview, no secrets |
| `services/petdata/alembic.ini` | config-IaC | full-read | clean — `sqlalchemy.url` is a documented-unused placeholder; real URL resolved at runtime from settings (see `alembic/env.py`) |
| `services/petdata/alembic/env.py` | security-critical | line-by-line | clean — resolves `PETDATA_DATABASE_URL` via `get_settings().database_url.get_secret_value()` at runtime, never logs or persists the raw URL |
| `services/petdata/alembic/script.py.mako` | config-IaC | full-read | clean — stock Alembic revision template, no injected content |
| `services/petdata/alembic/versions/001_initial_schema.py` | security-critical | line-by-line | finding — [F1] (#243): RLS is enabled via `ENABLE ROW LEVEL SECURITY` (line 47), not `FORCE`, so the table-owner role the app connects as bypasses the policy entirely; the `_tenant_isolation` policy (lines 48-52) is otherwise correctly scoped to `current_setting('request.jwt.claims', true)::jsonb->>'tenant_id'`, but is defense-in-depth only until #29 wires the session claim and the app moves off the owner role. `_enable_inert_rls` interpolates only the hardcoded `_TENANT_TABLES` tuple into DDL, never external data, so no injection risk in the migration itself |
| `services/petdata/alembic/versions/002_add_animal_species.py` | app-code | full-read | clean — single additive column migration, no data-shape risk |
| `services/petdata/docker-compose.test.yml` | config-IaC | full-read | clean — ephemeral tmpfs Postgres, fixed local-only `postgres`/`postgres` dev credential scoped to a disposable container |
| `services/petdata/docker-compose.yml` | config-IaC | full-read | clean — same local-only dev credential pattern as the test compose file, named volume not exposed beyond host |
| `services/petdata/docs/design/architecture.md` | inert | secret-scan + claim-check | clean — design doc; no secrets, structure matches current `src/petdata/` layout |
| `services/petdata/docs/design/concept.md` | inert | secret-scan + claim-check | clean — product concept narrative, no secrets |
| `services/petdata/docs/design/development-standards.md` | inert | secret-scan + claim-check | clean — coding standards doc; grep hit was the word "token" in prose, not a credential |
| `services/petdata/docs/design/phase1-data-extraction.md` | inert | secret-scan + claim-check | clean — Phase 1 design notes, no secrets |
| `services/petdata/docs/guides/cloudflare-containers.md` | inert | secret-scan + claim-check | clean — deployment guide; describes `wrangler secret put` usage, names no actual secret values |
| `services/petdata/entrypoint.sh` | security-critical | line-by-line | clean — `set -euo pipefail`, launches uvicorn with env-driven host/port/workers, no credential handling |
| `services/petdata/openapi.json` | app-code | full-read | clean — generated spec kept in sync with `app.openapi()` by a checked test; no internal-only routes or secrets leak into the public contract |
| `services/petdata/pyproject.toml` | config-IaC | full-read | clean — dependency manifest and tool config, no embedded credentials |
| `services/petdata/scripts/check_version.py` | app-code | full-read | clean — semver validation against `pyproject.toml`, no external input |
| `services/petdata/scripts/export_openapi.py` | app-code | full-read | clean — writes the generated spec to a stable path resolved from `__file__`, no injection surface |
| `services/petdata/src/petdata/__init__.py` | app-code | full-read | clean — package version export only |
| `services/petdata/src/petdata/config.py` | security-critical | line-by-line | finding — [F2] (#244): `cookies: str` (SMS session credential) is a plain `str` field while the structurally equivalent `database_url` is `SecretStr`; inconsistent secret-typing risks the cookie value appearing in a `repr()`/log of the `Settings` object |
| `services/petdata/src/petdata/infrastructure/__init__.py` | app-code | full-read | clean — empty package marker |
| `services/petdata/src/petdata/infrastructure/database/__init__.py` | app-code | full-read | clean — empty package marker |
| `services/petdata/src/petdata/infrastructure/database/session.py` | security-critical | line-by-line | finding — [F1] (#243): `get_session` never issues `SET LOCAL request.jwt.claims` (or any tenant GUC) on the request-scoped session, so the RLS policy in `001_initial_schema.py` has nothing to evaluate against even where it would otherwise apply; session lifecycle itself (commit on success, rollback on exception, lazy cached engine) is correct |
| `services/petdata/src/petdata/main.py` | security-critical | line-by-line | clean — CORS origins come from settings (no wildcard with `allow_credentials=True`); `/health` and `/llms.txt` are deliberately unauthenticated and return no sensitive data; protected router mounted with auth dependencies at include time |
| `services/petdata/src/petdata/models/__init__.py` | app-code | full-read | clean — re-export module only |
| `services/petdata/src/petdata/models/base.py` | security-critical | line-by-line | clean — `_async_url` strips `sslmode` via regex only to re-apply SSL through `connect_args["ssl"]="require"` when `require_ssl` is set; no downgrade path when `require_ssl=True` |
| `services/petdata/src/petdata/models/mappers.py` | app-code | full-read | clean — pure type coercion between Pydantic contract and ORM row; `tenant_id` deliberately excluded from the contract so it can't be set by a caller |
| `services/petdata/src/petdata/models/tables.py` | security-critical | line-by-line | clean — every tenant-owned table carries `tenant_id`; check constraints bound rating fields 0-5; foreign keys cascade-delete correctly |
| `services/petdata/src/petdata/modules/__init__.py` | app-code | full-read | clean — empty package marker |
| `services/petdata/src/petdata/modules/api/__init__.py` | app-code | full-read | clean — re-export module only |
| `services/petdata/src/petdata/modules/api/auth.py` | security-critical | line-by-line | clean — [F3] (#245) noted for context (this module produces the static `Cookie` header consumed by `client.py`'s `follow_redirects=True` client); `_validate_format` itself is clean, rejecting CR/LF/NUL header-injection characters and enforcing a strict `key=value` regex before the value is ever placed in a header |
| `services/petdata/src/petdata/modules/api/client.py` | security-critical | line-by-line | finding — [F3] (#245) [F6] (#248): `httpx.Client` is constructed with `follow_redirects=True` (line 56) and a static `Cookie` header from `CookieAuth.get_headers()` (line 55); because the cookie is a client-level header rather than a domain-scoped cookie-jar entry, httpx resends it on every redirect hop regardless of destination host, so a redirect from the configured SMS host leaks the session cookie to the redirect target. Separately, `_get_json` buffers the full response into memory via `response.json()` with no `max_response_size`/streaming cap, so a compromised/misbehaving SMS endpoint can return an oversized payload |
| `services/petdata/src/petdata/modules/api/exceptions.py` | app-code | full-read | clean — plain exception hierarchy, no sensitive data captured beyond truncated response bodies already destined for internal logs |
| `services/petdata/src/petdata/modules/api/parser.py` | app-code | full-read | finding — [F6] (#248): parses untrusted SMS JSON into models with explicitly-flagged PLACEHOLDER field mappings (lines 3-5, 48, 125, 187) and no upper bound on payload/record size before buffering into a Python list; a misbehaving or compromised SMS endpoint can return an oversized `records` array with no client-side cap, since `client.py`'s `httpx.Client` ([F6] (#248)) has no `max_response_size`/streaming limit either |
| `services/petdata/src/petdata/modules/auth/__init__.py` | app-code | full-read | clean — empty package marker |
| `services/petdata/src/petdata/modules/auth/dependencies.py` | security-critical | line-by-line | clean — JWKS validator is a cached singleton relying on `PyJWKClient(cache_keys=True)`'s 300s TTL for key rotation; raises loudly if `SUPABASE_URL` is unset rather than silently skipping auth |
| `services/petdata/src/petdata/modules/db/__init__.py` | app-code | full-read | clean — re-export module only |
| `services/petdata/src/petdata/modules/db/models.py` | app-code | full-read | clean — re-exports shared `evermore_schema` contract models; field-level validation bounds live in `packages/schema`, out of this slice's file scope |
| `services/petdata/src/petdata/modules/db/repository.py` | security-critical | line-by-line | finding — [F1] (#243) [F5] (#247): no query in this file filters by `tenant_id` (only `animal_id`/PK/`table_name`), so tenant scoping depends entirely on the RLS layer flagged inert in `001_initial_schema.py`; separately, every write path (`insert_*`/`update_*`/`delete_*`) carries no actor/`created_by` column and issues hard `DELETE`s with no soft-delete or versioning, so once the (not-yet-built) sync job starts writing, mutations will be unattributable and unrecoverable (feeds #230). SQL itself is safe: every statement uses SQLAlchemy Core with bound parameters, no raw string interpolation |
| `services/petdata/src/petdata/modules/web/__init__.py` | app-code | full-read | clean — empty package marker |
| `services/petdata/src/petdata/modules/web/dependencies.py` | app-code | full-read | clean — thin FastAPI DI wiring, no logic to audit beyond the session dependency it wraps |
| `services/petdata/src/petdata/modules/web/routes.py` | security-critical | line-by-line | finding — [F4] (#246): `list_animals` (lines 60-66) takes `limit: int = 100, offset: int = 0` with no `Query(le=..., ge=0)` bound, so a caller can request an unbounded `limit` (memory/DoS) or a negative `offset` that reaches the SQL `OFFSET` clause unvalidated; router-level `dependencies=[Depends(require_auth), Depends(require_subscription("petdata"))]` gating is otherwise correct and `animal_id` path values flow only into parameterized repository calls |
| `services/petdata/src/petdata/modules/web/schemas.py` | app-code | full-read | finding — [F4] (#246): no request-schema type constrains `limit`/`offset` (the route takes plain `int` params rather than a validated query model), so the unbounded-pagination gap in `routes.py` has no schema-level backstop; response models themselves are frozen with no computed fields that leak unintended data |
| `services/petdata/tests/conftest.py` | test | full-read | clean — shared fixtures only, no hardcoded live credentials |
| `services/petdata/tests/integration/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/integration/api/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/integration/api/test_client.py` | test | full-read | clean — exercises `SMSClient` against a local test double, no live SMS credentials |
| `services/petdata/tests/integration/db/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/integration/db/test_alembic.py` | test | full-read | clean — upgrade/downgrade round-trip against the ephemeral test database |
| `services/petdata/tests/integration/db/test_repository.py` | test | full-read | clean — repository CRUD round-trips against the ephemeral test database |
| `services/petdata/tests/integration/web/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/integration/web/test_llms_txt.py` | test | full-read | clean — asserts the discovery route is reachable and well-formed, consistent with its intended unauthenticated status |
| `services/petdata/tests/test_openapi_spec.py` | test | full-read | clean — asserts the committed `openapi.json` matches the live app spec (drift guard) |
| `services/petdata/tests/unit/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/unit/api/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/unit/api/test_auth.py` | test | full-read | clean — cookie-format validation tests use synthetic values (`abc123`, `xyz789`), not live cookies |
| `services/petdata/tests/unit/api/test_exceptions.py` | test | full-read | clean — exception construction/attribute tests only |
| `services/petdata/tests/unit/api/test_parser.py` | test | full-read | clean — parser tests use synthetic SMS-shaped fixtures, none of the PLACEHOLDER-field / oversized-input risk from `[F6] (#248)` is exercised with adversarial (oversized) input |
| `services/petdata/tests/unit/db/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/unit/db/test_models.py` | test | full-read | clean — model validation unit tests |
| `services/petdata/tests/unit/models/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/unit/models/test_base.py` | test | full-read | clean — exercises `_async_url` including the `sslmode`-stripping regex; no assertion of the `require_ssl=True` + malicious sslmode-in-URL interaction, minor coverage gap rather than a vulnerability |
| `services/petdata/tests/unit/models/test_mappers.py` | test | full-read | clean — round-trip mapping tests confirm `tenant_id` is excluded from the contract |
| `services/petdata/tests/unit/models/test_pool.py` | test | full-read | clean — connection-pool configuration tests |
| `services/petdata/tests/unit/models/test_tables.py` | test | full-read | clean — ORM table/constraint tests |
| `services/petdata/tests/unit/test_auth.py` | test | full-read | clean — JWT-based `require_auth`/`require_admin`/`require_subscription` tests use locally-signed synthetic tokens, not real Supabase secrets |
| `services/petdata/tests/unit/web/__init__.py` | test | full-read | clean — empty package marker |
| `services/petdata/tests/unit/web/test_routes.py` | test | full-read | clean — route tests confirm auth/subscription gating and repository wiring |
| `services/petdata/uv.lock` | generated | config-scan | clean — dependency lockfile, only version/hash pins, no credentials |
| `services/petdata/worker/index.ts` | security-critical | line-by-line | clean — `FORWARDED_ENV_KEYS` (lines 20-28) explicitly lists `PETDATA_COOKIES` and `PETDATA_DATABASE_URL` for forwarding into the container from Wrangler secret bindings; this is the intended, documented mechanism (secrets are never committed, only injected via `wrangler secret put`) — considered as a candidate finding and dropped (working as intended, not a code defect) |
| `services/petdata/worker/package-lock.json` | generated | config-scan | clean — npm lockfile, only version/integrity hashes |
| `services/petdata/worker/package.json` | config-IaC | full-read | clean — Worker package manifest, no secrets |
| `services/petdata/worker/tsconfig.json` | config-IaC | full-read | clean — standard Cloudflare Workers TypeScript config |
| `services/petdata/wrangler.jsonc` | security-critical | line-by-line | clean — `vars` carries only non-secret config (`PORT`, the production CORS allow-list); comments correctly state secrets are injected via `wrangler secret put` and never committed here |

Findings summary: `[F1] (#243)` tenant isolation inert (RLS `ENABLE` not `FORCE`, app connects as table owner, no session tenant GUC, repository has no tenant filter; ref #29), `[F2] (#244)` credential handling (untyped `cookies` field, not `SecretStr`), `[F3] (#245)` outbound egress/SSRF (httpx redirect + static `Cookie` header), `[F4] (#246)` API surface (`/animals` unbounded `limit`/`offset`, negative offset reaches SQL), `[F5] (#247)` mutation surface (repository writes carry no actor/attribution column, no soft-delete/versioning; feeds #230), `[F6] (#248)` ingestion boundary (SMS client/parser have no response/record size cap). Dropped candidate: Worker secret-forwarding design (`worker/index.ts`) — working as intended, not filed. Disposition, severity, and redacted actor/path/asset detail for each are recorded in the audit notes on issue #225.

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

## retriever (issue #226 slice)

Ticket estimated 160 tracked files under `services/retriever`; the live count at execution time (base `e9a2768`, 2026-07-05) is **138**, a delta of -22. The gap is pre-existing drift between the ticket's estimate and the repo (module consolidation, generated-file churn since the estimate was written), not a sign of missing files: the slice below is the full, current `git ls-files services/retriever` output, one row per file, no omissions.

**Secret-scan disposition:** a pattern sweep for API-key shapes (`sk-...`, `AKIA...`, `AIza...`), PEM private-key headers, and inline `password=`/`secret=` literals across every file in this slice (source, config, docs, tests) found zero matches. `.env.example` contains placeholder values only; every live secret field in `config.py` is `SecretStr`; `.env` itself is gitignored and not part of this slice.

| File | Class | Depth | Verdict |
|---|---|---|---|
| `services/retriever/.dockerignore` | config-IaC | full-read | clean -- full-read: excludes .env, __pycache__, .venv from build context |
| `services/retriever/.env.example` | config-IaC | full-read | clean -- full-read: placeholders only, no live secrets |
| `services/retriever/alembic.ini` | config-IaC | full-read | clean -- full-read: migration runner config, DB URL sourced from env at runtime not inlined |
| `services/retriever/alembic/env.py` | config-IaC | full-read | clean -- full-read: migration environment bootstrap, reads DATABASE_URL from settings, no inlined credentials |
| `services/retriever/alembic/README` | inert | secret-scan + claim-check | clean -- secret-scan clean; prose, no code claims to verify |
| `services/retriever/alembic/script.py.mako` | config-IaC | full-read | clean -- full-read: migration template, no logic |
| `services/retriever/alembic/versions/001_initial_schema.py` | security-critical | line-by-line | See #230 (data-integrity handoff, #230) -- ENABLE ROW LEVEL SECURITY present but no CREATE POLICY/FORCE ROW LEVEL SECURITY in-repo; tenant scoping is app-layer only |
| `services/retriever/alembic/versions/002_vector_storage.py` | security-critical | line-by-line | See #230 (data-integrity handoff, #230) -- RLS enabled on document_chunks, no in-repo policy |
| `services/retriever/alembic/versions/003_semantic_cache.py` | security-critical | line-by-line | See #230 (data-integrity handoff, #230) -- RLS enabled on semantic_cache, no in-repo policy |
| `services/retriever/alembic/versions/004_updated_at_trigger.py` | config-IaC | full-read | clean -- full-read: schema-only trigger migration, no RLS/policy content |
| `services/retriever/alembic/versions/005_document_columns.py` | config-IaC | full-read | clean -- full-read: schema-only column-add migration, no RLS/policy content |
| `services/retriever/assets/logo.png` | inert | secret-scan + claim-check | clean -- binary asset, secret-scan clean |
| `services/retriever/CHANGELOG.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/CLAUDE.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/docker-compose.test.yml` | config-IaC | full-read | clean -- full-read: test-only overrides, no secrets |
| `services/retriever/docker-compose.yml` | config-IaC | full-read | clean -- full-read: local pgvector+jaeger only, no prod credentials |
| `services/retriever/Dockerfile` | config-IaC | full-read | clean -- full-read: multi-stage, non-root user, path-scoped COPY, no baked-in secrets |
| `services/retriever/docs/architecture.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/docs/development-standards.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/docs/guides/adding-documents.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/docs/guides/cloudflare-containers.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/docs/guides/deployment.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/entrypoint.sh` | config-IaC | full-read | clean -- full-read: no hardcoded credentials, execs uvicorn directly |
| `services/retriever/openapi.json` | config-IaC | full-read | clean -- full-read: generated OpenAPI spec, no secrets, matches live routes |
| `services/retriever/pyproject.toml` | config-IaC | full-read | clean -- full-read: dependency + tool config, no secrets |
| `services/retriever/README.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; claims checked against current code/config, no drift found |
| `services/retriever/scripts/export_openapi.py` | config-IaC | full-read | clean -- full-read: generates openapi.json from the app instance, no side effects beyond file write |
| `services/retriever/src/retriever/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/config.py` | security-critical | line-by-line | #254 -- database_require_ssl defaults False with no deploy-surface override in-repo; also the source of the single llm_gateway_token, see #228 (LLM-abuse handoff, #228) |
| `services/retriever/src/retriever/infrastructure/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/cache/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/cache/pg_cache.py` | security-critical | line-by-line | clean -- semantic cache keyed by embedding + tenant_id; parameterized SQLAlchemy; cache-hit re-serving without re-screening is tracked as part of #250's path map, not a separate finding on this file |
| `services/retriever/src/retriever/infrastructure/cache/protocol.py` | security-critical | line-by-line | clean -- Protocol interface definition only, no logic |
| `services/retriever/src/retriever/infrastructure/database/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/database/session.py` | security-critical | line-by-line | #254 -- require_ssl is threaded from settings.database_require_ssl, which defaults False |
| `services/retriever/src/retriever/infrastructure/embeddings/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/embeddings/exceptions.py` | security-critical | line-by-line | clean -- typed exception classes only, no logic |
| `services/retriever/src/retriever/infrastructure/embeddings/openai.py` | security-critical | line-by-line | clean -- embedding client via injected gateway client, no hardcoded credentials |
| `services/retriever/src/retriever/infrastructure/embeddings/protocol.py` | security-critical | line-by-line | clean -- Protocol interface definition only, no logic |
| `services/retriever/src/retriever/infrastructure/llm/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/llm/exceptions.py` | security-critical | line-by-line | clean -- typed exception classes only, no logic |
| `services/retriever/src/retriever/infrastructure/llm/fallback.py` | security-critical | line-by-line | clean -- circuit-breaker/retry wrapper around the primary provider, no auth or data-handling logic |
| `packages/llm/src/evermore_llm/gateway_client.py` | security-critical | line-by-line | See #228 (LLM-abuse handoff, #228) -- single static gateway bearer token, no per-scope rotation |
| `services/retriever/src/retriever/infrastructure/llm/openai_compat.py` | security-critical | line-by-line | clean -- OpenAI-compat chat client using the injected gateway client; no hardcoded credentials |
| `services/retriever/src/retriever/infrastructure/llm/protocol.py` | security-critical | line-by-line | clean -- Protocol interface definition only, no logic |
| `services/retriever/src/retriever/infrastructure/observability/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/observability/langfuse.py` | security-critical | line-by-line | clean -- @observe() no-ops without credentials configured; question/answer tracing is opt-in and matches ADR 0026 |
| `services/retriever/src/retriever/infrastructure/observability/logging.py` | security-critical | line-by-line | clean -- structlog JSON configuration, no sensitive-field logging found |
| `services/retriever/src/retriever/infrastructure/observability/middleware.py` | security-critical | line-by-line | clean -- ExceptionHandlingMiddleware returns a generic 500 body ("Internal server error") with no internal detail leaked; RequestIdMiddleware only echoes/generates a UUID |
| `services/retriever/src/retriever/infrastructure/observability/tracing.py` | security-critical | line-by-line | clean -- OTel exporter selection (GCP/OTLP/console/no-op); no secrets in span attributes found |
| `services/retriever/src/retriever/infrastructure/safety/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/safety/confidence.py` | security-critical | line-by-line | clean -- advisory scorer only, gates caching not delivery, no security-relevant logic |
| `services/retriever/src/retriever/infrastructure/safety/detector.py` | security-critical | line-by-line | clean as far as it goes -- regex-based injection patterns are real but scoped to the question only; the coverage gap is tracked as #250 on service.py/prompts.py, not a defect in this file's own logic |
| `services/retriever/src/retriever/infrastructure/safety/hallucination.py` | security-critical | line-by-line | clean -- keyword-overlap heuristic is a known-weak but intentional MVP grounding check; no unguarded exception path found that would crash the request |
| `services/retriever/src/retriever/infrastructure/safety/moderation.py` | security-critical | line-by-line | clean -- OpenAIModerator fails open on timeout/400/exception by explicit design (documented tradeoff, avoids blocking legitimate requests); GuardrailsModerator delegation to gateway-side enforcement is a deliberate no-op, not a silent bug |
| `services/retriever/src/retriever/infrastructure/safety/schemas.py` | security-critical | line-by-line | #255 -- SafetyViolationType values (prompt_injection/moderation_flagged/hallucination) surface in blocked_reason, a 3-way oracle for evasion tuning |
| `services/retriever/src/retriever/infrastructure/safety/service.py` | security-critical | line-by-line | #251 -- check_output() (post-generation moderation) is fully implemented but has no caller in the live ask() pipeline |
| `services/retriever/src/retriever/infrastructure/storage/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/storage/exceptions.py` | security-critical | line-by-line | clean -- typed exception classes only, no logic |
| `services/retriever/src/retriever/infrastructure/storage/memory.py` | security-critical | line-by-line | clean -- in-memory test double for the storage protocol, not used in production wiring |
| `services/retriever/src/retriever/infrastructure/storage/protocol.py` | security-critical | line-by-line | clean -- Protocol interface definition only, no logic |
| `services/retriever/src/retriever/infrastructure/storage/r2.py` | security-critical | line-by-line | clean -- dead code, not wired into any live handler (config fields exist but no request-driven call path reaches this module); no live egress |
| `services/retriever/src/retriever/infrastructure/vectordb/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/infrastructure/vectordb/pgvector_store.py` | security-critical | line-by-line | See #230 (data-integrity handoff, #230) -- tenant scoping via app-layer WHERE tenant_id= filter only; parameterized SQLAlchemy, no SQLi surface |
| `services/retriever/src/retriever/infrastructure/vectordb/protocol.py` | security-critical | line-by-line | clean -- Protocol interface definition only, no logic |
| `services/retriever/src/retriever/main.py` | security-critical | line-by-line | See #228 (LLM-abuse handoff, #228) -- no slowapi/rate-limit middleware wired; any authenticated+subscribed user drives unbounded gateway calls |
| `services/retriever/src/retriever/models/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/models/base.py` | security-critical | line-by-line | clean -- declarative base only, no logic |
| `services/retriever/src/retriever/models/document.py` | security-critical | line-by-line | clean -- SQLAlchemy model, tenant_id defaults to DEFAULT_TENANT_ID (tracked under #230 on models/user.py) |
| `services/retriever/src/retriever/models/message.py` | security-critical | line-by-line | clean -- SQLAlchemy model, tenant_id defaults to DEFAULT_TENANT_ID (tracked under #230 on models/user.py) |
| `services/retriever/src/retriever/models/user.py` | security-critical | line-by-line | See #230 (data-integrity handoff, #230) -- DEFAULT_TENANT_ID hardcoded single-tenant UUID; no DB-level tenant backstop |
| `services/retriever/src/retriever/modules/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/modules/auth/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/modules/auth/dependencies.py` | security-critical | line-by-line | clean -- wires shared evermore_auth JwksValidator (RS256/ES256 allowlist, no alg confusion); require_auth/require_admin/require_subscription correctly gate every route |
| `services/retriever/src/retriever/modules/documents/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/modules/documents/exceptions.py` | security-critical | line-by-line | clean -- typed exception classes only, no logic |
| `services/retriever/src/retriever/modules/documents/repos.py` | security-critical | line-by-line | clean -- parameterized SQLAlchemy queries, tenant-scoped |
| `services/retriever/src/retriever/modules/documents/routes.py` | security-critical | line-by-line | #252 -- upload_document includes raw exception text in HTTPException detail (file-read failures and DocumentIndexingError both interpolate str(exc)) |
| `services/retriever/src/retriever/modules/documents/schemas.py` | security-critical | line-by-line | clean -- Pydantic schemas only, no logic |
| `services/retriever/src/retriever/modules/documents/services.py` | security-critical | line-by-line | clean -- orchestrates upload/index/delete; propagates rag_service errors, tracked under #252 at the route layer |
| `services/retriever/src/retriever/modules/messages/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/modules/messages/repos.py` | security-critical | line-by-line | #256 -- persisted conversation turns replay into every later model call with no re-screening |
| `services/retriever/src/retriever/modules/messages/routes.py` | security-critical | line-by-line | clean -- require_auth on both routes; DEFAULT_TENANT_ID usage tracked under #230 |
| `services/retriever/src/retriever/modules/messages/schemas.py` | security-critical | line-by-line | clean -- Pydantic schemas only, no logic |
| `services/retriever/src/retriever/modules/rag/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; empty or re-export-only package init |
| `services/retriever/src/retriever/modules/rag/dependencies.py` | security-critical | line-by-line | clean -- FastAPI dependency wiring only; DEFAULT_TENANT_ID usage tracked under #230 (models/user.py) |
| `services/retriever/src/retriever/modules/rag/docling_processor.py` | security-critical | line-by-line | #253 -- DoclingConfig.max_pages is defined and threaded through config but never read/enforced in process(); only the 20MB upload size cap bounds a document |
| `services/retriever/src/retriever/modules/rag/exceptions.py` | security-critical | line-by-line | clean -- typed exception classes only, no logic |
| `services/retriever/src/retriever/modules/rag/loader.py` | security-critical | line-by-line | clean -- file validation and format-aware size limits; no injection or path-traversal surface found |
| `services/retriever/src/retriever/modules/rag/prompts.py` | security-critical | line-by-line | #250 -- build_rag_prompt embeds retrieved chunk content verbatim into the system-role prompt with no injection/moderation screening |
| `services/retriever/src/retriever/modules/rag/retriever.py` | security-critical | line-by-line | clean -- HybridRetriever composes semantic+keyword search scoped by tenant_id param; no unparameterized SQL |
| `services/retriever/src/retriever/modules/rag/routes.py` | security-critical | line-by-line | clean -- require_auth on /ask and /history; blocked_reason exposure tracked as #255 on service.py, not a separate issue here |
| `services/retriever/src/retriever/modules/rag/schemas.py` | security-critical | line-by-line | clean -- Pydantic schemas only, no logic |
| `services/retriever/src/retriever/modules/rag/service.py` | security-critical | line-by-line | #250, #255, #256 -- unscreened chunks reach system prompt; blocked_reason leaks violation category; unscreened history replay |
| `services/retriever/tests/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/conftest.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/__init__.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/conftest.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/fixtures/test-doc.md` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_auth_flow.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_document_lifecycle.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_health.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_input_validation.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_rag_and_history.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/integration/test_rate_limit_and_concurrency.py` | inert | secret-scan + claim-check | See #228 (LLM-abuse handoff, #228) -- docstring documents intended rate-limit behavior; no app-level limiter exists to test against (test-only artifact, no risk itself) |
| `services/retriever/tests/test_auth.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_cache.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_config.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_docling_processor.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_document_routes.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_document_service.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_embeddings.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_error_handling.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_gateway_client.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_health.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_hybrid_retriever.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_llm_fallback.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_llm_provider.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_loader.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_message_repos.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_message_routes.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_models.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_observability.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_openapi_spec.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_prompts.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_rag_dependencies.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_rag_routes.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_rag_service.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_safety.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_storage.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_subscription_guard.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/tests/test_vectordb.py` | inert | secret-scan + claim-check | clean -- secret-scan clean; test-only artifact, no production risk |
| `services/retriever/uv.lock` | config-IaC | full-read | clean -- full-read: lockfile, no secrets |
| `services/retriever/worker/index.ts` | config-IaC | full-read | clean -- full-read: pure reverse-proxy Worker, no secret material or logic beyond forwarding |
| `services/retriever/worker/package-lock.json` | config-IaC | full-read | clean -- full-read: lockfile, no scripts of concern |
| `services/retriever/worker/package.json` | config-IaC | full-read | clean -- full-read: dependency manifest, no scripts of concern |
| `services/retriever/worker/tsconfig.json` | config-IaC | full-read | clean -- full-read: compiler config only |
| `services/retriever/wrangler.jsonc` | config-IaC | full-read | clean -- full-read: Cloudflare Worker config; secrets via `wrangler secret put`, none inlined |

138 files in the retriever slice as of this PR tree (base `e9a2768`); ticket estimated 160, delta -22, per the plan's live-count note. Every row above carries a definitive verdict, none left as `pending audit`: the 7 findings owned by #226 (#250, #251, #252, #253, #254, #255, #256) are filed as GitHub issues (`security` label) and cited on their evidence rows (detail in the audit comment); the RLS/tenant-isolation gap is handed off to #230, and the rate-limit (denial-of-wallet) and gateway-token blast-radius gaps to #228, per the plan and cited on their evidence rows; every remaining row is `clean` with a file-specific rationale.

## Slice: reconciliation-time additions (issue #222)

Five tracked files carried no ledger row after the four sweeps: two top-level tooling files (outside every module sweep's scope) and the three cross-cutting audit documents the sweeps themselves produced. They are ledgered here during the epic #222 reconciliation. All five were secret-scanned clean.

| File | Class | Depth | Verdict |
|---|---|---|---|
| `scripts/check-doc-links.py` | config-IaC | full-read | clean -- full-read: fixed-arg `git` subprocess (no shell), reads tracked markdown only, checks path existence; no network, no secret handling, no injection surface |
| `tools/llm-stub/llm_stub.py` | boundary-adjacent | trust-review | clean -- trust-review: stdlib-only local-dev OpenAI-compatible stub; binds `127.0.0.1` by default, serves fake canned data, no secrets, no outbound egress. `$LLM_STUB_HOST` can widen the bind but exposes only stub data (no security asset) |
| `docs/security/data-integrity-recovery.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: #230 audit output, redacted per disclosure discipline, no secrets |
| `docs/security/llm-abuse-surface.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: #228 audit output, redacted per disclosure discipline, no secrets |
| `docs/security/stacker-packages-audit.md` | inert | secret-scan + claim-check | clean -- secret-scan + claim-check: #227 audit output, redacted per disclosure discipline, no secrets |

5 files in this slice. The remaining coverage gap is the `services/biowriter/` design subtree (19 tracked files), deferred to #267 to be swept when biowriter is scaffolded (Phase 5); a reconciliation-time secret-scan of those 19 files found no secrets. With this slice, ledger coverage is 447 of 466 tracked files finalized; the 19 deferred biowriter files are the only remaining gap, tracked and documented (`docs/security/reconciliation.md`).
