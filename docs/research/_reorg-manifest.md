# Research Corpus Reorganization Manifest

This file logs every move and rename applied during the reorganization of
`docs/research/`. The corpus is **not** under version control (no `.git` at the
`evermore/` root), so this manifest is the only record by which a human can
reverse a change. Nothing was deleted: items judged off-use-case were moved to
`_parked/`, which preserves their original sub-paths.

- **Old path** is relative to `docs/research/` before the reorg.
- **New path** is relative to `docs/research/` after the reorg.
- A move into `_parked/` preserves the file's original relative sub-path under
  `_parked/`, so reversal is a straight move back to the old path.

## Top-level structure change

| Old layout (root + topical folders) | New layout |
|---|---|
| root `.md` files, root `.pdf` papers, and flat topical folders (`handbooks`, `credentialing`, `shelter-outcomes`, `training`, `behavior-and-welfare`, `dpfl-learning-library`, `dog-training-document-archive`, `body-language`) | `extractions/` (Tier 2 compiled), `source-research/` (Tier 1 peer-reviewed, by domain), `reference-library/` (Tier 1 operational/interpretive, by domain), `_parked/` (off-use-case, recoverable) |

## Renames (file name changed, content unchanged)

### reference-library/dog-training-archive/

| Old path | New path |
|---|---|
| `dog-training-document-archive/dog training learning theory classical and operant conditioning guide.pdf` | `reference-library/dog-training-archive/learning-theory-classical-operant-conditioning.pdf` |
| `dog-training-document-archive/karen pryor ten principles of behavior shaping clicker training.pdf` | `reference-library/dog-training-archive/karen-pryor_ten-principles-behavior-shaping.pdf` |
| `dog-training-document-archive/operant conditioning clicker training comprehensive guide karen pryor.pdf` | `reference-library/dog-training-archive/karen-pryor_operant-conditioning-clicker-guide.pdf` |
| `dog-training-document-archive/operant conditioning for creative responses in mammals - karen pryor.pdf` | `reference-library/dog-training-archive/karen-pryor_operant-conditioning-creativity.pdf` |
| `dog-training-document-archive/positive reinforcement crate training guide karen pryor.pdf` | `reference-library/dog-training-archive/karen-pryor_positive-reinforcement-crate-training.pdf` |
| `dog-training-document-archive/new owner six week positive reinforcement puppy kindergarten obedience and behavior workbook.pdf` | `reference-library/dog-training-archive/puppy-kindergarten_positive-reinforcement-workbook.pdf` |
| `dog-training-document-archive/puppy socialization bite inhibition and behavioral development critical periods guide.pdf` | `reference-library/dog-training-archive/puppy-socialization-bite-inhibition.pdf` |

### Foundational adoption-advertising papers (renamed and moved)

| Old path | New path |
|---|---|
| `Putting your best pet forward: Language patterns of persuasion in online pet advertisements.pdf` | `source-research/adoption-advertising/putting-your-best-pet-forward_markowitz_2020.pdf` |
| `Exploring Best Practices in Constructing Dog Adoption Advertisements.pdf` | `source-research/adoption-advertising/constructing-dog-adoption-advertisements_kelling.pdf` |

## Moves into tier folders (name unchanged, relocated)

### extractions/ (Tier 2 — compiled generation inputs)

| Old path | New path |
|---|---|
| `key-adoption-profile-research-findings-summary.md` | `extractions/key-adoption-profile-research-findings-summary.md` |
| `recommended-pet-biography-template-format.md` | `extractions/recommended-pet-biography-template-format.md` |
| `recommended-adoption-profile-pictures.md` | `extractions/recommended-adoption-profile-pictures.md` |
| `shelter-dog-adoption-success-rates.md` | `extractions/shelter-dog-adoption-success-rates.md` |

### source-research/ (Tier 1 — peer-reviewed)

| Old path | New path |
|---|---|
| `shelter-outcomes/*` | `source-research/shelter-outcomes/*` (7 files, names unchanged) |
| `behavior-and-welfare/*` | `source-research/behavior-and-welfare/*` (7 files, names unchanged) |

### reference-library/ (Tier 1 — operational/interpretive)

| Old path | New path |
|---|---|
| `handbooks/*` | `reference-library/handbooks/*` (4 files) |
| `credentialing/*` | `reference-library/credentialing/*` (1 file) |
| `training/*` | `reference-library/training/*` (5 files) |
| `body-language/*` | `reference-library/body-language/*` (8 files) |
| `dpfl-learning-library/*` (retained items) | `reference-library/dpfl-learning-library/*` |

## Moves into _parked/ (off-use-case, recoverable — NOT deleted)

All originated under `dpfl-learning-library/`. Each file's original sub-path is
preserved verbatim under `_parked/reference-library/dpfl-learning-library/...`,
so reversal is a move back up out of `_parked/`. 31 files total:

- **10 `.mp4` videos** — not ingestible by the text-RAG pipeline. From the DPFL
  Playgroup Video Library, Flexi Find-Its, and Training Principles Videos.
- **13 DPFL annual impact reports + infographics** (`DPFL Impact and Research/`,
  including `Infographics/`) — organizational impact/marketing, not research or
  generation input.
- **8 Spanish-language cheat-sheet translations**
  (`.../Spanish Language Cheat Sheets/`) — out of scope for English-language
  generation.

Reversal example:
`_parked/reference-library/dpfl-learning-library/DPFL Impact and Research/DPFL Impact Report - 2024.pdf`
→ `reference-library/dpfl-learning-library/DPFL Impact and Research/DPFL Impact Report - 2024.pdf`

## Notes

- No file contents were modified. Renames and moves only.
- `drover` CLI was attempted for auto-naming but its local LLM backend
  (ollama) returned unparseable output in this environment; filenames were
  applied by hand to the file-naming standard (lowercase, hyphens within
  fields, underscores between fields, author/year signal preserved).
- New index files created (not moves): `README.md`, `_reorg-manifest.md`.
- The `dpfl-learning-library/` collection retains its original internal folder
  names (with spaces and special characters) intentionally, to keep it
  recognizable as a vendor-supplied named collection.
