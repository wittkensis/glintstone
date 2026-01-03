# Tablet Interaction Components

**Component Category:** Core
**Document Version:** 1.0

Tablet components handle the display of and interaction with cuneiform tablet images. These are the visual centerpiece of the Glintstone platform, enabling users to view ancient artifacts and contribute to their transcription.

**Design Principles:**
- Direct manipulation (pan, zoom, tap) for intuitive interaction
- Progressive disclosure of detail
- Immediate visual feedback for all interactions
- Clear affordances for interactive regions

---

## TabletViewer

### Purpose and Use Cases

TabletViewer displays a tablet image with pan/zoom capabilities and optional interactive region overlays. Use for:
- Main tablet viewing in task interfaces
- Review interfaces showing tablet + transcription
- Exploration/archive browsing
- Marketing hero displays

### Anatomy

```
+------------------------------------------+
|                              [Zoom Controls]
|                                    [-][o][+]
|  +--------------------------------+
|  |                                |
|  |                                |
|  |     [Tablet Image]             |
|  |                                |
|  |     +------+                   |
|  |     |Region|  <- Optional      |
|  |     +------+     overlay       |
|  |                                |
|  +--------------------------------+
|
|  [Surface Tabs]
|  [Obverse] [Reverse] [Edge]
+------------------------------------------+
```

### HTML Structure

```html
<figure class="tablet-viewer" aria-label="Tablet viewer">
  <!-- Zoom controls -->
  <div class="tablet-viewer__controls" role="group" aria-label="Zoom controls">
    <button type="button" aria-label="Zoom out" data-action="zoom-out">
      <svg aria-hidden="true"><!-- minus icon --></svg>
    </button>
    <button type="button" aria-label="Reset zoom" data-action="zoom-reset">
      <svg aria-hidden="true"><!-- reset icon --></svg>
    </button>
    <button type="button" aria-label="Zoom in" data-action="zoom-in">
      <svg aria-hidden="true"><!-- plus icon --></svg>
    </button>
  </div>

  <!-- Image container with pan/zoom -->
  <div class="tablet-viewer__viewport"
       role="img"
       aria-label="Tablet image: YBC 4644, Old Babylonian letter"
       tabindex="0">
    <img
      src="tablet-image.jpg"
      alt="Clay tablet with cuneiform inscription"
      class="tablet-viewer__image"
      draggable="false"
    >

    <!-- Region overlays -->
    <div class="tablet-viewer__overlays" aria-hidden="true">
      <button
        class="tablet-viewer__region"
        data-region-id="sign-1"
        data-state="default"
        style="left: 20%; top: 30%; width: 10%; height: 8%;"
        aria-label="Sign region, line 1 position 3"
      ></button>
    </div>
  </div>

  <!-- Surface tabs -->
  <div class="tablet-viewer__surfaces" role="tablist" aria-label="Tablet surfaces">
    <button role="tab" aria-selected="true" aria-controls="surface-obverse">
      Obverse
    </button>
    <button role="tab" aria-selected="false" aria-controls="surface-reverse">
      Reverse
    </button>
    <button role="tab" aria-selected="false" aria-controls="surface-edge">
      Edge
    </button>
  </div>

  <!-- Caption -->
  <figcaption class="tablet-viewer__caption">
    YBC 4644 - Old Babylonian Letter
  </figcaption>
</figure>
```

### Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| default | Full controls, surface tabs | Task and review interfaces |
| compact | No surface tabs, minimal controls | Thumbnails, previews |
| hero | Large, animated, no interaction | Marketing page |
| readonly | View only, no region interaction | Archive browsing |

### States

| State | Description | Visual Indicator |
|-------|-------------|------------------|
| loading | Image loading | Skeleton placeholder |
| loaded | Image ready | Full image displayed |
| error | Load failed | Error message + retry |
| panning | User dragging | Cursor change |
| zoomed | Zoom level not 1.0 | Zoom indicator visible |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-tablet-id | string | required | Tablet identifier |
| data-surface | string | "obverse" | Current surface |
| data-zoom | number | 1.0 | Current zoom level |
| data-variant | string | "default" | Display variant |
| data-regions | string | "" | JSON region data |
| data-active-region | string | "" | Currently selected region |

### Interactive Behavior

**Zoom Controls:**
- Click [-] to zoom out (step: 0.25x, min: 0.5x)
- Click [+] to zoom in (step: 0.25x, max: 3.0x)
- Click [o] to reset to 1.0x
- Scroll wheel: zoom at cursor position (with Ctrl/Cmd modifier)
- Pinch gesture: zoom on touch devices

**Pan:**
- Click and drag to pan when zoomed > 1.0x
- Two-finger drag on touch devices
- Arrow keys when focused (step: 10% of viewport)

**Region Interaction:**
- Hover: subtle highlight
- Click: select region, trigger callback
- Tab: navigate between regions
- Enter/Space: select focused region

### Accessibility Requirements

**Keyboard Navigation:**
- Tab to focus viewport
- Arrow keys to pan when zoomed
- Tab through interactive regions
- Enter/Space to activate region
- Escape to deselect region

**Screen Reader:**
- Announce tablet description on focus
- Announce region count and navigation instructions
- Announce selected region details

**ARIA:**
```html
<div role="img" aria-label="[Tablet description]" tabindex="0">
  <!-- Regions have role="button" or role="option" depending on context -->
</div>
```

**Visual:**
- Focus ring on viewport and regions
- High contrast region borders
- Non-color region state indicators

### Region Overlay Specification

Regions are positioned using percentage-based coordinates relative to the image:

```javascript
{
  id: "sign-1",
  x: 20,        // Left edge at 20% from left
  y: 30,        // Top edge at 30% from top
  width: 10,    // 10% of image width
  height: 8,    // 8% of image height
  lineNumber: 1,
  positionInLine: 3,
  status: "proposed",
  confidence: 72
}
```

**Region States:**
| State | Border Style | Background |
|-------|--------------|------------|
| default | Transparent | None |
| hover | Solid, subtle | 5% overlay |
| active | Solid, emphasis | 10% overlay |
| selected | Solid, bold | 15% overlay |
| ai-suggested | Dashed, AI color | 5% AI overlay |

### Loading and Error States

**Loading:**
```html
<div class="tablet-viewer tablet-viewer--loading">
  <div class="tablet-viewer__skeleton" aria-label="Loading tablet image">
    <!-- Animated pulse placeholder -->
  </div>
</div>
```

**Error:**
```html
<div class="tablet-viewer tablet-viewer--error">
  <div class="tablet-viewer__error">
    <svg aria-hidden="true"><!-- error icon --></svg>
    <p>Failed to load tablet image</p>
    <button type="button">Try again</button>
  </div>
</div>
```

---

## RegionOverlay

### Purpose and Use Cases

RegionOverlay is a sub-component that renders clickable/tappable regions over a tablet image. Use for:
- Sign highlighting in tasks
- Line selection in transcription
- Damage area marking
- Interactive learning

### Anatomy

```html
<button
  class="region-overlay"
  data-state="default"
  data-type="sign"
  aria-label="Sign region: AN (dingir), line 1 position 3"
  aria-pressed="false"
>
  <span class="region-overlay__pulse" aria-hidden="true"></span>
</button>
```

### Variants

| Variant | Description | Visual |
|---------|-------------|--------|
| sign | Individual sign | Rounded rectangle |
| line | Full text line | Wide rectangle |
| damage | Damaged area | Irregular/dashed |
| selection | User-drawn area | Dotted while drawing |

### States

| State | Description | Animation |
|-------|-------------|-----------|
| default | Idle, visible | None |
| hover | Mouse over | Subtle glow |
| focus | Keyboard focused | Focus ring |
| active | Being pressed | Scale down slightly |
| selected | Currently selected | Bold border, pulse |
| correct | Correct selection (feedback) | Success pulse |
| incorrect | Wrong selection (feedback) | Error shake |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-region-id | string | Unique identifier |
| data-state | string | Current interaction state |
| data-type | string | Region type variant |
| data-confidence | number | 0-100 confidence score |
| data-status | string | Content status |

### Accessibility

- Minimum touch target: 44x44px (expand hit area if needed)
- Clear focus indicator
- Announces region description
- Supports Enter/Space activation

---

## SignCard

### Purpose and Use Cases

SignCard displays an individual cuneiform sign with optional metadata. Use for:
- Task option display (which sign matches?)
- Sign learning/curriculum
- Reference display in context panels
- Search results

### Anatomy

```
+----------------------+
|                      |
|    [Sign Image]      |
|                      |
+----------------------+
|  Sign Name           |
|  Meaning/Reading     |
+----------------------+
|  [Confidence] [Status]  <- Optional
+----------------------+
```

### HTML Structure

```html
<article class="sign-card" data-variant="default">
  <figure class="sign-card__image">
    <img
      src="sign-an.svg"
      alt="Cuneiform sign AN"
      loading="lazy"
    >
  </figure>

  <div class="sign-card__content">
    <h3 class="sign-card__name">AN</h3>
    <p class="sign-card__reading">an, dingir</p>
    <p class="sign-card__meaning">god, sky, heaven</p>
  </div>

  <!-- Optional metadata footer -->
  <footer class="sign-card__meta">
    <span class="confidence-indicator" data-level="high">
      78% confident
    </span>
    <span class="status-badge" data-status="proposed">
      Proposed
    </span>
  </footer>
</article>
```

### Variants

| Variant | Size | Content | Use Case |
|---------|------|---------|----------|
| option | 80-120px | Image + name only | Task options |
| compact | 60px | Image only | Inline reference |
| default | 120-160px | Image + name + meaning | Learning |
| detailed | 200px+ | Full information | Sign library |

### States (when interactive)

| State | Description |
|-------|-------------|
| default | Resting state |
| hover | Mouse over |
| focus | Keyboard focus |
| selected | Currently selected |
| correct | Correct answer feedback |
| disabled | Not selectable |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-sign-id | string | Sign identifier |
| data-variant | string | Display variant |
| data-interactive | boolean | Can be selected |
| data-selected | boolean | Currently selected |
| data-ai-suggested | boolean | AI recommendation |

### Accessibility

**When used as task option:**
```html
<div role="radiogroup" aria-label="Sign options">
  <label class="sign-card" data-interactive>
    <input type="radio" name="sign-choice" value="an">
    <figure>...</figure>
    <div class="sign-card__content">...</div>
  </label>
</div>
```

- Large touch targets (72px minimum for options)
- Clear selected state indicator
- Keyboard: Tab to navigate, Space to select
- Screen reader: Announces sign name and selection state

---

## TranscriptionLine

### Purpose and Use Cases

TranscriptionLine displays a single line of cuneiform transcription with interactive segments. Use for:
- Review interface transcription display
- Line-by-line editing
- Learning exercises
- Export preview

### Anatomy

```
+------------------------------------------+
| 1. | a-na {d}utu be-li2-ia    [Status][%]|
|    | ^^^^ ^^^^^^ ^^^^^^^^^^              |
+------------------------------------------+
```

### HTML Structure

```html
<div
  class="transcription-line"
  data-line-number="1"
  data-surface="obverse"
  role="listitem"
>
  <span class="transcription-line__number" aria-hidden="true">1.</span>

  <div class="transcription-line__content">
    <!-- Segmented transcription -->
    <button
      class="transcription-segment"
      data-type="word"
      data-segment-id="seg-1"
      aria-label="Word: a-na, meaning: to"
    >
      a-na
    </button>

    <button
      class="transcription-segment"
      data-type="determinative"
      data-segment-id="seg-2"
      aria-label="Determinative: divine name marker"
    >
      {d}
    </button>

    <button
      class="transcription-segment"
      data-type="divine-name"
      data-segment-id="seg-3"
      aria-label="Divine name: Shamash"
    >
      utu
    </button>

    <button
      class="transcription-segment"
      data-type="word"
      data-segment-id="seg-4"
      aria-label="Word: be-li2-ia, meaning: my lord"
    >
      be-li2-ia
    </button>
  </div>

  <div class="transcription-line__meta">
    <span class="status-badge" data-status="accepted">Accepted</span>
    <span class="confidence-meter" data-level="92">92%</span>
  </div>
</div>
```

### Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| display | Read-only | Archive viewing |
| interactive | Segments clickable | Review interface |
| editable | Inline editing | Expert correction |
| comparison | Side-by-side versions | Dispute resolution |

### Segment Types

| Type | Description | Visual Style |
|------|-------------|--------------|
| word | Standard word | Default monospace |
| determinative | Classifier sign | Superscript, secondary color |
| divine-name | Divine/personal name | Distinct styling |
| damaged | Damaged text | Gray, damage marker (#) |
| missing | Missing/broken | Bracketed [x] |
| uncertain | Uncertain reading | Parenthesized, underline |
| number | Numeric value | Distinct styling |

### States

| State | Description |
|-------|-------------|
| default | Normal display |
| hover | Segment hovered |
| selected | Segment selected |
| editing | Inline edit mode |
| highlight | Highlighted for comparison |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-line-number | number | Line number |
| data-surface | string | obverse/reverse/edge |
| data-status | string | Verification status |
| data-confidence | number | Confidence score |
| data-editable | boolean | Can be edited |

### Accessibility

- Line number announced for context
- Segments navigable via Tab
- Click/Enter shows segment detail
- Screen reader announces segment type and content
- Focus management for edit mode

---

## TranscriptionPanel

### Purpose and Use Cases

TranscriptionPanel displays the complete transcription for a tablet, organized by surface and line. Use for:
- Review interface main view
- Expert editing workspace
- Archive display
- Export preview

### Anatomy

```
+------------------------------------------+
| TRANSCRIPTION                            |
| [Obverse] [Reverse] [Edge]   [Export]    |
+------------------------------------------+
| @obverse                                 |
+------------------------------------------+
| 1. | a-na {d}utu be-li2-ia    [v] [92%]  |
| 2. | um-ma {m}a-bi-e-szar2... [?] [78%]  |
| 3. | ar-du-ka-a-ma           [?] [65%]  |
| ...                                      |
+------------------------------------------+
| @reverse                                 |
+------------------------------------------+
| 1. | ...                                 |
+------------------------------------------+
```

### HTML Structure

```html
<section class="transcription-panel" aria-label="Tablet transcription">
  <header class="transcription-panel__header">
    <h2>Transcription</h2>

    <div role="tablist" aria-label="Surfaces">
      <button role="tab" aria-selected="true">Obverse</button>
      <button role="tab" aria-selected="false">Reverse</button>
      <button role="tab" aria-selected="false">Edge</button>
    </div>

    <button type="button" class="button" data-variant="secondary">
      Export ATF
    </button>
  </header>

  <div role="tabpanel" aria-label="Obverse transcription">
    <h3 class="transcription-panel__surface-label">@obverse</h3>

    <ol class="transcription-panel__lines" role="list">
      <!-- TranscriptionLine components -->
    </ol>
  </div>
</section>
```

### Variants

| Variant | Description |
|---------|-------------|
| default | Full display with all controls |
| compact | Collapsed view, expandable |
| readonly | No editing, minimal controls |
| side-by-side | Two versions for comparison |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-tablet-id | string | Tablet identifier |
| data-surface | string | Currently visible surface |
| data-editable | boolean | Enable editing mode |
| data-show-meta | boolean | Show status/confidence |

### Accessibility

- Tab list for surface navigation
- Lines are semantic list items
- Focus management between surfaces
- Keyboard shortcuts for common actions (optional)

---

## Usage Guidelines

### TabletViewer + TranscriptionPanel Layout

For review interfaces, use the Sidebar layout component:

```html
<div class="sidebar" data-width="50%">
  <div class="tablet-viewer" data-variant="default">
    <!-- Tablet with region overlays -->
  </div>

  <div class="transcription-panel" data-editable>
    <!-- Line-by-line transcription -->
  </div>
</div>
```

**Synchronized Behavior:**
- Clicking a region highlights the corresponding line
- Clicking a line highlights the corresponding region
- Zoom state in viewer syncs with current line focus

### Task Interface Pattern

For sign matching tasks:

```html
<div class="stack" data-space="lg">
  <p class="task-prompt">Which sign matches the highlighted area?</p>

  <div class="tablet-viewer" data-variant="compact">
    <!-- Single highlighted region -->
  </div>

  <div class="grid" data-columns="2">
    <label class="sign-card" data-interactive>
      <input type="radio" name="sign">
      <!-- Sign A -->
    </label>
    <label class="sign-card" data-interactive>
      <input type="radio" name="sign">
      <!-- Sign B -->
    </label>
    <label class="sign-card" data-interactive>
      <input type="radio" name="sign">
      <!-- Sign C -->
    </label>
    <label class="sign-card" data-interactive>
      <input type="radio" name="sign">
      <!-- Sign D -->
    </label>
  </div>
</div>
```

### Performance Considerations

- Lazy load tablet images
- Use srcset for responsive image sizes
- Debounce zoom/pan updates (16ms for 60fps)
- Virtualize long transcription lists (>50 lines)
- Cache region calculations on zoom

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial tablet components |
