# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this directory is

`docs/` holds everything under version control that is not application code: the living architecture and product docs, the append-only decision record, the research corpus, and per-module test-quality audits. Four kinds of content live here, each with its own rules below.

## Living docs

The `.md` files directly under `docs/` (`architecture.md`, `evermore-vision-and-architecture.md`, `auth-flow.md`, `subscriptions.md`, `module-template.md`, `local-development.md`, `cloudflare-ai-gateway-setup.md`) are living documents: edit them in place when the thing they describe changes. Each fact has one owning doc; every other mention of that fact elsewhere in the repo is a one-line signpost back to the owner, not a restatement. `docs/architecture.md` owns system topology and cross-cutting contracts (auth, subscriptions, observability); `docs/evermore-vision-and-architecture.md` owns product vision and the data model; the rest own the area named in their title.

## `adr/` - decisions

Architecture Decision Records are append-only. A decision is recorded once, at the next sequential number, and never rewritten in place. When a later decision changes course, it supersedes the earlier record: the earlier file stays, gets marked superseded (naming the successor), and is not deleted or edited to match the new state. `docs/adr/README.md` is the index (old-to-new numbering, current status per record); read it before adding or amending an ADR, and add new records by appending, not by editing history.

## `research/` - the research corpus

The evidence base behind BioWriter's generation and Retriever's shelter-ops assistant. Authoritative layout and per-file detail live in `research/README.md`; read it first. The corpus is organized by the role each artifact plays, on a two-tier model:

| Path | Tier | Feeds | Contents |
|---|---|---|---|
| `research/distilled/` | Tier 2 (compiled) | BioWriter generation and the lint rubric | Distilled rules, templates, the five-section kennel-card format |
| `research/source-research/` | Tier 1 (primary) | citable evidence base (RAG-indexable) | Peer-reviewed studies, grouped by domain (local-only, git-ignored) |
| `research/reference-library/` | Tier 1 (operational) | Retriever shelter-ops assistant | Handbooks, training, body-language, DPFL library (local-only, git-ignored) |

The two foundational kennel-card papers (Markowitz 2020; Kelling et al.) live in `research/source-research/adoption-advertising/`. The generation contract for the v1 kennel-card feature is `research/distilled/recommended-pet-biography-template-format.md`.

**Do not commit source research papers.** The repository tracks our derived work only. Tier 1 source PDFs (`research/source-research/`, `research/reference-library/`) are third-party copyrighted material kept local-only and git-ignored; never commit them. Only Tier 2 `research/distilled/` (our distilled rules, each carrying citations to the underlying papers) is committed. Git history is the version-control safety net; get explicit user approval before deleting anything.

Working conventions for the corpus:

- **Read-only content.** Do not edit the contents of corpus documents; this folder is curated and organized, not authored. Creating index or README files is fine.
- **Reading PDFs and DOCX:** use Docling (`docling --to md <file>`), not raw parsing. Sample large PDFs; do not read them end to end just to classify.
- **Renames** follow the file-naming standard (all lowercase, hyphens within fields, fields joined by underscores, no spaces or parentheses, target <=50 chars).
- **Commit only Tier 2 distilled rules.** Tier 1 source PDFs are git-ignored; never add them. Git history records structural changes (moves, renames), so no separate manifest is kept.

Terminology: in Evermore, "extraction" means retrieving existing data out of a shelter system (a Pet Data module capability), distinct from the distilled Tier-2 research rules in `research/distilled/`. Do not conflate the two.

Known state: the two adoption-advertising papers are well distilled into Tier 2. The papers in `source-research/behavior-and-welfare/` and `source-research/shelter-outcomes/` are only partially distilled and have no Tier-2 rubric yet; distilling them is backlog for the behavior-analysis module. `research/.daedalus/` is stray pipeline config, not part of the corpus; leave it.

## `testing/` - test-quality audits

Point-in-time audits of test-suite effectiveness and mutation-testing coverage, one per module plus a tracking summary (`petdata-test-audit.md`, `retriever-test-effectiveness-audit.md`, `stacker-test-audit.md`, `mutation-tracking.md`). These are dated snapshots, not living docs: add a new audit rather than editing an old one in place when a module is re-audited.

## What is not here

No plans directory. Planning documents are not tracked under `docs/`; work breakdown lives in GitHub Issues and Projects (ADR `0023-github-native-project-management.md`).
