---
title: "Design System Concept 1 — Lapis & Clay"
subtitle: "Deep Excavation Layer"
status: draft
created: 2026-05-22
---

# Concept 1 — Lapis & Clay

**Tagline:** *Excavation as interface. Every surface is a layer to be uncovered.*

**Feeling:** You are looking into a site trench. The interface has physical depth—not decorative shadow tricks, but genuine surface hierarchy that reads like geological strata. Clay tablets feel like clay. Lapis lazuli blue demarcates scholarly structure. Everything is warm, serious, and built for long working sessions.

**Target mood:** Archaeological site director's workstation — trusted, precise, unapologetically material.

---

## Design Principles

1. **Stratigraphy, not flatness.** Four distinct surface levels: bedrock (deepest), excavation floor, working table, raised artifact. Each level has a distinct value and tactile treatment.
2. **Lapis structures, clay speaks.** Blue-derived tones own navigation, structure, and chrome. Clay/earth tones own data, content, and text.
3. **Inset = resting, raised = interactive.** Inputs and passive areas are inset (press into the surface). Buttons and interactive cards are raised.
4. **Warmth in darkness.** Backgrounds are near-black but with a warm red undertone — no cold grays.
5. **No pill buttons.** Radius system tops out at 4px. Sharp corners on structural elements, 2px on inputs.

---

## Color System

### Base Palette

| Token | Value | Role |
|-------|-------|------|
| `--color-bg` | `#141210` | Bedrock — deepest background, ATF viewer, image viewports |
| `--color-bg-deep` | `#1a1714` | Excavation floor — sidebars, secondary panels |
| `--color-bg-surface` | `#211d19` | Working table — main content area |
| `--color-bg-elevated` | `#2c271f` | Raised surface — cards, active panels |
| `--color-bg-top` | `#352f26` | Topmost raised — tooltips, popovers, dialogs |
| `--color-border-deep` | `#1e1b16` | Hairline at deepest level |
| `--color-border` | `#3a332a` | Standard border |
| `--color-border-raised` | `#4a4035` | Border on raised surfaces |
| `--color-border-focus` | `#6a8cbf` | Focus ring (lapis-derived) |

### Text

| Token | Value | Role |
|-------|-------|------|
| `--color-text` | `#e9e4de` | Primary text — warm white, not pure |
| `--color-text-secondary` | `#9e9288` | Secondary text |
| `--color-text-muted` | `#6b6158` | Muted/tertiary |
| `--color-text-disabled` | `#4a4038` | Disabled state |
| `--color-text-inverse` | `#141210` | Text on light surfaces |

### Accent System — Lapis

Lapis owns all interactive and structural chrome.

| Token | Value | Role |
|-------|-------|------|
| `--color-lapis` | `#3d6fa8` | Primary interactive (buttons, links, active nav) |
| `--color-lapis-light` | `#5585c0` | Hover state |
| `--color-lapis-dim` | `#2a4d78` | Pressed state |
| `--color-lapis-subtle` | `rgba(61,111,168,0.12)` | Active row tint, selected background |
| `--color-lapis-20` | `rgba(61,111,168,0.20)` | Focus tint |

### Accent System — Clay

Clay owns all content, data display, and signal highlighting.

| Token | Value | Role |
|-------|-------|------|
| `--color-clay` | `#c19a6b` | Secondary accent, ATF token hover, inline citations |
| `--color-clay-light` | `#d4b080` | Clay hover/emphasis |
| `--color-clay-subtle` | `rgba(193,154,107,0.12)` | Token highlight tint |
| `--color-clay-20` | `rgba(193,154,107,0.20)` | Selected token tint |
| `--color-gold` | `#c9a962` | Accent gold — bookmarks, starred items, premium actions |
| `--color-gold-subtle` | `rgba(201,169,98,0.15)` | Gold highlight |

### Language Colors

| Token | Value | Role |
|-------|-------|------|
| `--color-lang-sux` | `#7eb8a0` | Sumerian — muted jade |
| `--color-lang-akk` | `#b89a7e` | Akkadian — warm clay |
| `--color-lang-sux-tint` | `rgba(126,184,160,0.15)` | Sumerian line bg |
| `--color-lang-akk-tint` | `rgba(184,154,126,0.15)` | Akkadian line bg |

### Semantic Colors (WCAG AA at all surface levels verified)

| Token | Value | Role |
|-------|-------|------|
| `--color-success` | `#5d8a5d` | Pipeline complete, positive states |
| `--color-success-text` | `#a8d4a8` | Success text on dark bg |
| `--color-warning` | `#c9a040` | Incomplete pipeline, caution |
| `--color-warning-text` | `#e8cb80` | Warning text |
| `--color-error` | `#a84848` | Error, destructive |
| `--color-error-text` | `#e8a0a0` | Error text |
| `--color-info` | `#4a7a9e` | Info, neutral message |
| `--color-info-text` | `#9ac0dc` | Info text |

---

## Typography

**Typeface pair:** Space Grotesk (structure/UI) + Source Serif 4 (body/ATF/reading)

The geometric sans provides precision and legibility for UI chrome. The humanist serif carries the scholarly weight of long texts and ATF transliterations.

```css
--font-ui: 'Space Grotesk', system-ui, sans-serif;
--font-body: 'Source Serif 4', 'Palatino', serif;
--font-mono: 'Berkeley Mono', 'Cascadia Code', monospace;
--font-cuneiform: 'Noto Sans Cuneiform', serif;
```

**Google Fonts load:** `Space+Grotesk:wght@400;500;600;700&Source+Serif+4:ital,opsz,wght@0,8..60,300..900;1,8..60,300..900`

### Scale

```css
--text-2xs:  0.6875rem;  /* 11px — badges, fine labels */
--text-xs:   0.75rem;    /* 12px — secondary labels */
--text-sm:   0.875rem;   /* 14px — metadata, sidebar content */
--text-base: 1rem;       /* 16px — body, UI default */
--text-lg:   1.125rem;   /* 18px — emphasized body */
--text-xl:   1.25rem;    /* 20px — card titles, sidebar headers */
--text-2xl:  1.5rem;     /* 24px — section headings */
--text-3xl:  1.875rem;   /* 30px — page headings */
--text-4xl:  2.5rem;     /* 40px — display */
--text-mono: 0.9375rem;  /* 15px — ATF monospace default */
```

### ATF-Specific Typography

The ATF viewer uses the monospace stack at a larger optical size. Cuneiform Unicode renders at a stepped-up size with wider line height for sign legibility.

```css
.atf-line {
  font-family: var(--font-mono);
  font-size: var(--text-mono);
  line-height: 1.9;  /* generous for interlinear annotations */
  letter-spacing: 0.01em;
}

.atf-sign {
  font-family: var(--font-cuneiform);
  font-size: 1.4em;
  vertical-align: -0.15em;
}
```

---

## Depth System

The core differentiator of this concept. Three mechanisms create depth together:

### 1. Background Value Stepping

```css
/* Each level is ~6% lighter in perceived lightness */
--bg-l0: #141210;   /* bedrock */
--bg-l1: #1a1714;   /* deep panel */
--bg-l2: #211d19;   /* surface */
--bg-l3: #2c271f;   /* elevated */
--bg-l4: #352f26;   /* top (popovers) */
```

### 2. Inset vs. Raised Shadow

```css
/* Inset — resting, passive elements (inputs, code blocks, image viewports) */
--shadow-inset-sm: inset 0 1px 3px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(0,0,0,0.3);
--shadow-inset-md: inset 0 2px 6px rgba(0,0,0,0.6), inset 0 0 0 1px rgba(0,0,0,0.35);

/* Raised — interactive, actionable elements */
--shadow-raised-sm: 0 1px 2px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04);
--shadow-raised-md: 0 2px 6px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.05) inset;
--shadow-raised-lg: 0 6px 16px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.06) inset;

/* Floating — dialogs, dropdowns */
--shadow-float: 0 16px 40px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.06);

/* Glow (lapis) — focus, active primary */
--shadow-glow-lapis: 0 0 0 3px rgba(61,111,168,0.35);

/* Glow (clay) — focused token in ATF */
--shadow-glow-clay: 0 0 0 2px rgba(193,154,107,0.4);
```

### 3. Top Highlight Edge

Interactive raised surfaces have a hairline top edge highlight (simulates light from above):

```css
.btn, .card--raised {
  box-shadow: var(--shadow-raised-md);
  border-top: 1px solid rgba(255,255,255,0.08);
}
```

---

## Spacing & Layout

8px base grid throughout. No deviation.

```css
--space-1:  0.25rem;   /* 4px */
--space-2:  0.5rem;    /* 8px */
--space-3:  0.75rem;   /* 12px */
--space-4:  1rem;      /* 16px */
--space-5:  1.25rem;   /* 20px */
--space-6:  1.5rem;    /* 24px */
--space-8:  2rem;      /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
```

### Border Radius

Sharp-dominant. Rounding is used only for data chips/badges, not structure.

```css
--radius-none: 0;
--radius-xs:   2px;   /* inputs, buttons */
--radius-sm:   4px;   /* cards, panels */
--radius-md:   6px;   /* dialogs */
--radius-pill: 9999px; /* only for pill badges — used sparingly */
```

---

## Animation

Physics metaphor: **objects settle under gravity.** Things fall into place, don't bounce out of it.

```css
--ease-settle:    cubic-bezier(0.22, 1, 0.36, 1);   /* decelerates hard — feels heavy landing */
--ease-lift:      cubic-bezier(0.4, 0, 0.6, 1);     /* symmetrical — for hover raises */
--ease-snap:      cubic-bezier(0.16, 1, 0.3, 1);    /* fast decelerate — panel opens */

--duration-instant: 80ms;
--duration-fast:    150ms;
--duration-base:    250ms;
--duration-slow:    400ms;
--duration-panel:   320ms;  /* sidebar slide */
```

### Signature Motions

**Pressed button:** `transform: translateY(1px)` + shadow collapse over 80ms. Feels like pressing a physical key.

**Sidebar reveal:** slides from right with `transform: translateX(100%) → 0` + simultaneous fade. 320ms `ease-snap`.

**Token hover in ATF:** background tint fades in over 120ms `ease-lift`, clay glow appears at 150ms.

**Pipeline step completion:** filled circle scales from 0.6 → 1.0 over 250ms `ease-settle` with a subtle clay glow pulse.

---

## Form Controls

### Text Input

```
┌─────────────────────────────────────────┐  ← 1px border (--color-border)
│                                         │  ← bg: --bg-l0 (inset into surface)
│  value text                             │  inset shadow creates well
│                                         │
└─────────────────────────────────────────┘
```

States:
- **Default:** `bg: var(--color-bg)`, `border: var(--color-border)`, `box-shadow: var(--shadow-inset-sm)`
- **Hover:** border lightens to `--color-border-raised`
- **Focus:** border becomes `--color-border-focus` (lapis), `box-shadow: var(--shadow-glow-lapis)`
- **Filled:** no visual change — letting content speak
- **Error:** border `--color-error-text`, error glow `0 0 0 3px rgba(168,72,72,0.3)`
- **Disabled:** `opacity: 0.45`, `cursor: not-allowed`

```css
.input {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  box-shadow: var(--shadow-inset-sm);
  color: var(--color-text);
  font-family: var(--font-ui);
  font-size: var(--text-base);
  padding: var(--space-3) var(--space-4);
  transition: border-color var(--duration-fast) var(--ease-lift),
              box-shadow var(--duration-fast) var(--ease-lift);
}
.input:focus {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-inset-sm), var(--shadow-glow-lapis);
  outline: none;
}
```

### Textarea

Same as input. Line height `1.6` for comfortable multiline. `resize: vertical` only.

Variant: **ATF input** — monospace font stack, slightly larger padding, deeper inset shadow to signal scholarly content area.

### Select / Combobox

Custom-styled. Chevron icon replaces native arrow.

States match text input. Open state: dropdown panel is `--bg-l4` with `--shadow-float`, slides down 4px over `150ms ease-snap`.

Option hover: `bg: var(--color-lapis-subtle)`.
Selected option: bold text + check mark in lapis color.

### Multi-Select (Filter Chips)

Used in dictionary sidebar and search.

```
[× Akkadian]  [× Noun]  [+ Add filter]
```

Active chips: `bg: var(--color-lapis-subtle)`, `border: 1px solid var(--color-lapis)`, lapis text, `border-radius: var(--radius-xs)`.

### Checkbox

Custom square. No border-radius. 16×16px.

- Unchecked: `bg: var(--color-bg)`, inset shadow, 1px border
- Checked: `bg: var(--color-lapis)`, white check SVG, border matches bg
- Indeterminate: `bg: var(--color-bg)`, lapis dash
- Focus: lapis glow ring

### Radio

18×18px circle (only form element that uses full-radius — because it's semantically a radio, not a button).

- Unselected: inset shadow, 1px border
- Selected: outer ring in lapis + filled inner dot (8px) in white

### Toggle Switch

32×18px pill. The one use of full-radius on this element class.

- Off: `bg: var(--color-bg-elevated)`, thumb is `--color-text-muted`
- On: `bg: var(--color-lapis)`, thumb slides right (150ms), thumb is white
- Thumb has `--shadow-raised-sm` for tactile weight

### Range Slider

Track is inset (well). Thumb is raised (pill shaped, 18px wide, 18px tall).

- Track: `bg: var(--color-bg)`, inset shadow, lapis filled portion left of thumb
- Thumb: lapis background, white border, raised shadow. On drag: slightly larger (20px)

### File Upload

Dashed border zone, 2px dash. On drag-over: border becomes solid lapis, bg gets lapis subtle tint.

```
┌  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ┐
│                                          │
│    ↑  Drop files here or Browse          │
│                                          │
└  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─  ┘
```

### Search Input

Has inline magnifier icon on left, × clear on right when filled. Slightly wider padding-left to accommodate icon.

Variant: **Global search** (header) — full-width, 44px height, monospace font for P-number/Q-number entry.

### Date / Date Range

Custom picker using native `<input type="date">` styled to match system. Range has two inputs with a dash separator.

---

## Button System

### Primary (Lapis)

```
[   Save Changes   ]   ← raised, lapis bg, white text
```

- `bg: var(--color-lapis)`, `color: white`, `border-radius: var(--radius-xs)`
- Hover: `bg: var(--color-lapis-light)`, `transform: translateY(-1px)`, shadow lifts
- Active: `transform: translateY(1px)`, shadow flattens (pressed feel)
- Focus: lapis glow ring outside button

### Secondary (Ghost)

```
[   Cancel   ]   ← no fill, lapis border + text
```

- `bg: transparent`, `border: 1px solid var(--color-lapis)`, `color: var(--color-lapis)`
- Hover: `bg: var(--color-lapis-subtle)`

### Destructive

```
[   Delete Entry   ]   ← error-derived background
```

- `bg: var(--color-error)`, white text

### Icon Button

Square, same padding on all sides. Used for toolbar actions (bookmark, zoom, actions menu).

Variants: `--icon-sm` (28px), `--icon-md` (36px), `--icon-lg` (44px)

### Split Button

Primary action + chevron dropdown separator. Used for "Run Connector" (run now vs. schedule).

### Button Group

Segmented control for tab-like selection at component level. No border-radius on internal buttons, only on group ends.

```
[ Text ] [ Transliteration ] [ Translation ]
```

---

## Key UI Components

### ATF Viewer

The signature experience. Full dark-mode, deep excavation feel.

```
┌──────────────────────────────────────────────────────┐
│  bg: --bg-l0 (bedrock)                               │
│  padding: generous (48px sides, 32px top)            │
│                                                      │
│  &obv. 1.  [i₃][gara₂][ba][na][sum]                 │
│               ↑ token — clay tint on hover           │
│  &obv. 2.  [lugal][u₃][nin]                          │
│                                                      │
│  § Translation                                       │
│  "The butter was given to him..."                    │
└──────────────────────────────────────────────────────┘
```

- Panel background: `--color-bg` (absolute deepest)
- Line numbers: `--color-text-muted`, right-aligned in fixed-width column
- Tokens: hover gets `bg: var(--color-clay-subtle)`, 2px clay glow, cursor pointer
- Selected token: `bg: var(--color-clay-20)`, clay glow persists
- Language stripe: left border 2px, color matches language token
- Damage markers (`[...]`): `color: --color-text-muted`, italic
- Determinatives: superscript, `color: --color-text-secondary`, slightly smaller

### Knowledge Sidebar

Slides from right. Icon nav is a vertical rail at the far right edge (40px wide). Content panel is 320px, slides left of the rail.

- Rail: `bg: --color-bg-deep`, icons are `--color-text-muted` default, `--color-clay` when active
- Content panel: `bg: --color-bg-surface`, lapis left border when open
- Header: uppercase label in `--color-text-muted` (Space Grotesk, 11px, 0.08em letter-spacing)
- Tabs animate: active indicator is 2px lapis line under tab text

### Pipeline Indicator

Shows data completeness across stages. Compact version in tablet header, detailed in connector detail.

```
● ─── ● ─── ● ─── ○   (filled dot = complete, empty = incomplete)
ATF   OCR   NLP   IMG
```

- Complete dot: `--color-success` filled, thin `--color-bg-deep` ring separating from line
- Incomplete dot: `--color-border` border, transparent fill
- Active (running): pulsing clay glow, 1.5s ease-in-out infinite
- Connector lines: `--color-border` default, `--color-success` fill animates left to right on completion

### Navigation Header

60px height. Lapis border-bottom (1px). Logo mark in clay/gold.

Nav items: uppercase, 11px, 0.1em letter-spacing (Space Grotesk). Hover: clay underline slides in from left over 150ms.

Active: persistent clay underline, text at full `--color-text` instead of muted.

### Tablet Card (List View)

Raised card on `--bg-l2`. Top-right: pipeline compact indicator. Bottom: language badge.

Hover: card lifts 2px, shadow strengthens. Transition 200ms ease-settle.

Selected/active: lapis left border 3px, bg shifts to `--color-bg-elevated`.

### Badges

Language, POS, status. Sharp corners (`--radius-xs`). Inset-style: `bg` is a subtle tint of the semantic color, text is the full semantic color.

```css
.badge--sux   { background: var(--color-lang-sux-tint);  color: var(--color-lang-sux); }
.badge--akk   { background: var(--color-lang-akk-tint);  color: var(--color-lang-akk); }
.badge--noun  { background: var(--color-lapis-subtle);   color: var(--color-lapis-light); }
.badge--success { background: rgba(93,138,93,0.15);     color: var(--color-success-text); }
```

### Data Tables

- Header: `bg: --color-bg-deep`, small caps labels, `--color-text-muted`
- Row hover: `bg: --color-lapis-subtle`
- Selected row: persistent lapis subtle bg + 2px left lapis border
- Sorted column: header chevron in lapis, column cells slightly lighter
- Zebra striping: **not used** — hover + border system handles scanability

### Modal / Dialog

- Backdrop: `rgba(0,0,0,0.6)` with subtle blur `backdrop-filter: blur(4px)`
- Dialog: `bg: --color-bg-top`, `box-shadow: --shadow-float`, `border-radius: --radius-md`
- Enters: scale from 0.96 + fade in over 250ms ease-settle
- Title: Space Grotesk, 18px, semibold
- Destructive dialog: thin error-color top border on dialog

### Toast / Notification

Bottom-right, slides up from bottom. 4px corner (not pill). Icon + text. Auto-dismiss with shrinking timer line at bottom.

### Empty States

Centered in their container. Icon (large, `--color-text-muted`) above heading above body text above optional CTA. Never cutesy — always purposeful.

### Skeleton Loading

Animated shimmer. Bg: subtle gradient cycling from `--color-bg-elevated` to `--color-bg-top` and back. Duration: 1.5s, ease-in-out infinite.

---

## Accessibility

- All text/bg combinations target WCAG AA (4.5:1 for normal text, 3:1 for large)
- Focus indicators: lapis glow ring — always visible, never hidden
- Keyboard nav: full tab order, roving tabindex for icon nav rail
- `prefers-reduced-motion`: all transitions reduced to `opacity` only, no transforms
- Color is never the *only* indicator: pipeline uses icon + label in addition to color

---

## What Makes This Distinctly This Concept

This is the only concept that:
- Uses an **inset/raised duality** as its primary tactile system (not flat)
- Has **two accent colors with explicit domain ownership** (lapis = structure, clay = content)
- Reads as **warm and dark** — feels like late-night excavation report work
- Typography uses a **serif for body and ATF** — the humanist serif gives academic weight
