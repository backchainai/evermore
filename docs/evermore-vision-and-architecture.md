# Evermore: Vision and Architecture (v0.1)

Status: draft, 2026-06-19. Living document. Source of truth for what Evermore is and how it is shaped; the GitHub backlog and the repo scaffold derive from this.

## What Evermore is

Evermore is an AI platform for nonprofit animal shelters. It ingests each shelter's animal data from whatever systems they already use, runs AI modules that produce adoption marketing and answer staff questions, and over time distributes and measures campaigns. Shelters subscribe to the modules they need through one authenticated portal.

The architecture is industry-neutral. The initial design partner is Friends of Homeless Animals (FOHA), an animal shelter served pro bono. The name comes from a short story written by the project owner.

## North Star

Maximize **healthy, safe, and permanent adoptions** for homeless animals. Every module is measured against that single outcome. The working proxy metric is **time-online** (days to adoption), which is the primary outcome variable in the adoption-advertising research and the natural trigger for outcome-based pricing.

## Who it serves

Nonprofit shelters: chronically under-funded, skeleton crews, volunteer-heavy, and a patchwork of data systems (Shelterluv and peers, bespoke in-house apps, or plain PDF / HTML / Word / text exports, with an API or database only if you are lucky). The wedge: shelters are starved for labor, so any task AI can absorb frees a human for the work that actually places animals.

## Positioning

Evermore is **not** a shelter management system and does not replace Shelterluv. It is the **AI intelligence layer that rides on top of whatever system a shelter already uses.** Incumbent systems are rigid, built by small non-specialist teams, with weak or no data-extraction APIs and almost no real AI. That gap is the reason to exist: Evermore brings advanced tooling the incumbents cannot build, and meets the data wherever it lives (even a PDF export).

## Business model

- **Pro bono tier:** rate-limited and content-limited free access. Mission-first, keeps costs bounded.
- **Outcome-aligned pricing:** a few dollars per *successful adoption* to offset costs. Revenue is tied to the north star; a shelter pays only when an animal goes home. This is also a trust and marketing story: no shelter gambles budget on software that might not work.

## The data spine (core vocabulary)

The platform is a pipeline of named objects. These names are settled; do not overload them.

| Object | What it is | Provenance | Versioned | Owner |
|---|---|---|---|---|
| **Source documents** | Raw inputs: Shelterluv kennel-card export, FOHA-app observations, PDFs, HTML, Word | n/a | no | external |
| **Animal Record** | Canonical normalized data for one animal (demographics, history, behavior observations, medical) | n/a | tracked | Pet Data |
| **Package** | A curated, named selection of evidence assembled by a human (now) or the LLM (later), the generation-ready subset of the Animal Record | **yes**, per item `{source document, location, category}` | **yes** | Pet Data |
| **Template** | The structure and rules for a collateral type (the five-section kennel card, a Facebook post, an adoption ad) | n/a | n/a | BioWriter |
| **Composition** | The generated and human-edited piece = Package + Template + customizations. The living source of truth inside the platform. | **yes**, each unit links back to its package items and the research rule it satisfies | **yes, automatically** | BioWriter |
| **Export** | A flat file rendered from a Composition (PDF, DOCX, Drive). For manual transfer into the shelter system. | **no** (flattened) | a snapshot of a Composition version | BioWriter |

Flow: `Sources -> Animal Record -> Package -> Composition -> Export`. Provenance lives in Package and Composition and drops at Export. Each arrow is a capability; **the Package is the seam between Pet Data and BioWriter** and decouples them.

## Modules

| Module | Repo (post-rename) | Role |
|---|---|---|
| **Stacker** | `apps/stacker` | The portal substrate: single sign-on, subscription/entitlement gating, module registry. Shelters see only what they subscribe to. |
| **Pet Data** | `services/petdata` (was `petbio`) | The data plane: extensible per-source connectors, the canonical Animal Record, behavior and trend analysis, and the Package builder. |
| **BioWriter** | `services/biowriter` (new) | The generation plane: kennel cards, social posts, and ads from Package + Template + research; the live lint/score editor; Composition versioning and Export. |
| **Retriever** | `services/retriever` | Dual role: an end-user module (RAG chat over shelter ops and policy docs) **and** an internal platform service (indexes the research corpus so BioWriter can cite the paper a recommendation came from). |
| **Behavior & Trend Analysis** | within `services/petdata` | Time-decay weighting of longitudinal volunteer observations into per-animal trends. Lets staff get ahead of behavior changes and makes every Composition more accurate. |
| **Social Distribution & Analytics** | future | Integrations (for example Hootsuite) to schedule cross-platform campaigns, plus per-animal engagement monitoring and content QA (errors, omissions, stale listings). |

## The wedge: the research-backed kennel card

The first thing put in front of a shelter is the **kennel card writer**. Why it is the highest-leverage artifact on the platform: a volunteer writes the kennel card, it is entered in Shelterluv, Shelterluv federates it to Petfinder and Adopt-a-Pet, and that text becomes the animal's public listing on the sites adopters actually search. The photos come from the shelter system; the words come straight from the kennel card. An untrained volunteer's phrasing is therefore the top of the adoption funnel, published nationally.

Two capabilities, both grounded in the research rubric:

- **Generate:** produce a compliant kennel card from the animal's Package and the five-section template.
- **Lint and score:** grade a human-written draft against the rubric in the editor in real time. Half the rules are mechanically detectable (social descriptors, first-person dog voice, paragraph vs bullets, 200 to 280 word target, pronoun-over-noun).

The pitch, in one provocative sentence: *your volunteers are lovingly writing kennel cards in the style the research shows gets animals adopted slower, and we fix that with the evidence.*

## Research corpus (two-tier)

Lives in `docs/research/` (see `docs/research/README.md`). The evidence is the platform's credibility and a moat that a generic LLM wrapper cannot copy.

- **Tier 1, source-research:** primary peer-reviewed studies, indexable by a Retriever collection for citation. The kennel-card backbone is Markowitz (2020, 184,805 Petfinder profiles) and Kelling et al.
- **Tier 2, distilled rules:** compiled summaries, templates, and rubrics that drive generation directly. The kennel-card template and rubric already exist (currently in `docs/research/extractions/`, to be renamed `distilled/`).
- **Known coverage gap:** the behavior-and-welfare and shelter-outcomes papers are only partially distilled; distilling them is backlog behind the Behavior & Trend Analysis module.
- **Author relationships:** courting the researchers is a named strategic asset; it hardens "defensible" into "endorsed," and outcome data flowing back to them closes the flywheel.

## Design principles

- **Human-in-the-loop, always.** AI drafts and critiques; people decide. The UI is built review-first so automation can slot in behind it as trust grows; every human accept/reject is a labeled example that trains the auto-selector.
- **Evidence-backed and traceable.** Generation is grounded in research and, over time, in measured outcomes. Provenance persists through the Composition (hover a sentence, see the evidence and the rule behind it).
- **Source-agnostic.** The platform never assumes a shelter's stack; connectors are fungible.
- **Workforce multiplier.** Success is measured in staff hours returned and animals placed, not features shipped.

## The flywheel

Engagement and adoption-outcome data (from the social/analytics module and time-online tracking) feed back to refine what "successful collateral" means for these animals at this shelter. Evermore stops guessing from papers alone and starts learning from results. The longer a shelter runs it, the better its marketing gets.

## Related documents

- Decisions: `adr/0001-monorepo-structure.md`, `adr/0002-github-native-project-management.md`, `adr/0003-standardized-tech-stack.md`
- Execution: `plans/repo-restructure-and-rename.md`
- Research corpus map: `research/README.md`
