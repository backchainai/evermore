---
adr: 019
title: Apache-2.0 for all repositories
status: accepted  # proposed | accepted | deprecated | superseded
date: 2026-06-09
tags: [licensing, open-source, governance]
supersedes: null
superseded_by: null
related: []
---

# 019: Apache-2.0 for all repositories

## Status

Accepted

## Context

Retriever shipped under AGPL-3.0-or-later, following a two-license posture that
applied AGPL to network-deployed services and Apache-2.0 to locally-running
tools. Chris Krough and Backchain have since committed to a single open-source
license for every repository, regardless of artifact class. Attribution is the
return on open source: wide adoption attracts employers (Chris Krough, personal
brand) and business (Backchain). AGPL's network copyleft chilled exactly the
adoption the projects want and protected nothing Backchain monetizes, since
there is no commercial relicense to sell.

A unilateral relicense is valid only when the relicensing party holds copyright
on all the code. The contributor check (`git shortlog -sne --all`) showed every
human commit authored by Chris Krough, with the only other author being the
`semantic-release` CI bot. Backchain LLC holds copyright on all code, so the
flip is clean.

## Decision

Relicense Retriever from AGPL-3.0-or-later to Apache-2.0. This aligns Retriever
with a practice-wide standard: every Chris Krough / Backchain repository ships
true, OSI-compliant open source under Apache-2.0, whether it is a local CLI, a
library, a Claude Code plugin or skill, an eval framework, or a network service.

Copyright remains Backchain LLC. Contributors retain copyright on their
contributions under Apache-2.0. There is no AGPL, no copyleft, no commercial
license, no dual licensing, and no CLA or DCO. The public license is the license.

Attribution is dual by design: legal and copyright attribution to Backchain LLC
(LICENSE, NOTICE, per-file SPDX headers); author identity to Chris Krough
(package manifest authors and maintainers, CITATION.cff, README About block).

## Alternatives Considered

- **Keep AGPL-3.0-or-later.** Rejected. Network copyleft deters adoption and the
  enterprise use that drives employer and business interest, while protecting no
  revenue stream Backchain actually has.
- **Two-license split (Apache for tools, AGPL for services).** The prior posture.
  Rejected as adding friction and contributor confusion for no benefit; the
  license choice should follow the open-source goal, not artifact class.
- **Dual licensing or a commercial relicense option.** Rejected. There is no
  commercial license to sell; the offering is the public license.

## Consequences

- Downstream users, including commercial and SaaS operators, can adopt and deploy
  Retriever without copyleft obligations. This maximizes adoption and the
  attribution that travels with it.
- The professional-workspace rule `.claude/rules/repo-licensing.md` still
  describes the superseded two-license split; that rule is updated separately
  (tracked in prof-qy8r).
- New source files carry an Apache-2.0 SPDX header; existing `backend/src` files
  received the header in a one-time sweep.
- GitHub re-detects the repository license as Apache-2.0 once the LICENSE swap
  lands on `main`.
