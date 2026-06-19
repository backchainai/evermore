# Evermore Research Corpus

The evidence base behind Evermore's generation and analysis. It is organized by the role each artifact plays in the platform, not by where it came from.

Two tiers feed the **BioWriter** module (kennel cards and adoption profiles), and a broader reference set backs **behavior analysis** and the **Retriever** shelter-operations assistant.

## Layout

### `extractions/` — Tier 2: compiled, purpose-built generation inputs
Distilled findings and templates derived from the primary research, written to drive LLM generation directly. These are the rules BioWriter applies and grades against.

- `key-adoption-profile-research-findings-summary.md` — the central thesis (central-route persuasion), effect sizes, and the Top 10 Do's / Don'ts.
- `recommended-pet-biography-template-format.md` — the five-section kennel-card template, word-count target, style and disclosure rules, and a Sally-based worked example. This is the generation contract for the v1 kennel-card wedge.
- `recommended-adoption-profile-pictures.md` — the photo checklist (a rubric-shaped, non-text capability for later).
- `shelter-dog-adoption-success-rates.md` — success-factor overview (foster care, behavioral prep, advocacy).

### `source-research/` — Tier 1: primary peer-reviewed sources (searchable, citable)
The studies behind the extractions. Indexable by a Retriever collection so BioWriter can cite the paper a recommendation came from.

- `adoption-advertising/` — directly backs the kennel-card wedge:
  - `putting-your-best-pet-forward_markowitz_2020.pdf` (Markowitz 2020; 184,805 Petfinder profiles)
  - `constructing-dog-adoption-advertisements_kelling.pdf` (Kelling et al.; 561-participant study)
- `shelter-outcomes/` — outcome and live-release research (grounds the time-to-adoption metric).
- `behavior-and-welfare/` — shelter-dog behavior and welfare research (grounds behavioral descriptions and the behavior-analysis module).

### `reference-library/` — operational and interpretive knowledge (Retriever ops corpus)
How-to material for shelter staff and volunteers, not generation inputs. Suited to the Retriever knowledge-assistant use case.

- `handbooks/` — volunteer and foster-care handbooks/manuals.
- `training/` — training guides and protocols.
- `dog-training-archive/` — foundational training references (learning theory, Karen Pryor, puppy socialization).
- `body-language/` — canine body-language and communication references (includes infographic images).
- `credentialing/` — evaluator/credentialing guides.
- `dpfl-learning-library/` — Dog Playing for Life playgroup and handling library (cheat sheets, playgroup ops, shelter recommendations, presentation slides).

## Curation notes

- This corpus was not pre-curated. Off-use-case material (`.mp4` videos, DPFL impact/marketing reports and infographics, and Spanish-language cheat-sheet translations) was removed from the active corpus.
- Existing per-folder PDFs already followed a lowercase-hyphen naming convention and were preserved. Files with spaces or special characters (the two adoption-advertising sources and the training archive) were renamed to the convention.
- Tooling: file content was identified from the Tier-2 summaries and corpus taxonomy. `drover` (LLM auto-naming) was unavailable in this environment (no local Ollama backend); names were applied by hand to the same convention.
