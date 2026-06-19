# BioWriter UI/UX Design

Design reference for the BioWriter user interface. Captures the layout model, interaction patterns, and the Share subsystem settled during design sessions, so they survive into the build. BioWriter is not yet scaffolded (plan Phase 5/6); this document is the design input for that work.

## What BioWriter is

BioWriter is the generation plane of Evermore: a tool that turns an animal's curated evidence into research-backed adoption content (kennel cards, social posts, ads), scores it live against the adoption-research rubric, versions it, and exports it. Its first and highest-exposure surface is the kennel card writer, the text that becomes the animal's public listing on the sites adopters search.

The end user is a **shelter volunteer or staff member**: often non-technical, time-pressed, frequently on a shared office machine. The design optimizes for someone who needs a good card finished and listed quickly, not for a power user who enjoys steering a tool. Adopters read the output but never touch BioWriter.

### Where BioWriter sits on the data spine

`Sources -> Animal Record -> Package -> Composition -> Export`

- BioWriter consumes a **Package** (curated, provenance-bearing evidence assembled in Pet Data) plus a **Template**, and produces a **Composition** (the generated and human-edited piece, auto-versioned, provenance retained).
- **Export** renders a Composition to a flat file (PDF, DOCX, Drive). Export drops inline provenance by design; see the version stamp below for the one pointer that survives.
- The animal is **pre-selected upstream** in the Stacker portal. Choosing which animal is not a BioWriter screen; BioWriter opens with the animal and its Pet Data already present.

## The core interaction loop

Everything in the interface serves one loop:

**generate-or-paste -> score -> recommend -> accept/modify -> re-score -> repeat**

1. The volunteer picks a channel (Kennel Card or Social Media).
2. The canvas prepares for that channel. The volunteer clicks **Generate** or **pastes** their own text.
3. As soon as text is present, it is **scored** against that channel's rubric.
4. The conversation opens with a recommendation and an accept-or-modify choice, and continues organically.
5. Accepting a recommendation, or selecting evidence, re-generates the relevant part and re-scores.

The loop has no hard gate. The volunteer decides when the card is done; the score advises, it does not block (see Share, below).

## Viewport model

BioWriter **nests inside the Stacker portal shell**. The portal's top bar (Evermore identity, the active app, user menu, theme control) stays in place, so the user can always tell which application they are in. Within that shell, BioWriter renders a stable four-zone workspace that persists for the whole session. The user never navigates away to adjust something.

```
+------------------------------------------------------------------+
|  Stacker portal bar:  Evermore   BioWriter        avatar  theme  |
+------------------------------------------------------------------+
|  Canvas header (slim, fused):  Sally  [Kennel Card|Social]  ▰ score  Share |
+--------------+------------------------------------+--------------+
|              |                                    |              |
|  Left rail   |            Center canvas           |  Right rail  |
|  conversation|         the bio (flat card)        |  animal data |
|              |                                    |  (evidence)  |
|              |                                    |              |
|  [composer]  |        ...footer: version stamp    |              |
+--------------+------------------------------------+--------------+
```

The widget vocabulary is whatever fits the app. The *model* is settled; specific controls are not borrowed wholesale from any reference tool.

### Zone 1: left rail, the conversation

The primary channel, conversational. The volunteer talks to the assistant to guide, ask questions, and refine, regardless of whether they are looking at a generated draft, a template, or their own pasted text. The conversation persists all session.

- A persistent **composer** at the bottom. Selecting evidence in the right rail flows into the composer as **removable chips**; the volunteer can add a free-text rider next to the chips and send one message. The two input modes (talking and selecting) are one channel into the model, and literally one input box.
- The assistant's recommendations carry an inline **accept (Apply) / modify** choice, so the volunteer accepts output piece by piece.
- Selecting evidence produces a visible turn in the transcript ("Added her crate-training history, updated the Home Behavior section"), so the conversation stays an honest history of what drove each version.

### Zone 2: center canvas

The largest zone, a calm cream surface where the Composition lives as a flat card. It holds the rendered bio for the active channel. Empty and working states own this space too (a quiet centered prompt, a slim determinate progress bar), never a spinner-only void. Chrome stays out of its way.

The canvas carries a gentle footer with the **version stamp** (see Share).

### Zone 3: right rail, selectable animal data

The evidence selection surface, drawn from the animal's Pet Data. Each item is a checkbox row showing the fact **and its source** in small text (for example, "Rests head on your lap when seated, intake note, May 12").

The volunteer multi-selects items, which compose into the composer as chips, then submits one message that injects the selection into the conversation and re-generates.

Because every item carries its `{source, location, category}`, **this rail is also the provenance surface**. Provenance appears at the moment of inclusion, where it is most legible, rather than as a separate panel to hunt for.

### Zone 4: canvas header, slim and fused

To avoid two stacked toolbars (the portal bar plus a second BioWriter bar), BioWriter's own controls live as a **slim row fused to the top edge of the canvas**, not a full second bar. It carries:

- The animal name (editable).
- The **channel toggle** (Kennel Card | Social Media).
- The ambient **score** indicator.
- The **Share** action.

These are global to the artifact. Per-element actions belong to the rails.

## Channels

BioWriter produces multiple content types from the same evidence. The first two are **Kennel Card** and **Social Media**. The header toggle switches between them.

The channel toggle swaps more than content. Each channel is a **separate document with its own state**:

- Its own **rubric** (a roughly 200 to 280 word warm narrative for a kennel card, versus a short hooked post with a call to action and a character budget for social).
- Its own **canvas shape** (a card frame versus a post with a character counter).
- Its own **score**.

The evidence pool is shared across channels, but inclusion is tracked per channel. Selecting data for the card does not leak into the post.

## Score

The score measures the current draft against the active channel's research rubric. It is **always on**: as soon as text is present, it scores.

- **Ambient readout**, fused to the canvas header: a slim indicator with a gentle status gradient and a short label. Zero interaction, always in peripheral vision.
- **On-demand detail**: clicking the indicator opens a floating panel with the rule-by-rule diagnosis, the research reason behind each rule, and a one-tap "fix this" that drops into the composer as a conversation turn.

The score and the conversation's recommendations are **one rubric analysis surfaced two ways**, not two separate critique systems. The score is the glance; the conversation is the fix. Build them from one pass so the volunteer is never told the same thing twice in two voices.

Tone is load-bearing. A red bar on a card a volunteer wrote with care reads as a slap. The score leads with the animal and the goal ("here is how to get Sally adopted faster"), never with the deficiency, and pairs color with generous copy.

> Open question: a red/amber/green-style gradient pulls in semantic status colors the seven-color Backchain palette does not carry. Resolve by either extending the design system with semantic status tokens or expressing the score within palette. See Open questions.

## Share

Share is always available. The score **warns but never gates**. The human stays in charge; a rubric does not override someone who knows this specific animal, and a time-pressed volunteer is never trapped in perpetual "needs work."

### Override flow

When the volunteer shares a low-scoring card, a single confirmation appears (a modal, the right treatment for a discrete, self-contained task). It names what is weak and offers two paths:

- **Fix it** returns to the loop.
- **Share anyway** proceeds and fires the eval capture.

The warning copy carries the warmth ("Heads up: this leads with how Sally looks, not what she does, which research ties to slower adoption. Share anyway, or take 30 seconds to fix it?"). The warning is the override consent.

### Share is one atomic transaction

A Share bundles four things against a single immutable version id:

1. **Freeze** the Composition version (snapshot exactly what was shared, so later edits do not change what a printed card resolves to).
2. **Stamp** the artifact with that version (see below).
3. **Capture** the eval record.
4. **Log** the override flag, if any.

### Eval capture

Capture **every Share**, not only overrides. High-score shares are the positive baseline; logging only the contested tail yields a dataset of disputes with nothing to calibrate against. The override is one flag on the record, not the trigger.

Each record captures:

- The final shared text.
- The full conversation transcript (chips, free-text riders, every model turn).
- The score breakdown at the moment of Share (failed rules and values).
- The animal-data items included versus excluded (the Package selection, with provenance).
- The channel.
- The warnings shown and dismissed, and the override flag.
- A stable **animal-record reference**.

The animal-record reference is the keystone. It lets the capture log later join to the **adoption outcome** (whether the animal was adopted, and how fast). That join is how Evermore validates or corrects its own research rubric: the score is a hypothesis, and overrides plus outcomes are the experiment that tests it. This is the mechanism behind the phrase "research-backed."

Capturing volunteer prompts and content for analysis must be disclosed in the shelter's terms. The risk is low (their own data in their own tool), but it is not silent.

### Version stamp

Every Share embeds the **Composition version** into the artifact. This is the minimal provenance bridge across the Export boundary: the exported file stays flat, but carries one resolvable pointer back to the versioned, provenance-rich Composition. It does not reintroduce inline citations into an adopter-facing card; it stamps one reference home.

- The stamp is an **internal forensic anchor**, not an adopter feature, which is why it stays gentle. It must resolve uniquely (a bare "v7" is not unique across animals): use an animal-plus-composition-plus-version reference or a compact code.
- Embedding is channel-specific. On a kennel card (PDF, DOCX, print) the stamp is gentle footer text. A social post has no footer and no character budget to spare, so for social the version rides in the capture log and post metadata, never the visible caption.

## States to design

- **Empty.** Channel chosen, no text yet: canvas shows a prepared frame and a Generate or paste affordance, no score yet, the right rail lists available evidence, the conversation offers a quiet prompt to draft from the animal's records.
- **Working.** Canvas shows a centered status message and a slim determinate progress bar; the conversation streams collapsible step chips; controls are quiet.
- **Populated.** Draft on the canvas, score active, evidence selectable, Share enabled.
- **Override.** The Share confirmation modal over a low score.

## Brand and register

BioWriter inherits the Backchain design system: the cream canvas (`#F5F0E8`), charcoal headings (`#41423D`), gray body (`#50636F`), deep coral (`#A35945`) for interactive elements, coral (`#E07A5F`) decorative only, Inter for content, flat cards with hairline borders, no drop shadows, never pure black or pure white. The tokens transfer cleanly.

The **register** does not transfer wholesale. Backchain's consulting identity (industrial, "Modern Industry / Reborn Code," carved typography) is cold for a mission product about adopting an animal, used by volunteers and read by adopters. BioWriter keeps the tokens and dials the voice and imagery toward warmth and approachability. Whether this warrants a distinct Evermore product sub-brand is an open question (below).

## Open questions

- **Product sub-brand.** Does Evermore/BioWriter get its own warmer product identity, or inherit the Backchain consulting brand with only a tone adjustment? A warm product seed-prompt variant (same tokens, warmer philosophy) is the likely artifact.
- **Score color.** A traffic-light score needs semantic status colors outside the seven-color Backchain palette. Extend the design system with semantic status tokens, or keep the score within palette (for example, coral-intensity only).
- **Export per channel.** Share/Export behavior differs by channel: PDF, DOCX, or Drive for a kennel card versus a character-aware copy action for social.
- **Eval-logging disclosure.** Where in the shelter's terms the eval capture is disclosed.

## References

- Conversational Workspace UI pattern (the source of the viewport model), in the brand working files.
- Backchain design system: tokens, components, voice, and fonts, packaged for Claude Design.
- Vision and architecture: `docs/evermore-vision-and-architecture.md`.
- Data spine vocabulary: root `CLAUDE.md`.
