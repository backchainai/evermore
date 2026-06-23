# BioWriter design import

Generated UI design for the BioWriter service, imported from Claude Design (Anthropic's design product) via the `claude_design` MCP connector.

## Provenance

- **Source project:** "BioWriter" (Claude Design), owner Chris Krough
- **Project URL:** https://claude.ai/design/p/a310b7ad-1856-4ab1-89b1-c6a9d5203801?file=BioWriter.dc.html
- **Project ID:** `a310b7ad-1856-4ab1-89b1-c6a9d5203801`
- **Imported:** 2026-06-20, via the `DesignSync` MCP read methods (`list_files` / `get_file`)
- **Direction:** read-only pull (generation output). The writable design-system project is separate; do not push changes here back up with `/design-sync`.

This is a design artifact (a clickable comp), not the production BioWriter app. The settled UI/UX spec it realizes is at `services/biowriter/docs/design/ui-ux-design.md`.

## Contents

- `BioWriter.dc.html` : primary comp. Evermore portal shell (app switcher, persistent animal selector) wrapping the BioWriter kennel-card editor: assistant rail with cited suggestions, evidence/records rail, version drawer, and a quality score. Slate-and-blue canvas.
- `BioWriter - Coral.dc.html` : earlier variant on the Backchain cream-and-coral palette, single-suggestion layout.
- `support.js` : the dc-runtime that renders `.dc.html` comps (React-based, generated; do not edit by hand).
- `_ds/backchain-design-system-498b670c-d505-45f2-92e8-791ed34722f0/` : the embedded Backchain design system the comps were generated against.
  - `styles.css` : single entry point (imports the token files in order).
  - `tokens/` : `fonts.css`, `colors.css`, `typography.css`, `spacing.css`, `base.css`.
  - `_ds_bundle.js` : compiled React component primitives (Button, Card, etc.) exposed on `window.BackchainDesignSystem_498b67`, referenced by the comps via `<x-import>`.
  - `readme.md` : the design system's own documentation (verbatim from source).
  - `assets/fonts/` : the three variable font masters (Inter, Outfit, JetBrains Mono) with their OFL licenses, referenced by `tokens/fonts.css`.

## Viewing the comps

The `.dc.html` files load `support.js` and `_ds_bundle.js` over relative paths and need React/ReactDOM/Babel at runtime, so they render in the Claude Design environment (or any host that provides those globals). Opening the file directly with `file://` will not fully render without that runtime; view it in the source project for an exact preview.

## Fonts

The three variable font masters live in `_ds/.../assets/fonts/` and resolve the `@font-face` rules in `tokens/fonts.css` (`Inter-Variable.ttf`, `Outfit-Variable.ttf`, `JetBrainsMono-Variable.ttf`), so the comps render in Inter and Outfit rather than falling back to `system-ui`. Each ships next to its SIL Open Font License (`*-OFL.txt`); all three are OFL 1.1 and redistributable. They were vendored from the Backchain brand assets rather than pulled over the MCP, because the Claude Design `get_file` method caps responses at 256 KiB and the Inter master alone is ~854 KiB.

## Not imported

- **`uploads/pasted-1781910063581-0.png`** : a design-time reference paste (a 2440x1036 screenshot), not referenced by either comp. It exceeds the 256 KiB `get_file` cap and is not needed for the comps.
- **`_ds_manifest.json` / `_adherence.oxlintrc.json`** : design-tool metadata describing the full Backchain component library (`components/`, `ui_kits/`, `guidelines/`) that is not part of this token-only embedded bundle; they reference paths absent from this import.

## License

Apache License 2.0. Copyright (C) 2026 Backchain LLC. See [LICENSE](../../../LICENSE).
