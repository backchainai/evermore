# Data Integrity and Recovery Assessment (issue #230)

Reconciliation for issue #230, epic #222 (repo-wide threat-model audit). This is the reconciliation child that assesses resilience to destructive and corrupting attacks (threat-model threats 3 ransomware/destructive, 4 data-mutation, 5 defacement) as a posture question, not a per-route sweep. It consumes the mutation-surface and RLS findings already recorded by the module sweeps: petdata (#225), retriever (#226), stacker + packages (#227), in `docs/security/coverage-ledger.md` and `docs/security/stacker-packages-audit.md`. Redacted per the epic's public-repo discipline; exploitable and credential-specific detail goes to the private channel, `security@backchain.ai`.

Assets, ranked per `docs/security/threat-model.md`: 1) animal records and generated adoption content (integrity, the top asset), 2) staff/adopter PII, 3) LLM gateway credentials and spend, 4) SMS session credentials, 5) DB service keys, 6) CI secrets and deploy tokens, 7) repository integrity.

## Recovery matrix

| Asset | Destroy: detected? | Destroy: recoverable? | Destroy: latency | Corrupt: detected? | Corrupt: recoverable? | Corrupt: latency | Deface: detected? | Deface: recoverable? | Deface: latency |
|---|---|---|---|---|---|---|---|---|---|
| Animal records + generated content | No system alert; DB-level absence only | Only via unverified Supabase platform backup | Unbounded (until a human notices missing data) | No audit trail, no integrity check | No: hard delete, no soft-delete, no row versioning (petdata) | Unbounded (until a human notices by eye) | No per-row actor attribution, no audit trail | No: same as corrupt, no versioning | Unbounded (until a human notices public-facing content) |
| Staff/adopter PII | No system alert | Only via unverified Supabase platform backup | Unbounded | No audit trail | No versioning | Unbounded | N/A (not a defacement target) | N/A | N/A |
| LLM gateway creds/spend | Out of scope here, handed to #228 | - | - | - | - | - | - | - | - |
| SMS session creds | Detected only via upstream re-auth failure | Manual re-auth (upstream system, not Evermore-recoverable) | Depends on staff noticing | Not applicable (credential, not a record) | - | - | - | - | - |
| DB service keys | No rotation alerting documented | Manual rotation, undocumented cadence | Unbounded | - | - | - | - | - | - |
| CI secrets/deploy tokens | GitHub secret-access logging only | GitHub secret rotation, undocumented cadence | Depends on review cadence | - | - | - | - | - | - |
| Repository integrity | Git history detects tampering | Yes: redeploy from source (code is in git) | Bounded (git provides this) | Git detects | Yes, via git | Bounded | Git detects | Yes, via git | Bounded |

Summary reality: destruction of animal records, generated content, and PII is recoverable only through unverified Supabase platform backups. Corruption and defacement of records and content are largely undetected: there is no per-row actor attribution, no audit trail, no integrity check, and no functional versioning anywhere in the write path. Detection latency for both is effectively unbounded until a human notices by eye. Repository integrity (code) is the one asset with a real, git-backed recovery story; data is not.

## Backup / PITR posture

No ADR documents backup or recovery posture (checked `docs/adr/0025-petdata-postgres-pgvector.md` and `docs/adr/0030-per-service-supabase-projects.md`), and no in-repo document records backup frequency, retention, PITR tier, or a tested restore. The data store is Supabase-managed Postgres, one project per service (ADR 0030). Recovery therefore relies entirely on Supabase platform defaults, which are tier-dependent (daily backups on paid tiers; point-in-time recovery is a separate add-on) and are neither documented nor restore-tested anywhere in this repo.

Honest verdict: backup *existence* is assumed from the platform default tier; backup *frequency*, *retention*, and *restore-tested* status are all UNVERIFIED. This gap is itself a finding: recovery is the entire subject of this assessment, animal records are the top-ranked asset, and the design partner is a pro-bono shelter with limited capacity to notice data loss or to drive a restore effort unassisted.

## Mutation attributability

| Mutation path | Attributable (who/when)? | Detectable (audit/integrity)? | Reversible (versioning/soft-delete/restore)? |
|---|---|---|---|
| petdata repository writes (insert/update/delete across `petdata_animals`, `petdata_behavior_profiles`, `petdata_volunteer_notes`, `petdata_staff_assessments`, `petdata_walk_records`, `petdata_animal_images` via `modules/db/repository.py`) | No: rows carry `created_at`/`updated_at` only, no `created_by`/actor column | Weak: `petdata_sync_log` records sync events but not per-row actor, and no integrity/checksum check exists | No: hard `DELETE`, no soft-delete, no row versioning (ref #247, petdata F5) |
| petdata tenant isolation (`modules/db/repository.py`, `alembic/001_initial_schema.py`, `infrastructure/database/session.py`) | No DB-layer backstop: RLS is `ENABLE` not `FORCE`, the app connects as the table-owner role (which bypasses RLS), no `SET LOCAL request.jwt.claims` tenant GUC is issued, no query filters `tenant_id` | Same: a compromised DB credential can mutate across tenants undetected at the DB layer | No (ref #243, petdata F1) |
| retriever writes (`documents`, `messages`, `document_chunks`, `semantic_cache` via `infrastructure/vectordb/pgvector_store.py` and models) | App-layer only: tenant scoping is a `WHERE tenant_id=` filter, no DB backstop; `alembic` 001/002/003 `ENABLE` RLS with no `CREATE POLICY`/`FORCE` in-repo; `DEFAULT_TENANT_ID` is a hardcoded single-tenant UUID | App-layer only, no DB-level attribution | No: not versioned, not soft-deleted |
| stacker Stripe webhook -> service-role upsert to `public.subscriptions` | Attributable to the webhook path itself (signature-verified), but the `service_role` key bypasses RLS for the whole schema | Detectable via Stripe's own event log, not an Evermore-side audit trail | Upsert is idempotent for the same event, but no row-history table exists |

Note on petdata writes: no live write path exists yet (the SMS sync job is not built), so this exposure is latent today. It rises to High once sync writes begin.

## Defacement detection

A low-privilege or compromised staff account, or any actor reaching the inert-RLS DB layer directly, can alter animal records (name, breed, `photo_url`, `public_profile_url`) or generated content. Because there is no per-row actor attribution, no edit audit trail, and no integrity check, and because `photo_url`/`public_profile_url` feed public-facing content, an unauthorized edit is undetectable by the system: detection latency is effectively unbounded and depends entirely on a human noticing by eye before an adopter sees it. For generated content specifically, no persistence or versioning exists yet (see Composition versioning below), so there is nothing to diff against even after the fact.

## Credential blast-radius map

| Credential (redacted role) | Where it lives (redacted) | Can mutate/destroy | Recoverable? | Rotation story |
|---|---|---|---|---|
| petdata DB URL, table-owner role | petdata service env | Full write and hard `DELETE` on all `petdata_*` tables, bypasses RLS (owner role) | Only via unverified Supabase backup | Manual, no documented rotation |
| retriever DB URL | retriever service env | Write/delete documents, messages, chunks, semantic cache | Only via unverified Supabase backup | Manual, undocumented |
| Supabase service-role key (stacker Stripe webhook) | stacker server env | RLS-bypass writes to `public.subscriptions` and anything `service_role` can reach | Only via unverified Supabase backup | Manual, undocumented |
| SMS session cookie | petdata service env | No write to Evermore data directly, but controls the ingestion source and can poison inbound records; also untyped as a plain `str` (ref #244, petdata F2) | Not applicable (upstream system) | Manual re-auth, undocumented |
| LLM gateway token | retriever service env | Spend / denial-of-wallet, not a data-integrity asset | Not applicable | Handed to #228 |
| Stripe webhook signing secret | stacker server env | Forge webhook events to fabricate subscription state | Not applicable | Stripe dashboard |
| CI deploy tokens (Cloudflare API token, `CLAUDE_CODE_OAUTH_TOKEN`) | GitHub Actions secrets | Deploy or overwrite running services, drive repo automation | Redeploy from source (code is in git; data is not) | GitHub secret rotation, undocumented cadence |

## Composition / record versioning

Checked as a functional rollback mechanism, not merely a schema field:

- **Animal Record.** petdata tables carry `created_at`/`updated_at` only: no version history and no soft-delete. An overwrite or delete is lossy. There is no functional rollback at the record layer (ref #247).
- **Composition.** `evermore_schema.spine.Composition` (`packages/schema`) is a Pydantic contract with a `version: int = 1` field, but there is no persistence table, no migration, and no version-history store anywhere in the repo. `biowriter`, the module that would persist Compositions, is not yet scaffolded (Phase 5/6 per the top-level CLAUDE.md). The data-spine's "auto-versioned Composition" description does not function as rollback today: the version field is a contract default, not a stored history. This is a gap, not a verified control.

## Finding disposition

Already filed, referenced here rather than duplicated:

- #247, petdata writes are unattributable and non-recoverable (hard delete, no versioning).
- #243, petdata tenant-isolation RLS is inert (enabled but not forced, owner-role connection bypasses it).
- #250, retriever's unscreened-content-to-prompt path, the content-corruption vector for generated output.

Recommended for filing (new gaps this reconciliation surfaces, not covered by the above):

1. **Backup/PITR posture undocumented and restore untested** for all Supabase-backed data. Asset: animal records + generated content (top-ranked asset). Severity: High, recovery of the top asset is unverified end to end.
2. **No functional rollback for Animal Records or Compositions.** Versioning is contract-only (a default field value), not a stored history. Severity: Medium today, rising as petdata sync writes and biowriter persistence land.
3. **retriever tenant isolation lacks a DB-layer backstop.** RLS is enabled with no policy and no `FORCE`; this parallels #243 but for the retriever service. Severity: Medium.

Redacted to the private channel (`security@backchain.ai`): exact credential storage locations, concrete restore-runbook gaps, and any Supabase tier/spend specifics.
