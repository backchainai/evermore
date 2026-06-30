# Evermore Design System

> The shared visual + interaction system for **Evermore** — a suite of focused apps for animal shelters and rescues. One calm, blue-and-slate identity so every module (BioWriter, Snapshot, Matchmaker, Intake) feels like one coherent product even when each module's UX differs.

Link `styles.css` and the cool blue/slate token system is live as CSS custom properties; every Evermore module consumes the same tokens so the suite reads as one product.

> **Source of truth.** This package is the in-repo mirror of the canonical Claude Design project ([BioWriter](https://claude.ai/design/p/a310b7ad-1856-4ab1-89b1-c6a9d5203801?file=BioWriter.dc.html)). The repo carries the **consumed layer** (tokens, fonts, the `styles.css` entry) plus the **design contracts** (each primitive's `.prompt.md` spec and `.d.ts` API). The reference React `.jsx` implementations, the compiled `_ds_bundle.js` kit, the specimen guideline cards, and the interactive BioWriter preview live in the Claude Design project and are pulled in on demand via the `/design-sync` workflow, not vendored here.

---

## 1. Product context

Evermore is an **application made of modules**. Each module is its own project/surface, but they share this system so they read as one product:

| Module | Glyph | What it does |
|---|---|---|
| **BioWriter** | BW | Turns an animal's records into a publish-ready adoption bio (the reference module). |
| **Snapshot** | SN | Photo cleanup and kennel-card imagery. |
| **Matchmaker** | MM | Matches animals to prospective adopters. |
| **Intake** | IN | Records and paperwork. |

A persistent **animal subject** (e.g. "Sally") follows the user across modules — switching apps keeps the selected animal. The chrome (top bar with wordmark + module switcher + subject selector) is shared; the body of each module is its own thing.

---

## 2. Content fundamentals (voice & copy)

The voice in one line: **the steady colleague at the next desk** — warm, specific, and genuinely glad to help with the work, never selling it. Evermore talks to shelter staff who are busy and care a lot; it respects their time and their judgment.

- **Person & casing.** Second person to the user ("Reply, or ask for a different angle"). Sentence case everywhere except the Outfit wordmark. Eyebrow/section labels are UPPERCASE with wide tracking ("ASSISTANT", "VERSION OF THIS COMPOSITION").
- **Be concrete.** Name the specific thing: "Lead with what she does, not how she looks", "House-trained and crate-comfortable is your strongest line." Specifics beat vague warmth.
- **Offer the next step.** End on what to do ("book a meet-and-greet"), not a tidy slogan.
- **Calm status.** System messages are plain and reassuring: "BioWriter rewrote this. Use Next to continue." / "Ignored. The card is unchanged."

**Avoid:** hype vocabulary (transform, unlock, supercharge, AI-powered), em-dashes as connectors, three-part closers, manufactured urgency, and **emoji** (never used).

---

## 3. Visual foundations

**Aesthetic:** a calm clinical-but-warm product surface. Cool light canvases, white cards, one confident blue doing all the interactive work, slate for structure, and small warm accents (amber for "look here", green for "done"). Dense where it needs to be (app chrome, record lists), generous where it counts (the composition canvas).

### Color
- **Blue `#1A7AC2`** is load-bearing: every interactive thing (buttons, links, active tabs, eyebrows, focus rings, selected rows) is blue. **Slate `#1F3B54`** carries headings, labels, and emphasis. **Gray `#50636F`** is body text and, via an alpha scale, every hairline border.
- **Amber `#EF8E1F`** = attention/decoration only ("needs review" markers, the active citation). **Green `#2FB85F`** = positive/applied/live. **Red `#C0392B`** = destructive/error, always paired with an icon.
- **Surfaces:** canvas `#F1F5F8`, work canvas `#E9F1F7`, white `#FFFFFF` cards (white appears *only* on card surfaces), tinted `#E3EEF6` for avatars and selected rows.
- **Dark sections** flip via `.on-slate`: deep navy-slate `#16293B` canvas, near-white text, lightened blue, translucent-white cards.
- Text-role convention is **not "darkest wins"** — body is gray, headings are slate, interactive is blue. Contrast comes from role.

### Type
- **Three fonts, differentiation by color + density, not typeface.** **Inter** carries everything (chrome, body, headings, captions). **Outfit** is the wordmark only. **JetBrains Mono** for code, IDs, and version strings (`sally-kc-v7`).
- Fluid `clamp()` scale: Display 36→60, H1 30→36, H2 24→32, H3 20→24, body 16, small 14, xs 12. Plus **app-density steps**: 13px UI text and 11px meta drive the dense module chrome.
- Headlines: gentle tight tracking (−0.01em), 1.2 line-height. Body: 1.625, ~65ch measure.

### Shape, borders, elevation
- **Flat cards:** white surface, 1px gray-alpha hairline border, **no shadow.** Shadows are reserved for floating UI (menus, popovers, modals) and are slate-tinted, never pure black.
- **Radii:** 4px inputs, 6px cards/buttons/menus, 10px modals, pills for chips/avatars.
- Hairline alpha scale: 5 / 10 / 14 / 22 / 28 / 40% of gray.

### Motion & interaction
- Calm and intentional. Default 200ms, ease-out `cubic-bezier(0.16,1,0.3,1)`.
- **Hover:** filled buttons dim to `opacity:0.9`; secondary buttons' border goes gray → solid slate; interactive cards raise border alpha and lift `translateY(-2px)`; rows get a faint gray wash.
- **Press:** `scale(0.98)`. **Focus:** 2px blue `:focus-visible` ring, 2px offset. Honors `prefers-reduced-motion`. Hit targets ≥ 44px.

### Layout
- App shell is a **slim top bar (48px) over a three-zone body**: left rail (≈308px), flexible center canvas, right panel (≈324px). Floating menus drop from the bar. The reading measure inside documents caps ~65ch.

---

## 4. Iconography

Evermore is **near-iconless by design** — typography and color do the work.

- **Unicode glyphs** stand in for UI affordances, rendered in the brand fonts: `▾` (menu), `‹ ›` (prev/next), `→` (send / next step), `↳` (reply-to), `✓` (checked / applied), `×` (remove / dismiss), `▲` (form error), `◑` (theme). No icon font is shipped.
- **Two-letter module glyphs** (BW, SN, MM, IN) in rounded blue squares are the closest thing to an icon set — they identify modules in the switcher.
- **The blue dot** is the brand's smallest mark; it precedes the wordmark.
- **No emoji, ever.**
- If a future module genuinely needs a multi-icon set (a dashboard, a toolbar), substitute **[Lucide](https://lucide.dev)** via CDN — thin, even-stroke, geometric — set to slate (or blue for interactive). Flag the substitution; it is not a brand-provided set.

---

## 5. Repository index / manifest

**Root**
- `styles.css` — the single entry point consumers link (`@import`s only).
- `readme.md` — this guide. · `SKILL.md` — Agent-Skill front matter for Claude Code.
- `assets/fonts/` — the three variable fonts (Inter, Outfit, JetBrains Mono) + their OFL licenses.

**Tokens** (`tokens/`, all reached from `styles.css`)
- `fonts.css` — `@font-face` for Inter, Outfit, JetBrains Mono.
- `colors.css` — raw palette, alpha scale, status; Evermore light (`:root`) + dark (`.on-slate`) aliases.
- `typography.css` — families, fluid scale, app-density steps, weights, tracking.
- `spacing.css` — spacing, radius, border width, elevation, motion, layout, z-index.
- `base.css` — resets, canvas/body defaults, link + focus + reduced-motion.

**Component contracts** (`components/`) — the design spec + API for each primitive; each has a `.prompt.md` (how/when to use it) and a `.d.ts` (prop contract). The reference React `.jsx` implementations live in the Claude Design project.
- `core/` — `Button`, `Card`, `Badge`, `SectionLabel`
- `forms/` — `TextField`

**In the Claude Design project, not vendored here** (pull via `/design-sync` when needed)
- `components/**/*.jsx` + `evermore-kit.js` — reference React implementations and the compiled kit.
- `guidelines/` — specimen cards for the Design System tab: Colors (primary, accent & status, surfaces, text roles, dark section), Type (families, scale, app density), Spacing (scale, radius, elevation), Brand (wordmark & glyphs, voice).
- `ui_kits/biowriter/` — the reference-module preview; the live interactive component is `BioWriter.dc.html` at the project root.

### Consumer quickstart
```html
<!-- Link once; the cool blue/slate token system is now live as CSS custom properties. -->
<link rel="stylesheet" href="styles.css">
```
Tokens are available as CSS custom properties the moment `styles.css` is linked (e.g. `var(--color-cta)`, `var(--color-canvas)`, `var(--radius-md)`, `var(--space-lg)`). Build module UI in whatever framework the module uses (the Stacker portal is SvelteKit) against these tokens; the `.prompt.md` + `.d.ts` contracts in `components/` define how each primitive should look and behave.

---

## 6. Current scope
- **Five primitives.** `Button`, `Card`, `Badge`, `SectionLabel`, `TextField`. Evermore-native chrome (app top bar, side rail, suggestion card, record row, module switcher) is not yet a primitive; it currently lives inside `BioWriter.dc.html`.
- **No bespoke logo asset.** The mark is the blue dot + Outfit wordmark, by design.
