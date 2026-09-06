# ADR 0037: Hosted-only execution: nothing runs on an operator's machine

- Status: accepted
- Date: 2026-09-06
- Deciders: project owner
- Relates to: ADR 0029 (host all compute on Cloudflare), ADR 0038 (proposed engagement collector)

## Context

Parts of the working pipeline ran on the owner's workstation. That is acceptable for exploration and not acceptable for anything volunteers or shelter staff depend on: the pipeline stops when the laptop sleeps, live credentials sit on a personal machine, and nobody else can operate or observe it.

ADR 0029 already put all Evermore compute on Cloudflare. What it did not do was state the negative constraint, and the workstation pieces predate it.

## Decision

Nothing runs on the owner's laptop.

- Every scheduled or long-running component runs in the hosted environment: Cloudflare, Supabase, or a hosted third-party service.
- No pipeline step may depend on an operator's machine being awake, connected, or configured.

## Consequences

- The design in which collectors stay private and feed Evermore over an authenticated ingest endpoint with a service token is retired. That design existed to bridge a workstation to the platform, and with the collector hosted there is nothing to bridge.
- The ingest endpoint itself drops out of the plan. This is a consequence of the decision above, not a separately approved decision: with the collector hosted there is no second producer for that seam. If a genuinely external producer appears later, the seam can be reconsidered on its own merits.
- All credentials move into hosted secret stores (Cloudflare Worker secrets, Supabase project settings, or the hosted service's own secret store). No pipeline credential lives in a local `.env` file or an operator's keychain.
- The constraint binds future module designs, not only the collector. Any design that needs a periodic job needs a hosted scheduler (a Cron Trigger, a hosted queue, or a scheduled hosted job) as part of the design, rather than deferring it to an operator's crontab.
- Local development is unaffected. Running a service on a laptop in order to develop it is not a pipeline step; the constraint is about what production depends on.
- The immediate casualty is the existing workstation engagement collector, which is why ADR 0038 proposes a hosted replacement. That collector is not committed to this repo, so this ADR retires a working local tool rather than deleting repo code.

## Alternatives considered

- **Keep the workstation collector and bridge it in over an authenticated ingest endpoint with a service token.** Rejected: it makes an operator's machine a production dependency and keeps a live third-party credential on a personal device. This is the status quo the decision replaces.
- **Accept manual weekly operation, with an operator running the collector by hand.** Rejected: a weekly human step is the failure mode being removed, not a mitigation of it.
