# Backchain Design System

> **Discover Where AI Works.** The visual + voice system for **Backchain** (Backchain LLC) — an AI & automation consulting practice founded by Chris Krough. "Modern Industry / Reborn Code": industrial refinement, substance over flash, carved typography, flat cards, a warm cream canvas with one disciplined coral accent.

This project is a self-contained Claude Design system: link `styles.css`, mount the React primitives, and copy assets out of `assets/`. Everything a consumer needs ships here.

---

## 1. Company & product context

**Backchain** is the business brand of Chris Krough — 25+ years scaling platforms through 3 IPOs, 8 acquisitions, and hypergrowth (Amazon, OJO, Rackspace, Bazaarvoice, RetailMeNot). The practice helps small and mid-sized teams adopt AI and automation *where it actually pays*, and avoid it where it doesn't.

- **Positioning:** The Pragmatic Craftsman — the seasoned builder who has seen what works at scale, not the flashy AI evangelist.
- **Tagline:** *Discover Where AI Works* (marketing surfaces only).
- **Name origin:** *backchain training* — master the final step first, then build the chain backward so the learner always knows where it is going. Mirrors backpropagation and the consulting method (start from the outcome, work back to the capabilities). The mark is a **howling wolf** (training/pack motif), not blockchain imagery.
- **Domain:** backchain.ai · **Contact:** chris@backchain.ai
- **Primary surface:** the `backchain.ai` marketing site (recreated in `ui_kits/backchain-website/`).

### Sources this system was built from
Provided as an upload package (`uploads/backchain-claude-design-package_2026-06-19.zip`), preserved under `source/`:

| Source file | What it gave |
|---|---|
| `source/spec/visual_identity.md` | Master visual spec — palette rationale, WCAG ratios, type roles, layout, motion, logo philosophy |
| `source/spec/components.md` | Component library spec (Button, Card, Form Field, Badge, Stat Grid, Styled List…) |
| `source/spec/business_voice-guide.md` | Backchain voice & tone for all copy |
| `source/spec/brand_foundation.md` | Positioning, archetype, anti-position, proof points, naming |
| `source/spec/audience_strategy.md` | Per-touchpoint audience analysis |
| `source/tokens/design_tokens.css` / `.json` / `tailwind_preset.mjs` | Deterministic token values (the basis for `tokens/`) |
| `source/examples/backchain-visual-identity-reference.{png,html}` | Rendered reference of the live palette, type, and components |
| `source/assets/*` · `source/fonts/*` | Logo lockups, wolf logomark, favicon, the three variable fonts |

> **Two-brand note.** The source defines a sibling personal brand, *Chris Krough* (dark slate canvas), as the chromatic inverse of Backchain. This system is **scoped to Backchain** (light cream canvas). The dark scope is still shipped — apply `.on-slate` (or `[data-brand="chris-krough"]`) to any band to flip to cream-on-slate. Never co-brand the two in one artifact.

---

## 2. Content Fundamentals (voice & copy)

The voice in one line: **confident, interested, unhurried — the senior engineer who has done the harder version of this work for 25 years, would enjoy doing it again with you, and does not need the contract to make the month.** Peer-to-peer, never vendor-to-prospect.

**Four concurrent dials:** Confident (short, declarative refusals) · Excited (genuine pleasure in the *work*, not the deal) · Friendly (contractions, warm closer, reader is a former colleague) · Unattached (no manufactured urgency, "one open slot" is one open slot).

**Casing & person.** Sentence case everywhere except the Outfit wordmark (Title Case) and eyebrow/section labels (UPPERCASE, wide tracking). First person "I"/"we" for methodology and built-work; no addressed-reader salutations on the website.

**Do**
- Lead with the work, not throat-clearing. Open on what the work *is* or why it's interesting.
- Use concrete, specific proof: named clients, named systems, named numbers, named years ("6,700% growth at OJO", "200+ services migrated, zero downtime"). Specifics earn trust; generic claims read as marketing.
- Refuse short and reasoned, in one beat ("I can't size that without your SOW; I'd be guessing").
- State price plainly inline ("$270/hr, prepaid retainer, unused balance refunded").
- Lane lines in plain English a non-engineer can hold ("outside my wheelhouse").

**Avoid (AI-slop & salesperson tells)**
- Hype vocabulary: *transform, leverage, synergy, unlock, step-change, AI-powered, AI-native, AI wizard*. Lead with the customer outcome, not with "AI".
- **Em-dashes** — use colons, parentheses, or commas instead (a generation + autocorrect tell).
- **Tricolons** (three-beat lists) and **aphoristic closers** (tidy bows). End on the last specific thing.
- **Negation-contrast framing** ("real X, not fake Y", "substance over hype" *as a sentence*). Rewrite as a plain claim.
- Definitional intros to terms the reader knows; "just checking in"; CTAs stacked at every turn; pipeline-scarcity inflation.

**No emoji.** The brand never uses emoji in copy or UI. Markers are typographic (the deep-coral em-dash list marker) — see Iconography.

*Examples & full methodology: `source/spec/business_voice-guide.md`. The voice card lives in the Design System tab → Brand → "Voice in one line".*

---

## 3. Visual Foundations

**Aesthetic:** renovated industrial space — exposed concrete, weathered metal, factory light. Serious work, beautifully. Substance over flash; material authenticity; restrained palette with one punchy accent; large, unhurried, "carved" typography; product shown with pride; intellectual warmth.

### Color
- **Seven colors only**, never more. Never pure black (`#000`) or pure white (`#FFF`) — everything carries warmth and age.
- **Canvas:** cream `#F5F0E8`. **Card surface:** off-white `#FAFAF8` (the floating-card effect).
- **Text roles (not "darkest wins"):** headings/labels/emphasis = charcoal `#41423D`; **default body paragraphs = gray `#50636F`** (5.2:1 on cream, the quiet voice); eyebrows + stats = deep coral `#A35945`.
- **Accent rule — load-bearing:** **deep coral `#A35945` for anything interactive** (CTAs, link hover, nav, stats; 4.55:1 AA on cream). **coral `#E07A5F` for decoration only** (icons, dividers, blocks; fails WCAG as text; max 5–10% of a view). Never put text on coral or coral on cream as text.
- **Dark bands:** slate `#2F455B` canvas, cream text at 80% alpha, cards composite as cream/5 surface + cream/10 border (never solid gray).

### Type
- **Three fonts, differentiation is color not typeface.** **Inter** carries *all* web content (Display 700 hero → H2 600 → H3/H4 500 → body 400 gray → caption 300). **Outfit** is **brand/logo only** (wordmarks, lockups) — never general headings. **JetBrains Mono** for code.
- Fluid `clamp()` scale: Display 36→60px, H1 30→36, H2 24→32, H3 20→24, H4 18→20; body fixed 16px; small 14; XS 12 (eyebrows, uppercase, 0.05em tracking).
- Headlines: tight line-height (1.2), tight tracking (−0.02em), generous scale, confident not shouting. Body: 1.625 line-height, 65–75ch measure.

### Backgrounds & texture
Backgrounds are environments, not decorations: subtle concrete/grain at low opacity (5–15%), atmospheric slate-tinted shadow gradients suggesting factory light. **No** obvious texture tiles, heavy patterns, **bluish-purple gradients**, or generic stock imagery. Imagery direction is warm and atmospheric — UI on concrete, steel beams, factory windows, metal patina. Full-bleed photography is used sparingly and always warm-toned.

### Cards, borders, radius
- **Canonical card is flat:** off-white surface, **1px hairline gray/10 border, no drop shadow.** Shadows are reserved for floating UI (dropdown/popover/modal), and even then are warm slate-tinted, never pure black.
- **Modest, carved radii:** 2px inputs, 4px cards/buttons, 8px modals; pills for tags only. Large radii read playful and fight the aesthetic.
- Border widths: 1px hairline (default), 2px (focus/active input), 4px (heavy emphasis rules).
- Alpha scale for hairlines/muted text: 5 / 10 / 20 / 30 / 40 / 70 / 80%.

### Motion & interaction
- **Weighty, intentional, unhurried** — mechanical inspiration (slide, lift, rotate). Default 200ms, ease-out `cubic-bezier(0.16,1,0.3,1)`. No bouncy or frantic motion; no infinite decorative loops.
- **Hover:** links shift to deep coral + underline; filled buttons dim to `opacity:0.9`; secondary buttons' border goes gray/40 → solid charcoal; interactive cards raise border alpha and lift `translateY(-2px)`.
- **Press:** `transform: scale(0.98)`.
- **Focus:** `:focus-visible` 2px outline in text color, 2px offset (keyboard only).
- Honors `prefers-reduced-motion`. Touch targets ≥ 48px with ≥ 8px spacing.
- Transparency/blur is used once with intent: the sticky header is translucent cream with a light backdrop blur. Used sparingly, not as decoration.

### Layout
Asymmetric balance, generous whitespace ("20-foot ceilings"), floating card architecture, a `72rem` page container, body measure capped ~65ch. Hero moments anchor sections.

---

## 4. Iconography

Backchain is **near-iconless by design** — the system leans on typography, not an icon set, in keeping with "substance over flash."

- **Typographic markers are the brand's iconography.** The signature is the **deep-coral em-dash (`—`) list marker** (see `StyledList`). Unicode glyphs stand in for the few UI affordances needed: `→` (tertiary-button / "read more"), `↗` (external link), `✓` (success), `▲` (form error), `≡` (mobile menu). These render in the brand fonts; no icon font required.
- **No emoji, ever** — not in copy, not in UI.
- **The one pictorial mark is the wolf logomark** (`assets/backchain-logomark-*.png`), used as favicon/avatar and in lockups. It is a brand asset, not a UI icon.
- **No icon library shipped in the source package.** If a build genuinely needs a multi-icon set (dashboards, feature grids), substitute **[Lucide](https://lucide.dev)** via CDN — its thin, geometric, even-stroke style is the closest match to the "carved, clean-line, geometric" logo philosophy. Set stroke to charcoal (or deep coral for interactive) and keep weight light. **This is a substitution, not a brand-provided set — flag it and confirm with the user before relying on it.**

---

## 5. Repository index / manifest

**Root**
- `styles.css` — the single entry point consumers link. `@import`s only.
- `readme.md` — this guide. · `SKILL.md` — Agent-Skill front matter for download into Claude Code.
- `assets/` — logos, wolf logomark (slate / cream / coral / light), favicon, fonts.
- `source/` — the original upload package (specs, tokens, examples), preserved for reference.

**Tokens** (`tokens/`, all reached from `styles.css`)
- `fonts.css` — `@font-face` for Inter, Outfit, JetBrains Mono (variable masters in `assets/fonts/`).
- `colors.css` — raw 7-color palette, alpha scale, status colors; Backchain (`:root`) and dark (`.on-slate` / `[data-brand]`) semantic aliases.
- `typography.css` — families, fluid type scale, weights, line-heights, tracking.
- `spacing.css` — spacing, radius, border width, elevation, motion, z-index, layout.
- `base.css` — global resets, canvas/body defaults, link underline-on-hover, focus ring, reduced-motion.

**Components** (`components/`) — React primitives; each has `.jsx` + `.d.ts` + `.prompt.md`, with one `@dsCard` per group.
- `core/` — `Button`, `Card`, `Badge`, `SectionLabel`, `StatGrid`, `StyledList`
- `forms/` — `TextField` (input + textarea, full validation states)
- `navigation/` — `SiteHeader`, `SiteFooter`

**UI Kits** (`ui_kits/`)
- `backchain-website/` — full backchain.ai homepage recreation (hero, services, the backchaining method on a dark band, working contact form, footer). See its `README.md`.

**Foundations** (`guidelines/`) — specimen cards shown in the Design System tab: Colors (primary, accent, supporting, text-roles, dark-section), Type (headings, body, families), Spacing (scale, radius, elevation), Brand (lockup, logomark, voice).

### Using the system (consumer quickstart)
```html
<link rel="stylesheet" href="styles.css">
<!-- React + ReactDOM + Babel, then: -->
<script src="_ds_bundle.js"></script>
<script type="text/babel">
  const { Button, Card, SectionLabel } = window.BackchainDesignSystem_498b67;
  // …compose
</script>
```
Tokens are available as CSS custom properties the moment `styles.css` is linked (e.g. `var(--color-cta)`, `var(--text-display)`, `var(--space-lg)`).

---

## 6. Caveats
- **No icon set was provided** — see Iconography §4. Lucide is a flagged substitution.
- The source shipped only **light logo variants**; the cream / slate / coral logomarks in `assets/` were recolored from the light master for dark-section and accent use.
- Outfit is intentionally **not** used for body/headings — Inter carries all content. Outfit appears only in the wordmark fallback and logo lockups.
