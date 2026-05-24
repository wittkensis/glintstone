---
title: "Design System Concept 2 — Scholar's Studio"
subtitle: "Ink on Stone"
status: draft
created: 2026-05-22
---

# Concept 2 — Scholar's Studio

**Tagline:** *The interface as a well-made academic archive. Clear, committed, ink on stone.*

**Feeling:** A museum conservation lab meets a beautifully typeset journal. Light-dominant. High contrast between text and paper. The UI has the confidence of printed matter — decisions feel permanent, not provisional. Academics will recognize this as belonging to their world without feeling like it's playing dress-up.

**Target mood:** Physical finding-aid cabinet + Penguin Books editorial discipline.

---

## Design Principles

1. **Print logic.** Hierarchy is achieved through typography weight, size, and spacing — not background colors. Color is a finishing coat, not the structure.
2. **Stone and ink.** Backgrounds are warm stone (not white); text is near-black ink. The contrast is high, the warmth prevents clinical coldness.
3. **Texture as depth.** Subtle noise/grain CSS patterns replace shadow stacks. Surfaces don't float — they rest.
4. **Ink-on-press buttons.** Buttons have a slight letterpress inset on active. Inputs have a pen-line underline instead of full box border.
5. **One red, used with discipline.** Iron red is the single high-energy accent. Used for danger, errors, and critical CTAs only. Everything else is ink, stone, or verdigris.

---

## Color System

### Base Palette

| Token | Value | Role |
|-------|-------|------|
| `--color-bg` | `#f2ece2` | Warm stone — main background |
| `--color-bg-deep` | `#e8e0d4` | Slightly cooler stone — inset panels, sidebars |
| `--color-bg-surface` | `#faf6f0` | Lighter stone — card surfaces, elevated |
| `--color-bg-elevated` | `#ffffff` | White surface — dialogs, active cards |
| `--color-bg-inverse` | `#1c1917` | Deep ink — inverse components, footer |
| `--color-border` | `#c8bfb2` | Stone seam — standard borders |
| `--color-border-light` | `#ddd6cc` | Lighter border — dividers |
| `--color-border-strong` | `#a09080` | Strong border — active states |
| `--color-border-ink` | `#1c1917` | Ink border — focus rings, strong dividers |

### Text

| Token | Value | Role |
|-------|-------|------|
| `--color-text` | `#1c1917` | Near-black ink |
| `--color-text-secondary` | `#4a4540` | Secondary ink — metadata |
| `--color-text-muted` | `#7a726a` | Muted ink — labels, placeholders |
| `--color-text-disabled` | `#b0a898` | Disabled |
| `--color-text-inverse` | `#f2ece2` | Text on inverse/dark surfaces |
| `--color-text-link` | `#1c4e7a` | Link — cool indigo, not electric |

### Accent System — Verdigris

Verdigris (green-blue patina) owns interactive elements. Scholar's tools are green — pencil marks, annotations, bookmarks.

| Token | Value | Role |
|-------|-------|------|
| `--color-verdigris` | `#2d6a5a` | Primary interactive (buttons, active nav, links alt) |
| `--color-verdigris-light` | `#3a8570` | Hover state |
| `--color-verdigris-dim` | `#1f4f42` | Pressed state |
| `--color-verdigris-subtle` | `rgba(45,106,90,0.08)` | Hover tint, selected bg |
| `--color-verdigris-20` | `rgba(45,106,90,0.18)` | Focus tint |
| `--color-verdigris-tint` | `#e8f4f0` | Very light tint — active row bg |

### Accent System — Iron Red

Single high-energy accent. Used precisely.

| Token | Value | Role |
|-------|-------|------|
| `--color-iron` | `#8b3a3a` | Danger, destructive, critical signal |
| `--color-iron-light` | `#a84848` | Hover on iron elements |
| `--color-iron-subtle` | `rgba(139,58,58,0.08)` | Error bg tint |
| `--color-iron-tint` | `#fdf0f0` | Error field bg |

### Scholarly Accent — Faded Gold

Gold is used only for editorial highlights: bookmarks, starred/featured items, "notable" badges.

| Token | Value | Role |
|-------|-------|------|
| `--color-gold` | `#9a7a3a` | Dark gold — saturated enough for light backgrounds |
| `--color-gold-subtle` | `rgba(154,122,58,0.12)` | Gold highlight tint |

### Language Colors (adapted for light bg)

| Token | Value | Role |
|-------|-------|------|
| `--color-lang-sux` | `#2a6b50` | Sumerian — darker jade for contrast on stone |
| `--color-lang-akk` | `#7a4a28` | Akkadian — burnt sienna |
| `--color-lang-sux-tint` | `rgba(42,107,80,0.08)` | Sumerian line bg |
| `--color-lang-akk-tint` | `rgba(122,74,40,0.08)` | Akkadian line bg |

### Semantic Colors (WCAG AA on light bg)

| Token | Value | Role |
|-------|-------|------|
| `--color-success` | `#2d6a4a` | Success (verdigris-adjacent) |
| `--color-success-bg` | `#e8f4ee` | Success bg |
| `--color-warning` | `#8a6020` | Warning amber |
| `--color-warning-bg` | `#fdf5e0` | Warning bg |
| `--color-error` | `#8b3a3a` | Error (iron red) |
| `--color-error-bg` | `var(--color-iron-tint)` | Error bg |
| `--color-info` | `#1c4e7a` | Info (indigo) |
| `--color-info-bg` | `#e8f0f8` | Info bg |

---

## Typography

**Typeface pair:** Instrument Serif (headings/ATF) + IBM Plex Sans (UI/labels/metadata)

Instrument Serif is the star — high quality open-source serif with beautiful italic. IBM Plex Sans is the functional counterpart: legible, slightly mechanical, excellent at small sizes and data-dense contexts.

```css
--font-heading: 'Instrument Serif', 'Georgia', serif;
--font-ui: 'IBM Plex Sans', system-ui, sans-serif;
--font-mono: 'IBM Plex Mono', monospace;
--font-cuneiform: 'Noto Sans Cuneiform', serif;
```

**Google Fonts load:** `Instrument+Serif:ital@0;1&IBM+Plex+Sans:wght@300;400;500;600&IBM+Plex+Mono`

### Scale

Same values as Concept 1, but different optical rhythm because of the serif/light theme pairing.

```css
--text-2xs:  0.6875rem;
--text-xs:   0.75rem;
--text-sm:   0.875rem;
--text-base: 1rem;
--text-lg:   1.125rem;
--text-xl:   1.25rem;
--text-2xl:  1.5rem;
--text-3xl:  1.875rem;
--text-4xl:  2.5rem;
--text-mono: 0.9375rem;
```

### Display Typography (Instrument Serif)

Large headings use Instrument Serif at normal weight — the letterform quality carries the hierarchy. Bold sparingly, reserved for H1s and key labels.

```css
h1 { font-family: var(--font-heading); font-size: var(--text-4xl); font-weight: 400; letter-spacing: -0.02em; }
h2 { font-family: var(--font-heading); font-size: var(--text-3xl); font-weight: 400; letter-spacing: -0.015em; }
h3 { font-family: var(--font-heading); font-size: var(--text-2xl); font-weight: 400; }
```

### ATF Typography

Monospace (IBM Plex Mono) on a warm bg. Slightly larger. The light theme makes the ATF lines feel like a typeset critical edition.

```css
.atf-line {
  font-family: var(--font-mono);
  font-size: var(--text-mono);
  line-height: 2.0;
  color: var(--color-text);
}
.atf-sign {
  font-family: var(--font-cuneiform);
  font-size: 1.5em;
  vertical-align: -0.2em;
}
```

---

## Depth System

No deep shadow stacks. Depth from three sources only:

### 1. Paper Grain Texture

A very subtle noise overlay on backgrounds. The effect is barely visible — just enough to break up flat digital fields and evoke physical paper.

```css
/* Applied via pseudo-element to bg-level surfaces */
.surface::before {
  content: '';
  position: absolute; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  background-size: 256px 256px;
  opacity: 0.04;
  pointer-events: none;
}
```

### 2. Border + Offset Separation

Cards on stone bg are separated by a 1px border and a 4px-8px box-shadow in the stone color (not black). The effect is a paper-lift without darkness.

```css
--shadow-paper: 0 2px 4px rgba(100,80,60,0.12), 0 0 0 1px var(--color-border);
--shadow-paper-lifted: 0 4px 12px rgba(100,80,60,0.18), 0 0 0 1px var(--color-border-strong);
--shadow-float: 0 8px 24px rgba(100,80,60,0.22), 0 0 0 1px var(--color-border-strong);
--shadow-glow-verdigris: 0 0 0 3px rgba(45,106,90,0.25);
--shadow-glow-iron: 0 0 0 3px rgba(139,58,58,0.25);
```

### 3. Stepped Background Values

Same principle as Concept 1 but in warm stone tones. The difference is subtle — felt more than seen.

---

## Spacing & Layout

Same 8px-base grid.

Border radius is **slightly more generous** than Concept 1 — the serif/editorial context allows a bit more softness without losing precision.

```css
--radius-none: 0;
--radius-xs:   2px;
--radius-sm:   4px;
--radius-md:   6px;
--radius-lg:   10px;
--radius-pill: 9999px;  /* sparingly — only pill badges */
```

---

## Animation

Physics metaphor: **pages turning, drawers opening.** Lateral movement (sidebar) feels like a filing cabinet drawer. Vertical movement (modals, dropdowns) feels like lifting paper.

```css
--ease-lift:   cubic-bezier(0.0, 0, 0.2, 1);    /* material entering */
--ease-drop:   cubic-bezier(0.4, 0, 1, 1);       /* material leaving */
--ease-stamp:  cubic-bezier(0.22, 1, 0.36, 1);   /* deliberate arrival */
--ease-page:   cubic-bezier(0.4, 0, 0.2, 1);     /* smooth lateral */

--duration-instant: 80ms;
--duration-fast:    150ms;
--duration-base:    240ms;
--duration-slow:    380ms;
--duration-drawer:  300ms;
```

### Signature Motions

**Drawer/sidebar:** 300ms ease-page lateral slide. Subtle paper-lift shadow strengthens as it opens.

**Modal enter:** scales in from 98% + fades. Very slight — more fade than scale. Feels like setting a sheet down.

**Button press:** very subtle `filter: brightness(0.92)` on active. No transform — letterpress metaphor (the element gets _pressed into_ the page, not toward you).

**Token hover in ATF:** warm underline line draws from left to right under token (2px, verdigris tint). 120ms left-to-right.

**Pipeline completion:** check mark draws in (SVG stroke-dashoffset animation), 300ms stamp ease.

---

## Form Controls

### Text Input — Underline Style (Signature)

This concept uses a bottom-border-only input. Not the Material 2014 trend — implemented with more authority.

```
  value text
______________________________________________   ← 2px bottom border, --color-border
```

- Default: `bg: transparent`, only bottom border in `--color-border`
- Hover: border darkens to `--color-border-strong`
- Focus: border becomes `--color-border-ink` (full black), verdigris glow *below* the line only
- Filled: no visual change
- Error: iron red bottom border, error glow below

Variant: **Box input** — used in search and filter contexts where the open underline could be confused. Same rules but full 1px border + `bg: var(--color-bg-elevated)`.

```css
.input--underline {
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--color-border);
  border-radius: 0;
  padding: var(--space-3) 0;
  color: var(--color-text);
  font-family: var(--font-ui);
}
.input--underline:focus {
  border-bottom-color: var(--color-text);
  box-shadow: 0 2px 0 -1px var(--color-verdigris-20);
  outline: none;
}
```

### Textarea

Box style (not underline — too much open edge). `bg: var(--color-bg-elevated)`, stone-border, verdigris focus.

### Select

Full box style. Native appearance replaced with IBM Plex Sans + custom chevron. Open: dropdown is `bg: --color-bg-elevated`, `--shadow-float`.

### Checkbox

Custom ink-box. 16×16, `--radius-xs`.

- Unchecked: `bg: --color-bg-elevated`, `border: 2px solid --color-border-strong`
- Checked: `bg: var(--color-verdigris)`, white check. Border becomes verdigris.
- Focus: verdigris glow ring

### Radio

18×18 circle. Same treatment — verdigris fill.

### Toggle Switch

28×16px. Off: stone bg, muted border. On: verdigris. Thumb is white circle.

### Range Slider

Track: 3px height, stone color, verdigris fill for completed portion. Thumb: white circle with ink border, verdigris shadow on drag.

### File Upload

Dashed box (2px ink-colored dash), centered content. On drag: dashes become solid, bg becomes verdigris-tint.

### Search

Box style. Icon on left. Full-width header variant has bottom-border-only on light stone bg.

---

## Button System

### Primary (Verdigris)

```
[   Save Changes   ]
```

- `bg: var(--color-verdigris)`, white text, `--radius-sm`
- Hover: `bg: var(--color-verdigris-light)`, `transform: translateY(-1px)`
- Active: `filter: brightness(0.9)`, no transform (letterpress feel)
- Focus: verdigris glow

### Secondary (Ink Outline)

```
[   Cancel   ]   ← ink-color border, ink text
```

- `bg: transparent`, `border: 2px solid var(--color-text)`, `color: var(--color-text)`
- Hover: `bg: rgba(0,0,0,0.04)`
- This is a strong, editorial choice — the button looks *printed*

### Tertiary (Text Link Button)

```
Cancel   ← no border, no bg, underline on hover
```

### Destructive (Iron Red)

```
[   Delete Entry   ]   ← iron red bg, white text
```

### Ghost (Subtle)

```
[   Filter   ]   ← stone bg, border, muted text
```

- Used for low-priority actions, filter controls

### Icon Button

Square. Verdigris on hover (bg tint). Standard sizes: 28px, 36px, 44px.

### Button Group (Segmented)

```
[ Text | Transliteration | Translation ]
```

Ink border wraps the group. Active segment: `bg: var(--color-verdigris)`, white text. Internal borders are 1px ink-color.

---

## Key UI Components

### ATF Viewer

Light theme makes the ATF feel like a typeset critical edition from a university press. Text is primary ink. Sign numbering is muted.

```
┌──────────────────────────────────────────────────────┐
│  bg: --color-bg (warm stone)                         │
│                                                      │
│  §obv. col. i                                        │
│                                                      │
│  1.  [i₃] [gara₂] [ba] [na] [sum]                   │
│         ↑ hover: verdigris underline draws in         │
│  2.  [lugal] [u₃] [nin]                              │
│                                                      │
│  § Translation                                       │
│  _"The butter was given to him..."_                  │
│  ↑ italic serif translation reads like a caption     │
└──────────────────────────────────────────────────────┘
```

- Line numbers: right-aligned, `--color-text-muted`, separated by a 1px border column
- Token hover: verdigris underline slide animation (left to right, 120ms)
- Selected token: `bg: var(--color-verdigris-tint)`, verdigris underline persists
- Damage notation: `color: --color-text-muted`, italic
- Determinatives: superscript, `color: --color-text-secondary`

### Knowledge Sidebar

Light panel. Opens as a side drawer from the right. Header has bottom border (2px ink), icon rail on far right uses ink-colored icons.

- Panel bg: `--color-bg-surface` (slightly lighter than main)
- Content width: 320px
- Tab strip: horizontal at top, active tab has 2px bottom border in verdigris
- Search input in sidebar: underline style

### Pipeline Indicator

```
● ─── ● ─── ● ─── ○
ATF   OCR   NLP   IMG
```

Complete: verdigris filled circles, ink connecting lines.
Incomplete: stone-colored circles with border, dashed lines.
Running: verdigris circle with spinning border segment.

Text labels: IBM Plex Sans, 11px, uppercase, 0.06em letter-spacing.

### Navigation Header

60px. `bg: --color-bg-inverse` (deep ink). Logo in warm stone color. Nav items in `--color-text-inverse` at 0.8 opacity. Hover: full opacity, verdigris underline.

Active: persistent verdigris underline, full opacity.

This is the one dark surface in an otherwise light system — creates strong visual contrast and grounds the chrome.

### Tablet Card (List View)

`bg: --color-bg-elevated` (white surface). `--shadow-paper`. Hover: `--shadow-paper-lifted`, subtle lift.

Header text: Instrument Serif for the P-number. Metadata: IBM Plex Sans, small, muted.

Pipeline indicator compact: right-aligned text fraction (e.g., "3/4 complete") in verdigris.

### Badges

Slightly more generous padding than Concept 1. Rounded to `--radius-sm`. Border + tint bg pattern.

```css
.badge--sux    { bg: var(--color-lang-sux-tint); border: 1px solid var(--color-lang-sux); color: var(--color-lang-sux); }
.badge--akk    { bg: var(--color-lang-akk-tint); border: 1px solid var(--color-lang-akk); color: var(--color-lang-akk); }
.badge--noun   { bg: var(--color-verdigris-subtle); border: 1px solid var(--color-verdigris); color: var(--color-verdigris); }
```

### Data Tables

- Header: `bg: --color-bg-deep`, IBM Plex Sans, small caps, `--color-text-muted`
- Row: white bg. Divider lines between rows (1px `--color-border-light`)
- Row hover: `bg: var(--color-verdigris-tint)` — very gentle
- Selected: `bg: var(--color-verdigris-subtle)`, 2px left border verdigris

### Modal / Dialog

- Backdrop: `rgba(28,25,23,0.5)` — ink-tinted
- Dialog: `bg: --color-bg-elevated` (white), `--shadow-float`, `--radius-md`
- Top rule: 1px `--color-border` line after header
- Enters: 98% scale + fade over 240ms ease-stamp

### Toast / Notification

Bottom-right. `bg: --color-bg-inverse` (dark). White text — inverse surface. Verdigris left border 3px for success. Iron left border for error.

### Empty States

IBM Plex Sans body text. Instrument Serif for heading. Line illustration (thin, ink color) above text.

### Skeleton Loading

Animated shimmer on `--color-bg-deep` surface. Stone shimmer (warm, not blue-gray).

---

## Light/Dark Mode Note

This concept is inherently **light-primary**. A dark mode variant exists but is secondary:

Dark mode swaps: bg-inverse becomes the base, stone colors invert, verdigris remains. The dark mode of Scholar's Studio looks like Concept 1 — intentional, since they share a color philosophy.

---

## Accessibility

- All text/bg combinations: WCAG AA minimum (4.5:1). Key pairs verified:
  - Ink `#1c1917` on stone `#f2ece2`: 17.8:1 ✓
  - Verdigris `#2d6a5a` on stone `#f2ece2`: 5.8:1 ✓ (large text exceeds AA for normal)
  - Verdigris `#2d6a5a` on white: 5.9:1 ✓
  - Iron `#8b3a3a` on white: 7.1:1 ✓
- Focus: verdigris glow ring, always visible on all surfaces
- `prefers-reduced-motion`: animation-free, opacity-only transitions
- Underline inputs: `aria-describedby` for error messages, not relying on color alone

---

## What Makes This Distinctly This Concept

This is the only concept that:
- Is **light-primary** — completely different reading environment from the dark concepts
- Uses an **underline input pattern** with editorial authority
- Leans on **Instrument Serif** as a structural typeface (most headings in serif)
- Has a **single red accent used only for danger** — maximum discipline in color usage
- The active header is **dark inverse** against a light body — strong print-media contrast
