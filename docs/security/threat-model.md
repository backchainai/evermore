# Evermore Threat Model

Committed as part of epic #222 (audit every file and workflow against a threat model), first
child #224 (harden CI workflows and repo controls). This document is the threat model that
epic's per-module sweeps and reconciliation are evaluated against; it is not module-specific.

The repository is public. Four FastAPI/SvelteKit modules plus shared packages make up the
tracked tree. CI already SHA-pins third-party actions, sets per-workflow `permissions:` blocks,
and handles branch-name injection deliberately in `deploy.yml`; this document does not assume
that posture is sufficient, it states what it is defending and what remains open.

## Assets, ranked

1. Animal records and generated adoption content (integrity): the data an adopter reads and
   acts on. Silent corruption or defacement here reaches the public directly.
2. Staff and adopter PII (confidentiality).
3. LLM gateway credentials and spend (Anthropic/OpenAI API keys, Cloudflare AI Gateway).
4. Shelter-system session credentials (the SMS integration Evermore rides on top of).
5. Database service keys (Supabase service-role keys, Postgres credentials).
6. CI secrets and deploy tokens (Cloudflare API tokens, `CLAUDE_CODE_OAUTH_TOKEN`).
7. Repository integrity itself (history, branch protection, workflow files).

## Actors

- **Anonymous internet user**: the repo and its issues are public; anyone can open an issue,
  comment, or open a PR from a fork without authentication.
- **Unauthenticated web client**: any request that reaches a public-facing endpoint before
  Supabase Auth JWT validation runs.
- **Authenticated staff user**: a shelter volunteer or employee with valid session credentials;
  assumed non-malicious but not infallible (careless, phished, or a compromised device).
- **Hostile content inside ingested shelter-system data**: the SMS record Evermore ingests is
  not written by Evermore and is not trusted input. A field (an animal's notes, a behavior log)
  can carry a prompt-injection payload that reaches an LLM prompt with no human review step in
  between. Data is an actor here, not just a resource.
- **Fork-PR contributor**: anyone who opens a pull request from a fork. Fork PRs run with
  reduced `GITHUB_TOKEN` permissions and no repository secrets by default, but agent workflows
  (`claude.yml`, `claude-code-review.yml`) that trigger on PR or comment events still execute
  with whatever token and permissions the workflow grants the job, which is the surface this
  model treats as adversarial.

## Priority threats

1. **LLM prompt injection**: ingested or retrieved content is untrusted input to every prompt
   that consumes it; injection can steer generation, exfiltrate context, or poison outputs.
2. **LLM repurposing**: injection or unauthenticated access that turns the app's model calls
   into free compute for unrelated workloads (stolen inference, denial-of-wallet).
3. **Ransomware / destructive compromise**: what an attacker with write credentials can destroy,
   and whether recovery (backups, point-in-time recovery, versioning) actually restores it.
4. **Data-mutation attacks**: silent corruption of animal records or generated content that
   propagates to adopters before anyone notices.
5. **Defacement / troll mutation**: low-sophistication malicious edits; the question is
   detectability and rollback, not just prevention.
6. **Resource takeover for proxying**: SSRF and egress abuse that turn the services into
   infrastructure for attacks on third parties.

## Baseline threats

- Secret and credential exposure (repository, git history, CI logs).
- Cross-tenant data leakage: enforced at the database layer (Postgres RLS), not just
  application-level filters, since an application bug should not be the only barrier between
  one shelter's data and another's.
- CI/CD compromise: workflow injection, fork-PR secret exposure, agent-workflow abuse.
- Dependency supply chain: unpinned actions, unpatched transitive dependencies.

## Severity: exploitability times asset

| Severity | Meaning |
|---|---|
| Critical | Remotely exploitable now, against a top-ranked asset |
| High | Exploitable with modest preconditions, or a critical asset behind one failed layer |
| Medium | Requires a privileged position or chained failures; real but not imminent |
| Low | Hardening gap, defense-in-depth, or hygiene |

A missing defense layer is a finding even when the front layer currently holds: severity rates
the exploitability of the gap, not whether it has been exploited yet.

## Coverage method

Every tracked file gets a class, a depth, and a verdict, recorded in
`docs/security/coverage-ledger.md`. Sweep depth follows class:

| Class | Depth |
|---|---|
| security-critical | line-by-line adversarial read |
| boundary-adjacent | trust-review (what does this file trust, and why) |
| config-IaC | full read |
| inert | secret scan plus a claim check |

"Inert, secret-scanned only" is a legitimate ledger entry: the honesty is in writing it down,
not in over-reading files that carry no security-relevant logic. Each per-module audit (#225
petdata, #226 retriever, #227 stacker and packages) appends its slice to the same ledger file
so the epic's union check stays one document; #228 (LLM abuse surface) and #230 (data integrity
and recovery) close last and reconcile every row in this threat model against a verified control
or an open finding.

## Public-repo disclosure discipline

This repository is public. Findings filed against this threat model (as GitHub issues, labeled
`security`) name actor, path, asset, and severity, but never carry directly exploitable detail:
no working injection strings, no live endpoint paths, no credential locations. That detail goes
to the private channel named in `SECURITY.md`, security@backchain.ai. A public finding carries a
redacted reference to the private report instead of the exploit content itself.

## Related decisions

- `SECURITY.md`: the disclosure channel and scope for this repository.
- ADR `0007-authentication-strategy.md`: the original JWT authentication scheme (superseded by
  ADR `0030-per-service-supabase-projects.md`, the current per-service Supabase Auth model).
- ADR `0009-content-safety.md`: input/output moderation and pattern-based prompt-injection
  defense in `retriever`, the first line of defense against threat 1 above.
- ADR `0015-prompt-injection-defense.md`: the prompt-injection defense record this threat model's
  threat 1 generalizes from a single module (`retriever`) to every ingestion path in the system,
  including shelter-system data ingested by `petdata`.
