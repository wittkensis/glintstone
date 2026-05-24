---
title: "Design System Concept 3 — Instrument Panel"
subtitle: "Dark Precision Instrument"
status: draft
created: 2026-05-22
---

# Concept 3 — Instrument Panel

**Tagline:** *A research instrument. Every surface signals purpose.*

**Feeling:** A high-end scientific instrument control suite — think radio telescope console, magnetometer readout, or advanced academic workstation software (think JSTOR reimagined by aerospace engineers). Cool dark. Grid-structure visible. Phosphor-amber displays for active data. Everything is deliberate, measured, calibrated.

**Target mood:** NASA mission control married to a mid-century precision instrument maker. Academic rigour expressed through system design.

---

## Design Principles

1. **Visible structure, invisible chrome.** Grid lines and panel borders *are* the UI. No decorative backgrounds — structural lines do all the work.
2. **Phosphor warmth in cool dark.** The background is a desaturated cool-dark, but active/interactive elements use a warm amber phosphor glow. Like an instrument needle catching light.
3. **Two temperature zones.** Cool neutral = structure, data, passive chrome. Warm amber = signal, interaction, alert.
4. **Monospace as first-class.** ATF, code, IDs, numbers — monospace is not an exception. It's a native typeface in this system.
5. **Everything grid-aligned.** 8px grid enforced with a 1px hairline grid overlay in deep panels. Not literal gridlines — but spacing is so consistent it reads as one.

---

## Color System

### Base Palette

| Token | Value | Role |
|-------|-------|------|
| `--color-bg` | `#111418` | Instrument chassis — deepest bg, deepest panels |
| `--color-bg-deep` | `#161b21` | Deep panel bg — sidebars, ATF well |
| `--color-bg-surface` | `#1d242d` | Working surface — main content area |
| `--color-bg-elevated` | `#242d38` | Raised panel — cards, active panes |
| `--color-bg-top` | `#2c3645` | Topmost — popovers, dialogs |
| `--color-border-deep` | `#131921` | Hairline in deepest context |
| `--color-border` | `#2a3340` | Panel border — structural grid lines |
| `--color-border-raised` | `#38475a` | Border on elevated elements |
| `--color-border-bright` | `#4a5e78` | Highlighted border — active containers |
| `--color-border-focus` | `#c9920a` | Focus ring — amber |

### Text

| Token | Value | Role |
|-------|-------|------|
| `--color-text` | `#d8e0e8` | Primary text — cool white with blue tint |
| `--color-text-secondary` | `#8a9aaa` | Secondary — instrument labels |
| `--color-text-muted` | `#5a6878` | Muted — structural labels, line numbers |
| `--color-text-disabled` | `#3a4858` | Disabled |
| `--color-text-amber` | `#e8a830` | Amber display text — active values, live readings |
| `--color-text-link` | `#6b97c4` | Link — desaturated blue |

### Signal System — Amber (Phosphor)

Amber is the single warm accent. It signals active state, interaction, and live data.

| Token | Value | Role |
|-------|-------|------|
| `--color-amber` | `#c9920a` | Primary signal (active, interactive, focus) |
| `--color-amber-bright` | `#e8a830` | Bright amber — display values, reading out |
| `--color-amber-dim` | `#8a6108` | Dim amber — pressed state |
| `--color-amber-subtle` | `rgba(201,146,10,0.12)` | Amber tint — hover bg, selected row |
| `--color-amber-20` | `rgba(201,146,10,0.20)` | Focus tint |
| `--color-amber-glow` | `rgba(201,146,10,0.30)` | Glow effect — focus rings, active indicators |

### Signal System — Instrument Blue

Blue is cool-data. Read-only displays, informational states, ATF token language indicators.

| Token | Value | Role |
|-------|-------|------|
| `--color-signal-blue` | `#4a7aaa` | Data display blue |
| `--color-signal-blue-bright` | `#6b97c4` | Bright data blue |
| `--color-signal-blue-subtle` | `rgba(74,122,170,0.12)` | Blue tint |

### Signal System — Instrument Green

Green is completion/health. Pipeline indicators, successful ingestion, healthy system state.

| Token | Value | Role |
|-------|-------|------|
| `--color-signal-green` | `#3a7a52` | System healthy, complete |
| `--color-signal-green-bright` | `#5a9e72` | Bright success indicator |
| `--color-signal-green-subtle` | `rgba(58,122,82,0.15)` | Success bg |

### Language Colors (instrument-appropriate)

| Token | Value | Role |
|-------|-------|------|
| `--color-lang-sux` | `#5a9e88` | Sumerian — cool teal |
| `--color-lang-akk` | `#c9920a` | Akkadian — reuses amber (warm vs. cool) |
| `--color-lang-sux-tint` | `rgba(90,158,136,0.15)` | Sumerian line bg |
| `--color-lang-akk-tint` | `rgba(201,146,10,0.10)` | Akkadian line bg |

### Semantic Colors

| Token | Value | Role |
|-------|-------|------|
| `--color-success` | `var(--color-signal-green)` | Complete state |
| `--color-success-text` | `var(--color-signal-green-bright)` | Success text |
| `--color-warning` | `#aa7808` | Warning — amber variant, darker |
| `--color-warning-text` | `#e8a830` | Warning text |
| `--color-error` | `#a83838` | Error — desaturated red |
| `--color-error-text` | `#e09090` | Error text |
| `--color-info` | `var(--color-signal-blue)` | Info |
| `--color-info-text` | `var(--color-signal-blue-bright)` | Info text |

---

## Typography

**Typeface pair:** Geist (headings/UI) + Geist Mono (data/ATF/IDs)

Geist is Vercel's type system — precise, technical, humanist enough to be readable. Geist Mono is its monospace sibling. Using both from the same family creates total visual coherence. In this concept, monospace is promoted to equal standing with proportional type — it's not a code font, it's *the data font*.

```css
--font-ui: 'Geist', system-ui, sans-serif;
--font-data: 'Geist Mono', 'Berkeley Mono', monospace;
--font-cuneiform: 'Noto Sans Cuneiform', serif;
```

**Load:** Geist and Geist Mono from GitHub or self-hosted. (Google Fonts fallback: `DM Sans` + `DM Mono`.)

### Scale

Same numerical scale, different optical weight due to the typeface and cool dark rendering.

```css
--text-2xs:  0.6875rem;  /* 11px */
--text-xs:   0.75rem;    /* 12px — instrument labels */
--text-sm:   0.875rem;   /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg:   1.125rem;   /* 18px */
--text-xl:   1.25rem;    /* 20px */
--text-2xl:  1.5rem;     /* 24px */
--text-3xl:  1.875rem;   /* 30px */
--text-mono: 0.9375rem;  /* 15px — ATF base */
```

### Instrument Label Style

Structural labels use Geist Mono, all-caps, wide letter-spacing. Like panel labels on a scientific instrument.

```css
.instrument-label {
  font-family: var(--font-data);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}
```

### ATF Typography

Geist Mono at full size. ATF tokens look like data — this is appropriate because they *are* data.

```css
.atf-line {
  font-family: var(--font-data);
  font-size: var(--text-mono);
  line-height: 1.85;
  color: var(--color-text);
}
.atf-sign {
  font-family: var(--font-cuneiform);
  font-size: 1.35em;
  vertical-align: -0.1em;
}
.atf-token:hover {
  color: var(--color-text-amber);
}
```

---

## Depth System

Depth via structural lines, not shadows. Five methods:

### 1. Panel Border System

Every surface separation is a 1px `--color-border`. No thick borders — hairlines only, except focus rings.

```css
/* Panel inset well */
.panel--inset {
  background: var(--color-bg-deep);
  border: 1px solid var(--color-border);
}

/* Active panel */
.panel--active {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-bright);
  border-top: 1px solid var(--color-amber-glow);  /* amber top edge = active */
}
```

### 2. Subtle Gradient on Elevated Surfaces

Very subtle gradient — top edge slightly lighter, creates instrument-panel bevel feel without being visible at normal viewing.

```css
.card {
  background: linear-gradient(
    180deg,
    var(--color-bg-elevated) 0%,
    color-mix(in srgb, var(--color-bg-elevated) 95%, var(--color-bg) 5%) 100%
  );
}
```

### 3. Amber Top-Edge Rule on Active Elements

When an element is in active state (focused, selected, processing), it gains an amber top-border hairline.

```css
.panel--active, .input:focus, .card--selected {
  border-top-color: var(--color-amber);
}
```

### 4. Shadow Values (Precise, Not Atmospheric)

```css
--shadow-panel: 0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px var(--color-border);
--shadow-raised: 0 2px 6px rgba(0,0,0,0.5), 0 0 0 1px var(--color-border-raised);
--shadow-float: 0 8px 20px rgba(0,0,0,0.6), 0 0 0 1px var(--color-border-raised);
--shadow-glow-amber: 0 0 0 2px var(--color-amber), 0 0 8px rgba(201,146,10,0.4);
--shadow-glow-blue: 0 0 0 2px var(--color-signal-blue), 0 0 6px rgba(74,122,170,0.3);
```

### 5. Scan Line Overlay (ATF Panel Only)

The ATF viewer gets a subtle CSS scan-line texture — extremely faint horizontal lines every 2px, emulating an instrument CRT readout. Opacity 2%, barely visible, adds analogue character.

```css
.atf-panel::after {
  content: '';
  position: absolute; inset: 0;
  background: repeating-linear-gradient(
    to bottom,
    rgba(255,255,255,0.01) 0px,
    rgba(255,255,255,0.01) 1px,
    transparent 1px,
    transparent 2px
  );
  pointer-events: none;
}
```

---

## Spacing & Layout

Same 8px grid. Border radius system is the sharpest of the three concepts — instruments don't have rounded corners.

```css
--radius-none: 0;        /* preferred for panels, buttons */
--radius-xs:   2px;      /* only for inputs, tokens */
--radius-sm:   3px;      /* cards, minor elements */
--radius-md:   4px;      /* dialogs, dropdowns */
--radius-pill: 9999px;   /* explicitly avoided */
```

No pill buttons. No pill inputs. If a component is naturally pill-shaped (range slider thumb), document the exception.

---

## Animation

Physics metaphor: **instrument needles, meters, signal readouts.** Fast snaps, smooth sweeps, no bounce.

```css
--ease-sweep:    cubic-bezier(0.4, 0, 0.2, 1);   /* smooth sweep — meters, progress */
--ease-snap:     cubic-bezier(0.16, 1, 0.3, 1);  /* fast snap — panel opens, dropdown */
--ease-linear:   linear;                          /* linear — scanners, progress bars */

--duration-instant: 60ms;   /* faster than other concepts — instrument precision */
--duration-fast:    120ms;
--duration-base:    200ms;
--duration-slow:    350ms;
--duration-sweep:   500ms;  /* meter sweeps */
```

### Signature Motions

**Button press:** amber glow pulses once (200ms, 0 → glow → 0). No transform. Like pressing a control panel key with LED feedback.

**Sidebar open:** snaps in at 200ms, amber top-edge border appears simultaneously.

**ATF token hover:** token text color transitions to amber-bright over 80ms. Monospace text glows faintly.

**Pipeline progress:** gauge fills left-to-right with a linear sweep animation. Color transitions from blue (partial) through amber (running) to green (complete).

**Focus appearance:** amber glow ring expands from 0px to 2px over 100ms. Stays while focused.

**Loading state:** amber dots pulse left to right (not a spinner — a sweep, like radar).

---

## Form Controls

### Text Input

```
┌─────────────────────────────────────────┐  ← 1px --color-border
│                                         │  ← bg: --color-bg-deep
│  value text                             │  deep bg = instrument display well
│                                         │
└─────────────────────────────────────────┘
```

All inputs use a **display-well** pattern — deep inset bg (`--color-bg-deep`) inside the container surface. This is consistent with the instrument readout metaphor: data appears in a slightly darker well.

States:
- **Default:** `bg: var(--color-bg-deep)`, 1px border `--color-border`, no shadow
- **Hover:** border brightens to `--color-border-bright`
- **Focus:** amber top-border (1px), amber glow ring, border-top `--color-amber`
- **Filled:** text displays in `--color-text` — monospace when appropriate (IDs, numbers)
- **Error:** red border, red glow
- **Disabled:** `opacity: 0.35`

```css
.input {
  background: var(--color-bg-deep);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  color: var(--color-text);
  font-family: var(--font-ui);
  font-size: var(--text-base);
  padding: var(--space-3) var(--space-4);
  transition: border-color var(--duration-fast) var(--ease-sweep),
              box-shadow var(--duration-fast) var(--ease-sweep);
}
.input:focus {
  border-top-color: var(--color-amber);
  box-shadow: var(--shadow-glow-amber);
  outline: none;
}

/* Monospace variant — IDs, accession numbers, search by P-number */
.input--mono {
  font-family: var(--font-data);
  font-size: var(--text-sm);
  letter-spacing: 0.02em;
}
```

### Textarea

Same display-well style. `min-height: 120px`. `resize: vertical`. Monospace variant for ATF input.

### Select

Dark dropdown. Chevron icon in muted color. Open state: dropdown panel is `--bg-top`, 1px border, `--shadow-float`. Option hover: amber subtle tint. Selected: amber text + check.

### Multi-Select / Tag Input

```
[P000123 ×]  [Ur III ×]  [Akk ×]  [+ Add]
```

Tags: `bg: --color-bg-elevated`, `border: 1px solid --color-border-raised`, `--radius-xs`. Active/focused tag: amber border.

### Checkbox

Sharp square (0px radius). 15×15px. Instrument-panel style.

- Unchecked: `bg: --color-bg-deep`, 1px border
- Checked: amber bg, white check-mark, amber border
- Focus: amber glow ring

### Radio

16×16, square (not circle). This is an intentional departure — in an instrument panel metaphor, selection indicators are square indicator lights, not pills.

- Unselected: `bg: --color-bg-deep`, 1px border
- Selected: amber filled square with white 6px inner square

### Toggle Switch

32×16px. Sharp corners (0px radius on the track). Thumb is 12×12px square.

- Off: muted bg, muted thumb
- On: amber track, white thumb slides to right
- Transition: 150ms linear (instrument toggle, not elastic)

### Range Slider

Track: 3px height, dark well. Filled portion: amber. Thumb: square (8px), amber bg, no border-radius.

Drag: amber glow extends from thumb horizontally — like an instrument needle with glow tail.

### File Upload

Border style: 1px dashed `--color-border`. Monospace instrument label at center. On drag: border becomes solid amber, bg gets amber subtle tint.

### Search Input

Full-width in header. `--font-data` monospace by default (ATF IDs, lemmas, P-numbers). Magnifier icon on left in amber color. Results dropdown: instrument panel style.

### Date Input

Styled native + custom. Monospace for date values. Calendar popup uses instrument panel aesthetic.

---

## Button System

### Primary (Amber)

```
[ SAVE CHANGES ]   ← uppercase, monospace, amber text or amber bg
```

Variant A (Outline): `bg: transparent`, `border: 1px solid var(--color-amber)`, `color: var(--color-text-amber)`. Hover: `bg: var(--color-amber-subtle)`.

Variant B (Filled): `bg: var(--color-amber)`, `color: #111418` (dark text on amber).

Primary uses Variant A by default — instrument panels favor outline indicators over solid-filled controls.

### Secondary (Blue)

```
[ VIEW SOURCE ]   ← blue outline, used for informational actions
```

- `border: 1px solid var(--color-signal-blue)`, `color: var(--color-signal-blue-bright)`

### Destructive

```
[ DELETE ]   ← red border + red text (outline style)
```

- `border: 1px solid var(--color-error)`, `color: var(--color-error-text)`

### Ghost (Panel Chrome)

```
[ Filter ▾ ]   ← no border, muted text, used in toolbar
```

### Icon Button

Square, 0px radius. Amber on hover (glow). Standard sizes: 28px, 36px, 44px.

### Button Group

```
[ TEXT | TRANSLITERATION | TRANSLATION ]   ← monospace uppercase labels
```

Sharp corners, 1px amber border on wrapper. Active segment: amber bg, dark text.

### Indicator Button (Pipeline Control)

Special variant for pipeline run/stop/restart. Circular indicator dot (amber = running, green = complete) + text label.

```
● RUN CONNECTOR   ← amber dot pulses when running
```

---

## Key UI Components

### ATF Viewer

The showpiece. Instrument panel meets cuneiform research.

```
┌──────────────────────────────────────────────────────┐
│  bg: --color-bg (chassis)                            │
│  subtle scan-line overlay                            │
│                                                      │
│  OBVERSE  COL. I  ← instrument label style          │
│  ─────────────────────────────────────────           │
│                                                      │
│  001  [i₃][gara₂][ba][na][sum]                       │
│  ↑ amber on hover — token highlights in amber        │
│  002  [lugal][u₃][nin]                               │
│                                                      │
│  ──── TRANSLATION ────────────────────────           │
│  "The butter was given to him..."                    │
└──────────────────────────────────────────────────────┘
```

- Panel: deepest bg with scan-line overlay
- Section headers: Geist Mono, uppercase, muted, with full-width 1px rule
- Line numbers: right-aligned in fixed 4-char column, amber when line selected
- Tokens: amber text on hover, amber glow on selected
- Language left-border: 2px per language color

### Knowledge Sidebar

Opens with amber top-border appearing at panel edge. Icon rail is dark, icons muted by default, amber when active.

- Panel bg: `--color-bg-surface`
- Tab rail: horizontal row of Geist Mono uppercase labels. Active: amber underline.
- Content: monospace where appropriate (dictionary entries, IDs)

### Pipeline Indicator

This concept's pipeline is the most instrument-like:

```
[●]──[●]──[●]──[○]    PIPELINE  3/4  ████████████░░░░
ATF  OCR  NLP  IMG               ↑ amber progress gauge
```

Gauge fills with amber sweep animation. Complete segments turn green. The fraction reads in amber monospace.

Step dots are square (not circle), consistent with the instrument aesthetic.

### Navigation Header

60px. `bg: --color-bg` (deepest). Logo in amber or blue-white. Nav items in `--color-text-secondary`, Geist Mono uppercase. Active: amber left-border indicator (3px). Hover: text brightens.

### Tablet Card (List View)

`bg: --color-bg-elevated`. 1px border. No shadow — structure only.

Hover: amber top-border appears, border brightens overall.

Selected/active: persistent amber top-border + left amber 2px border.

P-number in Geist Mono. Period/provenience in muted text.

### Badges

Sharp corners. Monospace font. Outline style (bg tint + border + text).

```css
.badge { font-family: var(--font-data); border-radius: var(--radius-xs); }
.badge--sux    { background: var(--color-lang-sux-tint); border: 1px solid var(--color-lang-sux); color: var(--color-lang-sux); }
.badge--akk    { background: var(--color-lang-akk-tint); border: 1px solid var(--color-lang-akk); color: var(--color-lang-akk); }
.badge--active { background: var(--color-amber-subtle); border: 1px solid var(--color-amber); color: var(--color-text-amber); }
```

### Data Tables

- Header: `bg: --color-bg`, Geist Mono uppercase, `--color-text-muted`. Sortable header: amber chevron.
- Rows: `bg: --color-bg-surface`. No zebra — clean.
- Row hover: amber subtle tint
- Selected: amber left-border 2px + amber subtle bg
- Numerical values: right-aligned, monospace

### Modal / Dialog

- Backdrop: `rgba(0,0,0,0.65)` — no blur (instrument panels are always visible)
- Dialog: `bg: --color-bg-top`, 1px border `--color-border-raised`, amber top edge, 4px radius
- Title: Geist, uppercase letter-spacing
- Enters: slides down 8px + fade over 200ms ease-snap

### Toast / Notification

Bottom-right. `bg: --color-bg-top`, 1px border. Amber top-border for success (amber signal = operational). Red border for error. Small amber pulse dot as icon for active.

### Empty States

Geist Mono centered text. Instrument metaphor: "NO SIGNAL" style placeholder with measurement-grid style icon.

### Skeleton Loading

Amber sweep animation — a 20px-wide amber shimmer band sweeps left to right across the field. Feels like a radar sweep.

---

## Special: Annotation Diff Display

Glintstone stores competing interpretations. This concept handles the diff display best:

- Annotation runs are shown in stacked rows with a cool-blue tint
- The current/selected run gets an amber top-border
- Conflicting interpretations side-by-side: left panel blue-tinted, right panel amber-tinted
- Confidence scores: numeric display in Geist Mono, amber color for high confidence

---

## Accessibility

- All text/bg pairs: WCAG AA verified
  - Text `#d8e0e8` on `#1d242d`: 10.2:1 ✓
  - Amber `#c9920a` on `#1d242d`: 3.8:1 — amber used only for interactive/large elements ✓ (3:1 minimum for large text met)
  - Bright amber `#e8a830` on `#1d242d`: 6.1:1 ✓ for display values
  - Signal blue `#6b97c4` on `#1d242d`: 5.2:1 ✓
- Focus: amber glow ring, high contrast against dark surfaces
- Amber = interactive is reinforced by shape, position, and ARIA — color is not the sole indicator
- Monospace radio squares: `role="radio"`, `aria-checked` properly
- `prefers-reduced-motion`: all amber glow animations replaced with instant opacity toggle
- Scan-line overlay: `pointer-events: none`, `aria-hidden: true`

---

## What Makes This Distinctly This Concept

This is the only concept that:
- Has a **cool-dark base** (vs. warm-dark in Concept 1)
- Promotes **monospace to first-class typeface** alongside proportional
- Uses **amber as the sole warm signal** against a fully cool background — maximum signal-to-noise
- Has **square checkboxes and radio buttons** — instruments, not consumer UI
- Includes a **scan-line overlay** on the ATF panel
- The pipeline indicator reads like a **gauge/meter**, not a progress bar
- Has a **zero-pill-radius** policy — the only fully sharp-corner system of the three
