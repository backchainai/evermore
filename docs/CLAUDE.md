# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this directory is

`docs/` holds the **Evermore research corpus**: the evidence base behind the platform's content generation and behavior analysis. It is currently the only content under `docs/`, and it is reference material, not code.

**Do not commit source research papers.** The repository tracks our derived work only. Tier 1 source PDFs (`research/source-research/`, `research/reference-library/`) are third-party copyrighted material kept local-only and git-ignored; never commit them. Only Tier 2 `research/extractions/` (our distilled rules, each carrying citations to the underlying papers) is committed. Git history is the version-control safety net; get explicit user approval before deleting anything.

## The corpus map

Authoritative layout and per-file detail live in `research/README.md`; read it first. The corpus is organized by the role each artifact plays, on a two-tier model:

| Path | Tier | Feeds | Contents |
|---|---|---|---|
| `research/extractions/` | Tier 2 (compiled) | BioWriter generation and the lint rubric | Distilled rules, templates, the five-section kennel-card format |
| `research/source-research/` | Tier 1 (primary) | citable evidence base (RAG-indexable) | Peer-reviewed studies, grouped by domain (local-only, git-ignored) |
| `research/reference-library/` | Tier 1 (operational) | Retriever shelter-ops assistant | Handbooks, training, body-language, DPFL library (local-only, git-ignored) |

The two foundational kennel-card papers (Markowitz 2020; Kelling et al.) live in `research/source-research/adoption-advertising/`. The generation contract for the v1 kennel-card feature is `research/extractions/recommended-pet-biography-template-format.md`.

## Working conventions

- **Read-only content.** Do not edit the contents of corpus documents; this folder is curated and organized, not authored. Creating index or README files is fine.
- **Reading PDFs and DOCX:** use Docling (`docling --to md <file>`), not raw parsing. Sample large PDFs; do not read them end to end just to classify.
- **Renames** follow the file-naming standard (all lowercase, hyphens within fields, fields joined by underscores, no spaces or parentheses, target <=50 chars).
- **Commit only Tier 2 extractions.** Tier 1 source PDFs are git-ignored; never add them. Git history records structural changes (moves, renames), so no separate manifest is kept.

## Terminology

In Evermore, **"extraction" means retrieving existing data out of a shelter system** (a Pet Data module capability, not yet built). The `research/extractions/` folder, despite its name, holds **distilled** Tier-2 research rules. Do not conflate the two.

## Known state

- The two adoption-advertising papers are well distilled into Tier 2. The papers in `source-research/behavior-and-welfare/` and `source-research/shelter-outcomes/` are only partially distilled and have no Tier-2 rubric yet; distilling them is backlog for the behavior-analysis module.
- `research/.daedalus/` is stray pipeline config, not part of the corpus. Leave it.
