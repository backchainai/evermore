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
