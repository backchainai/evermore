# LLM Abuse Surface Assessment

**Audit type:** point-in-time, static (read-only). **Date:** 2026-07-05. **Issue:** [#228](https://github.com/backchainai/evermore/issues/228), part of epic #222. **Threats covered:** 1 (prompt injection), 2 (repurposing / denial-of-wallet), 6 (resource proxying). **Method:** `docs/security/threat-model.md`.

> **Redaction notice.** This is the public, redacted map. Every finding names actor, path, asset, and severity. Working injection payloads, live-endpoint detail, and credential locations/rotation runbooks route to the private channel: **security@backchain.ai** (see `SECURITY.md`). Nothing here is silently fixed; the epic files findings, it does not patch.

## Scope and reconciliation

The product's LLM surface is a single spine: untrusted content enters at four sources, converges on one prompt-composition point in `services/retriever`, is billed against one gateway credential, and fans out to output sinks. `services/petdata` ingests external shelter data but makes **no** model calls (no `openai`/`anthropic` import in `services/petdata/src`); its outbound egress is a threat-6 concern only, already filed as #245/#248. `apps/stacker` renders model output.

Output sinks already assessed by the sibling sweeps are cited here, not re-litigated (see "Reconciled, not re-filed" below). This document adds only the cross-cutting synthesis plus three new High findings (L1-L3).

```
SOURCES (untrusted)                 PROMPT COMPOSITION        MODEL           SINKS
1. user question ---------+
2. retrieved chunks ------+         RAGService.ask()          one gateway     a. stacker {@html}  (FINDING-S1)
   (corpus docs) ---------+-------> build_rag_prompt() ------> token, all ---> b. messages table -> replay (#256)
3. conversation history --+         (system + user + history)  providers       c. semantic cache -> re-serve (#250)
4. public @claude text ---+                                    (BYOK)          d. agent tools (read-only, workflow)
```

## A. End-to-end data-flow (AC1)

The `POST /api/v1/ask` chain, annotated with the control at each hop. Of nine hops, only the auth hop holds unconditionally; hops 3, 4, 5, 7, 8, 9 have an absent or no-op control.

| Hop | Location (file:line) | Untrusted data | Control at hop | Fail mode |
|---|---|---|---|---|
| 1. Ingress | `services/retriever/src/retriever/modules/rag/routes.py:68` (`POST /api/v1/ask`) | user `question` (<=2000 chars) | `require_auth` + router `require_subscription("retriever")` (`main.py:185`) | Closed (401/403 without JWT+claim) |
| 2. Input safety | `services/retriever/src/retriever/modules/rag/service.py:167` `check_input()` | question | regex `PromptInjectionDetector` (`infrastructure/safety/detector.py:16-47`, question-only) + moderation | Detector closed on match but enumerated/bypassable; default `GuardrailsModerator` is an app-layer no-op (`infrastructure/safety/moderation.py:151-161`, `rag/dependencies.py:135`) |
| 3. History load | `services/retriever/src/retriever/modules/rag/routes.py:91` `get_recent_messages()` | prior turns incl. prior model output | none (replayed verbatim, `service.py:232-233,268-269`) | **Open (#256)** |
| 4. Retrieval | `services/retriever/src/retriever/modules/rag/service.py:211,220` | corpus chunk content | tenant_id filter only; no injection/moderation screen | **Open (#250)** |
| 5. Prompt build | `services/retriever/src/retriever/modules/rag/prompts.py:54-72` `build_rag_prompt()` | chunks embedded into the **system** role at `{context}` (`prompts.py:36,69`) | none | **Open (#250)** |
| 6. Model call | `service.py:271,276` -> `infrastructure/llm/openai_compat.py:172,326` | full prompt | single gateway token (`gateway_client.py:48`); no tool/function-calling in `services/retriever/src` | Output is text-only; cannot execute in-service |
| 7. Output safety | `service.py:286` `check_hallucination()` only | model output | grounding heuristic (advisory); `check_output()` moderation exists but has **no caller** (`infrastructure/safety/service.py:93`, #251) | **Open** for output moderation |
| 8. Persist | `routes.py:118,124` `save_message()` | model output stored | none | Replays at hop 3 next turn (#256) |
| 9. Render | `apps/stacker/src/lib/modules/retriever/components/ChatMessage.svelte:35` `{@html marked.parse(content)}` | model output | none - `marked` output unsanitized | **Open** -> XSS (FINDING-S1, High; reconciled to `stacker-packages-audit.md`, not re-filed) |

The load-bearing cross-module chain is a poisoned corpus chunk (hop 4/5) reaching XSS in a staff browser (hop 9); both ends are already filed (#250 injection, FINDING-S1 sink).

## B. Injection map (AC2)

Every path where untrusted content reaches a model prompt.

| Untrusted path | Source (file:line) | Control | Fail-mode | Can steer downstream? |
|---|---|---|---|---|
| User question -> prompt (user role) | `rag/routes.py:33,68`; `service.py:167` | regex detector (`detector.py:16-107`) + moderation (default no-op) | Detector closed on match (bypassable regex list); app-layer moderation open (`moderation.py:151`; OpenAI backend fails open on error `moderation.py:100-127`) | Only via sinks (no tool-use); text output |
| Retrieved corpus chunk -> **system** prompt | `rag/prompts.py:36,69`; `service.py:257` | **none** (verbatim embed) - owned by **#250** | **Open** | Yes: steers generation; chains to `{@html}` XSS (FINDING-S1) |
| Conversation history (incl. prior model output) -> prompt | `messages/repos.py:75`; `rag/routes.py:91`; `service.py:232-233,268-269` | **none** (no re-screen on replay) - owned by **#256** | **Open** | Yes: self-reinforcing across turns |
| Semantic-cache hit -> served answer | `service.py:189-204`; `infrastructure/cache/pg_cache.py` | post-generation answer re-served without re-screening (noted in #250 path map) | **Open** | Re-serves prior (possibly poisoned) output |
| Public issue/comment/PR body (`@claude`) -> agent model | `.github/workflows/claude.yml:16-19`; `claude-code-review.yml:4-5` | trigger gated on `@claude` literal (anyone can type it); job `permissions:` read-only (`claude.yml:21-26`) | Trigger open to any anonymous actor; permission scope closed for repo mutation | Agent has repo **read** + tools but **no write**; steering bounded by read-only token. Denial-of-wallet only -> **L3** |
| Ingested SMS field -> petdata -> (future) corpus | `services/petdata/src/petdata/modules/api/` | petdata makes no model call; reaches a prompt only once indexed into retriever corpus | n/a today (no petdata->retriever wire in-repo) | Latent: becomes the "corpus chunk" row once wired |

## C. Model-call entry-point inventory (AC3)

Every entry point that triggers a model call.

| Entry point (file:line) | Actor / authn | Rate / quota / spend limit | Abuse verdict + severity |
|---|---|---|---|
| `POST /api/v1/ask` -> chat completion(s) (`rag/routes.py:68` -> `service.py:271,276`) | authenticated staff, `require_auth` + `require_subscription("retriever")` (`main.py:185`) | **None** - no limiter middleware in `main.py`; ADR-0012 rate-limiting documented but unwired | Denial-of-wallet: one valid subscribed token drives unbounded paid inference. Critical asset behind one missing layer. **High -> L1** |
| Embed-query on ask path (`service.py:186` -> embeddings via gateway) | same as `/ask` | none | Same billing surface as L1; folded into **L1** |
| `POST /api/v1/documents/upload` -> `embed_batch` (`documents/routes.py`) | `require_admin` + subscription | none; 20 MB upload cap only; `docling_max_pages` defined but unenforced (#253) | Admin-gated paid inference. **Medium** (privileged actor); page-cap gap already #253, not re-filed |
| Moderation `/moderations` call (only if `moderation_backend="openai_api"`) (`rag/dependencies.py:129-131`) | rides `/ask` auth | none | Default is `guardrails` (no call); opt-in adds a per-request billed call. **Low** |
| Agent workflow `claude.yml` -> Anthropic inference on `CLAUDE_CODE_OAUTH_TOKEN` | **anonymous internet user** - issue/comment with `@claude` (`claude.yml:16-19`); runs with secrets | none (no allow-list of triggering actors) | Anonymous denial-of-wallet: burns Anthropic quota on demand; repo mutation blocked (read-only `permissions:`). **High -> L3** |
| Agent workflow `claude-code-review.yml` -> inference per PR | fork-PR contributor; `pull_request` withholds secrets from fork PRs (GitHub default) -> action no-ops | none | Denial-of-wallet mitigated by secret-withholding. **Low** (platform behavior, not in-repo code) |

## D. Outbound-request inventory (AC4)

Where the services make outbound requests.

| Call site (file:line) | Destination trust | SSRF / egress verdict + severity |
|---|---|---|
| Retriever -> LLM gateway, all model calls (`infrastructure/llm/gateway_client.py:52-57`; `openai_compat.py:172,326`; `infrastructure/embeddings/openai.py`; `infrastructure/safety/moderation.py:69`) | `settings.llm_gateway_base_url` - config-pinned Cloudflare gateway (`config.py:187-214`); **not** request-controlled | No SSRF: URL derives from config, never request input. Single known host. **Low / clean** |
| Retriever document ingest (`rag/loader.py`, `rag/docling_processor.py`) | processes uploaded bytes; no URL fetch | No fetch-by-URL surface. **Clean** |
| Retriever R2 storage (`infrastructure/storage/r2.py`) | dead code, not wired into any live handler | No live egress. **Clean (dead code)** |
| petdata -> SMS host (`services/petdata/src/petdata/modules/api/client.py:50-56`) | `httpx.Client(follow_redirects=True, headers=<static Cookie>)` - SMS base URL config-pinned, but redirects follow to arbitrary hosts and resend the session cookie | SSRF/egress + credential leak on redirect; relay risk. Already **#245** (redirect+cookie) and **#248** (no size cap). **High** - reconciled, not re-filed |

**Net:** the retriever (the only model-calling service) has **no** attacker-reachable outbound-URL surface. The only live SSRF/egress finding in the spine is petdata's, already owned by #245/#248.

## E. Gateway-credential blast-radius & spend-monitoring (AC5)

Retriever authenticates to the LLM gateway with a **single static bearer token**, `settings.llm_gateway_token` (`config.py:73`), sent on `settings.llm_gateway_auth_header` (default `cf-aig-authorization`, `config.py:77`) by one shared client builder (`gateway_client.py:48-57`). That one token fronts **all** model traffic: chat (`openai_compat.py`), embeddings (`infrastructure/embeddings/openai.py`), and moderation (`infrastructure/safety/moderation.py`). Provider keys live inside the gateway (BYOK), so the token is the sole in-app secret gating paid inference.

**Blast radius of one leaked token:** unrestricted inference across every provider and model the gateway proxies, billed to the org, until the token is manually rotated. There is **no** per-service, per-scope, or per-model token; **no** in-repo per-key rate limit; **no** in-repo spend ceiling or budget-alert wiring. Langfuse (`observability/langfuse.py`) is observability only and `@observe()` no-ops without credentials (`main.py:153-157`); it is not a spend cap. Any gateway-side rate-limit or usage analytics is Cloudflare AI Gateway configuration, which a static repo audit cannot observe - recorded here as a **gap to verify**, not as a confirmed control.

Combined with L1 (no app-level rate limit on `/ask`), the spend asset sits behind exactly one secret and one auth check, with no app-layer ceiling on either. **Severity: High -> L2.** Token location and rotation runbook route to the private channel.

## F. Findings & recommended follow-on issues (AC6)

Three new **High** findings. Redacted bodies below name actor/path/asset/severity; exploit specifics route to security@backchain.ai. Per AC6, these are recorded here as the private-report record; **filing them as separate tracker issues is left to the operator.**

**L1 - Add rate/quota limit to the retriever `/ask` inference path (High).**
Actor: authenticated + subscribed staff user (or a compromised/phished staff token). Path: `POST /api/v1/ask` drives chat + embedding calls with no per-user or per-tenant throttle; `main.py` wires no limiter middleware and ADR-0012's rate-limiting is unimplemented. Asset: LLM gateway spend. The auth gating holds; the missing layer is throughput control. Recommendation: wire the ADR-0012 rate limit (per-user and per-tenant) ahead of the gateway call.

**L2 - Reduce LLM gateway-token blast radius and add spend monitoring (High).**
Actor: anyone who obtains the single gateway token (log leak, misconfig, compromised deploy env). Path: one static `llm_gateway_token` authenticates all chat/embeddings/moderation traffic, with no scoping and no in-repo spend ceiling or budget alert; gateway-side limits are unverifiable from code. Asset: gateway credentials + spend. Recommendation: per-service/scoped tokens, a spend ceiling with alerting, and a documented rotation path.

**L3 - Prevent anonymous denial-of-wallet via `claude.yml` agent workflow (High).**
Actor: anonymous internet user. Path: an issue/comment containing `@claude` triggers Anthropic inference on `CLAUDE_CODE_OAUTH_TOKEN` with no triggering-actor allow-list; repo mutation is blocked by the read-only `permissions:` block. Asset: Anthropic subscription quota. Injection-to-action is blunted by the read-only scope; the exposure is denial-of-wallet. #224 (agent-workflow hardening) is CLOSED, so this is recorded standalone rather than folded into it.

**No Critical finding.** The highest-exposure chain (corpus injection #250 -> `{@html}` XSS FINDING-S1) is two already-filed High findings behind an auth boundary, not a single remotely-exploitable critical-asset break.

**Reconciled, not re-filed** (cited from the sibling sweeps, counted once): #250 (retrieved/ingested content to system prompt), #251 (output moderation never invoked), #253 (docling page-cap unenforced), #255 (safety-rail disclosure), #256 (history replay), #245 (SMS cookie across redirects), #248 (SMS no size cap), and stacker FINDING-S1 (`{@html}` XSS) in `docs/security/stacker-packages-audit.md`.
