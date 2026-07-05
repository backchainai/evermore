# Epic #222 Reconciliation

Final reconciliation for epic #222 (audit every file and workflow against a threat model). This is the epic's closing step: it verifies the success criteria, maps every threat in `docs/security/threat-model.md` to a verified control or an open finding, and records the coverage state and residual gaps. Redacted per the epic's public-repo discipline; exploitable and credential-specific detail routes to the private channel, `security@backchain.ai` (`SECURITY.md`).

## Inputs

- Threat model: `docs/security/threat-model.md`
- Coverage ledger: `docs/security/coverage-ledger.md` (four sweep slices plus the reconciliation-time additions)
- Cross-cutting assessments: `docs/security/llm-abuse-surface.md` (#228), `docs/security/data-integrity-recovery.md` (#230), `docs/security/stacker-packages-audit.md` (#227)
- Child issues: #224, #225, #226, #227, #228, #230 (all closed)

## Success-criteria status

| # | Criterion | Status |
|---|---|---|
| 1 | All child issues closed | Met: #224, #225, #226, #227, #228, #230 all closed |
| 2 | `threat-model.md` committed and matching the epic summary | Met |
| 3 | Coverage-ledger union equals every tracked file; none lacks class, depth, verdict | Met with one documented deferral: 447 of 466 files finalized; 19 `services/biowriter/` design files deferred to #267 (secret-scan clean) |
| 4 | Every finding has actor/path/asset/severity; Critical/High have a follow-on issue or private report | Met |
| 5 | Reconciliation table maps each threat to a verified control or an open finding | Met (below) |

## Threat reconciliation

Each row maps a threat-model threat to the controls verified during the audit and the open findings that remain. Severity is exploitability times asset, per the threat model.

| # | Threat | Verified control(s) | Open finding(s) | Net verdict |
|---|---|---|---|---|
| 1 | LLM prompt injection | Auth + subscription gate on `/ask`; regex injection detector (closed on match); model output is text-only (no tool-use in-service) | #250 corpus reaches system prompt unscreened; #256 conversation history replays unscreened; #251 output moderation never invoked; #255 safety-rail disclosure; stacker FINDING-S1 `{@html}` XSS sink (private report) | Open: front layer holds, defense layers missing |
| 2 | LLM repurposing / denial-of-wallet | Auth + subscription; `claude.yml` read-only token; fork-PR secret withholding | #261 no `/ask` rate limit; #262 gateway-token blast radius + no spend ceiling; #263 anonymous denial-of-wallet via `claude.yml` | Open: auth holds, no throughput or spend ceiling |
| 3 | Ransomware / destructive compromise | Code and repository are git-recoverable; Supabase platform backup (existence assumed) | #264 backup/PITR undocumented and restore untested; #247 petdata hard-delete non-recoverable | Open: code recoverable, data recovery unverified |
| 4 | Data-mutation attacks | Application-layer tenant filters | #247 unattributed writes; #265 no functional rollback; #243 / #266 RLS inert, no DB-layer backstop; #250 content-corruption vector | Open: mutations largely undetected |
| 5 | Defacement / troll mutation | (none effective today) | #247, #265 (no per-row attribution, audit trail, or integrity check; detection latency unbounded) | Open: undetectable per the #230 assessment |
| 6 | Resource takeover / SSRF | Retriever gateway URL is config-pinned (no request-controlled egress); R2 storage code is dead | #245 SMS client resends session cookie across redirects; #248 SMS extraction has no response/record size cap | Retriever clean; petdata egress open |
| B1 | Secret / credential exposure | Secret scanning + push protection enabled (#224); full-history gitleaks scan clean (#224 C3); reconciliation secret-scan of unledgered files clean | #244 SMS session cookie not wrapped in `SecretStr`; credential-rotation cadence undocumented (recorded in the #230 credential blast-radius map) | Controlled, with a hygiene gap |
| B2 | Cross-tenant leakage (RLS) | Application-layer tenant filters | #243 petdata RLS inert (enabled not forced, owner-role connection bypasses it); #266 retriever lacks a DB-layer backstop | Open: no database-layer backstop |
| B3 | CI/CD compromise | #224: SHA-pinned actions, per-workflow `permissions:` blocks, CodeQL, read-only agent tokens, fork-PR secret withholding, deliberate branch-injection handling in `deploy.yml` | #263 anonymous denial-of-wallet trigger (repo mutation blocked); #268 `claude-code-review.yml` unpinned runtime marketplace + fork-PR author gate commented out | Hardened; residual agent-workflow findings |
| B4 | Dependency supply chain | #224: SHA-pinned actions, Dependabot enabled | #241 docling upgrade past Dependabot-flagged versions; the Dependabot alert backlog remains open | Open: patch backlog |

Every threat maps to at least one verified control or open finding. Criterion 5 is met.

## Coverage state

The coverage-ledger union finalizes 447 of 466 tracked files, each with a class, depth, and finalized verdict.

- The #224 slice (73 files: all of `.github/`, all of `docs/`, and root files) was seeded `pending audit` in PR #242 and its verdicts were recorded in the #224 issue comment rather than written back. They are finalized here by transcription: the two agent-workflow findings map to #263 (`claude.yml`) and #268 (`claude-code-review.yml`); the other 71 rows are clean, grounded in #224's per-workflow audit and full-history secret scan.
- Two top-level tooling files (`scripts/check-doc-links.py`, `tools/llm-stub/llm_stub.py`) and the three cross-cutting audit documents were ledgered during this reconciliation. All five are clean.
- The `services/biowriter/` design subtree (19 tracked files) was never assigned to a sweep. biowriter is unscaffolded (Phase 5), so its coverage is deferred to #267, to be swept when the module is scaffolded. A reconciliation-time secret-scan of those 19 files found no secrets. This is the only remaining coverage gap and it is tracked.

## Finding inventory

Twenty-two findings are filed as `security`-labeled GitHub issues, plus one private report:

- petdata (#225): #243, #244, #245, #246, #247, #248
- retriever (#226): #250, #251, #252, #253, #254, #255, #256
- LLM abuse surface (#228): #261, #262, #263
- Data integrity and recovery (#230): #264, #265, #266
- CI workflows (#224, finalized here): #268
- Dependency supply chain: #241
- Stacker (#227) FINDING-S1 (High `{@html}` XSS): private report, not a public issue (publicly filing an unpatched High XSS on a public repository would itself disclose a live vulnerability); recorded redacted in `docs/security/stacker-packages-audit.md`. Medium/Low stacker findings (FINDING-S2 through S6) are recorded in that document.

## Action items owned by the maintainer

- Open a GitHub private security advisory for stacker FINDING-S1 (High `{@html}` XSS) and route the exploit detail to `security@backchain.ai`.
- Triage the open Dependabot alert backlog alongside #241.

## Disposition

Success criteria 1, 2, 4, and 5 are met. Criterion 3 is met for 447 of 466 files, with the 19-file `services/biowriter/` gap deferred to #267 and documented here (secret-scan clean). Epic #222 closes on the merge of this reconciliation; #267 carries the residual biowriter coverage.
