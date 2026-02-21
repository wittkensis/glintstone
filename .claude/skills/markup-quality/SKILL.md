---
triggers: [markup, html, semantic, accessibility, a11y, structure, dom, wrapper, reduce, heading, ui, optimize, refactor]
description: Semantic HTML, accessibility, and wrapper reduction for clean DOM structure
---

# Markup Quality - Semantic HTML & DOM Optimization

## Core Principle

**"HTML is for structure, CSS is for presentation"**

- Semantic HTML reduces CSS needs, improves accessibility, and simplifies maintenance
- Every `<div>` should justify its existence - wrappers accumulate technical debt
- Use the right element for the job: `<button>` not `<div onclick>`, `<nav>` not `<div class="navigation">`
- State belongs in data attributes, not class names
- Screen readers, SEO, and future developers thank you for semantic markup

## Semantic HTML Patterns

### Metadata Displays: Use `<dl>/<dt>/<dd>`

**NEVER use generic divs for key-value pairs. Use description lists.**

```html
<!-- ❌ BAD: div soup -->
<div class="metadata">
  <div class="meta-row">
    <div class="meta-label">Language</div>
    <div class="meta-value">Akkadian</div>
  </div>
  <div class="meta-row">
    <div class="meta-label">Period</div>
    <div class="meta-value">Old Babylonian</div>
  </div>
</div>

<!-- ✅ GOOD: semantic description list -->
<dl class="tablet-meta__row">
  <div class="meta-item">
    <dt>Language</dt>
    <dd>Akkadian</dd>
  </div>
  <div class="meta-item">
    <dt>Period</dt>
    <dd>Old Babylonian</dd>
  </div>
</dl>
```

**When to use `<dl>`:** Metadata, glossaries, key-value pairs, term definitions

### Content Sectioning: `<article>`, `<section>`, `<aside>`, `<nav>`

Use semantic sectioning elements to structure pages:

```html
<!-- ❌ BAD: meaningless divs -->
<div class="page-content">
  <div class="main-area">
    <div class="intro">...</div>
    <div class="text-content">...</div>
  </div>
  <div class="sidebar-content">...</div>
</div>

<!-- ✅ GOOD: semantic sections -->
<main class="page-content">
  <article class="tablet-detail">
    <section class="tablet-intro">...</section>
    <section class="tablet-transliteration">...</section>
  </article>
  <aside class="knowledge-sidebar">...</aside>
</main>
```

**Guidelines:**
- `<main>` - Primary page content (one per page)
- `<article>` - Self-contained content (could stand alone)
- `<section>` - Thematic grouping with heading
- `<aside>` - Tangentially related content
- `<nav>` - Navigation links

### Interactive Elements: `<button>` vs `<a>`

```html
<!-- ❌ NEVER: div with onclick -->
<div class="clickable" onclick="togglePanel()">Toggle</div>

<!-- ✅ GOOD: button for actions -->
<button class="btn btn--toggle" onclick="togglePanel()">Toggle</button>

<!-- ✅ GOOD: link for navigation -->
<a href="/tablets/P123456" class="tablet-link">View Tablet</a>
```

**Decision tree:**
- Action that changes state → `<button>`
- Navigation to another page → `<a href>`
- NEVER use div/span with onclick

### Collapsible Content: `<details>/<summary>`

```html
<!-- ✅ GOOD: native collapsible (no JS needed) -->
<details class="atf-legend">
  <summary>Legend</summary>
  <div class="atf-legend__items">...</div>
</details>
```

**When to use:** Expandable sections, progressive disclosure, FAQ items

## Wrapper Reduction

### Audit Process

**Step 1: Count nesting depth**
- Max 4-5 levels is a warning sign
- Use browser DevTools to visualize

**Step 2: Justify each wrapper**
Ask for every `<div>`:
- Does it provide semantic meaning? → Use semantic element instead
- Does it enable flexbox/grid layout? → Check if parent can handle it
- Does it only have one child? → Probably unnecessary
- Is it just for styling? → Question if CSS can be on another element

**Step 3: Common elimination patterns**
- Single-child wrapper → merge into parent or child
- Adjacent wrappers with same purpose → combine them
- Flexbox alignment wrapper → use `align-items` on parent
- Spacing wrapper → use `gap` property instead

### Example: Composite Panel Header (from codebase)

```html
<!-- ❌ BEFORE: 4 levels of nesting -->
<div class="composite-panel__header">
  <div class="composite-panel__title-group">
    <h2 class="composite-panel__title">
      <div class="title-wrapper">
        {{ designation }}
      </div>
    </h2>
  </div>
</div>

<!-- ✅ AFTER: 2 levels (removed 2 unnecessary wrappers) -->
<div class="composite-panel__header">
  <h2 class="composite-panel__title">{{ designation }}</h2>
  <span class="composite-panel__count">{{ count }} tablets</span>
</div>
```

### Flexbox/Grid Eliminates Wrappers

```html
<!-- ❌ BAD: wrapper just for centering -->
<div class="outer">
  <div class="center-wrapper">
    <div class="content">...</div>
  </div>
</div>

<!-- ✅ GOOD: flexbox on parent -->
<div class="outer" style="display: flex; align-items: center; justify-content: center;">
  <div class="content">...</div>
</div>

<!-- ❌ BAD: wrapper for spacing between items -->
<div class="list">
  <div class="item-wrapper"><div class="item">Item 1</div></div>
  <div class="item-wrapper"><div class="item">Item 2</div></div>
</div>

<!-- ✅ GOOD: gap property -->
<div class="list" style="display: flex; gap: var(--space-4);">
  <div class="item">Item 1</div>
  <div class="item">Item 2</div>
</div>
```

## Heading Hierarchy

### Rules

1. **Single `<h1>` per page** - The main page title
2. **Never skip levels** - h2 follows h1, h3 follows h2 (never h1 → h3)
3. **Visual ≠ Semantic** - Use CSS to style, not wrong heading level
4. **Screen reader navigation** - Users jump between headings

### Detection

```javascript
// Quick audit in browser console:
document.querySelectorAll('h1').length > 1 // ❌ Multiple h1s
```

### Example from Tablet Detail Page

```html
<!-- ✅ CORRECT hierarchy -->
<h1>{{ tablet.p_number }}</h1>                    <!-- Page title -->
<h2>Metadata</h2>                                  <!-- Major section -->
<h3>Physical Description</h3>                      <!-- Subsection -->
<h3>Provenance</h3>                                <!-- Subsection -->
<h2>Transliteration</h2>                           <!-- Major section -->
```

### When Visual ≠ Semantic

Use CSS to adjust size, don't pick wrong heading level:

```html
<!-- ✅ GOOD: h3 styled smaller -->
<h3 class="subsection-title" style="font-size: var(--text-sm);">
  Minor Detail
</h3>

<!-- ❌ BAD: h5 for small text (skipped h4) -->
<h5>Minor Detail</h5>
```

## Data Attributes for State

### Why Data Attributes?

- **Separates state from styling** - `.sidebar` is identity, `data-state="open"` is state
- **Self-documenting** - `data-view-mode="grid"` is clearer than `.grid-mode`
- **Better JS querying** - `[data-state="open"]` is explicit
- **Avoid class soup** - `.sidebar.is-open.expanded` vs `.sidebar[data-state="open"]`

### Patterns

```html
<!-- ✅ GOOD: data attribute for state -->
<aside class="atf-knowledge-sidebar" data-state="closed">
  <!-- JS changes data-state to "open" -->
</aside>

<div class="tablet-detail-viewer" data-viewer-state="expanded">
  <!-- viewer-state: "expanded" | "collapsed" -->
</div>

<section class="atf-viewer" data-mode="interactive">
  <!-- mode: "interactive" | "raw" | "parallel" -->
</section>
```

### CSS Styling

```css
/* ✅ Style based on data attributes */
.atf-knowledge-sidebar[data-state="closed"] {
  flex: 0 0 48px;
}

.atf-knowledge-sidebar[data-state="open"] {
  flex: 0 0 348px;
}

.atf-viewer[data-mode="raw"] .atf-word__gloss {
  display: none;
}
```

### Common State Attributes

- `data-state` - open/closed, active/inactive, loading/loaded
- `data-view-mode` - grid/list, compact/expanded
- `data-expanded` - true/false for boolean states
- `data-active-tab` - which tab is active
- `data-has-content` - true/false for conditional rendering

## Accessibility Checklist

Use this for every new component:

- [ ] **Semantic HTML used** - No div/span soup, proper elements chosen
- [ ] **ARIA labels where needed** - `aria-label`, `aria-labelledby`, `aria-describedby`
- [ ] **Keyboard navigation works** - Tab order logical, Enter/Space activate
- [ ] **Focus visible** - Outline or focus ring clearly visible
- [ ] **Screen reader tested** - Use VoiceOver/NVDA to verify experience
- [ ] **Form labels associated** - `<label for="id">` or wrapping label
- [ ] **Button vs link correct** - Actions use button, navigation uses link
- [ ] **Heading hierarchy valid** - Single h1, no skipped levels
- [ ] **Color contrast sufficient** - Text meets WCAG AA (4.5:1 for normal text)
- [ ] **Interactive elements identifiable** - Buttons look clickable

### ARIA Patterns from Codebase

```html
<!-- Tabs with proper ARIA -->
<nav role="tablist" aria-label="Knowledge panels">
  <button class="tab-button"
          role="tab"
          aria-selected="false"
          data-tab="dictionary">
    Dictionary
  </button>
</nav>

<!-- Expandable regions -->
<button aria-expanded="false"
        aria-controls="meta-secondary"
        id="meta-toggle">
  More
</button>
<div id="meta-secondary" hidden>...</div>
```

## Anti-Patterns

### NEVER Do These

❌ **Use div when semantic element exists**
```html
<!-- BAD -->
<div class="navigation">
  <div class="nav-item">Home</div>
</div>

<!-- GOOD -->
<nav class="navigation">
  <a href="/" class="nav-item">Home</a>
</nav>
```

❌ **Skip heading levels**
```html
<!-- BAD: h1 → h3 (skipped h2) -->
<h1>Page Title</h1>
<h3>Subsection</h3>

<!-- GOOD: proper hierarchy -->
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
```

❌ **Empty wrappers just for styling**
```html
<!-- BAD: wrapper adds no semantic or layout value -->
<div class="wrapper">
  <div class="inner-wrapper">
    <div class="content">Text</div>
  </div>
</div>

<!-- GOOD: one element, styled directly -->
<div class="content">Text</div>
```

❌ **onclick on div/span**
```html
<!-- BAD: not keyboard accessible -->
<div class="clickable" onclick="doThing()">Click me</div>

<!-- GOOD: semantic button -->
<button class="btn" onclick="doThing()">Click me</button>
```

### ALWAYS Do These

✅ **Question every wrapper's purpose** - Can it be removed or merged?

✅ **Use semantic HTML first, ARIA second** - `<nav>` before `<div role="navigation">`

✅ **Test with keyboard** - Tab through, ensure all interactive elements reachable

✅ **Verify heading hierarchy** - Use browser extension or manual scan

## Quick Reference

| Content Type | Semantic Element | Example |
|--------------|------------------|---------|
| Metadata, key-value | `<dl><dt><dd>` | Language: Akkadian |
| Navigation links | `<nav><ul><li>` | Header menu |
| Page sections | `<section>`, `<article>` | Intro, main content |
| Tangential content | `<aside>` | Sidebar, related info |
| Interactive action | `<button>` | Toggle panel, submit |
| Navigation link | `<a href>` | Go to tablet detail |
| Collapsible content | `<details><summary>` | Expandable legend |
| State management | `data-state="value"` | Open/closed sidebar |

**Wrapper reduction checklist:**
1. Count nesting depth (>5 is bad)
2. Justify each wrapper's existence
3. Remove single-child wrappers
4. Use flexbox/grid gap instead of spacing wrappers
5. Combine adjacent wrappers with same purpose

**Heading rules:**
- One h1 per page
- Never skip levels
- Use CSS for visual sizing, not wrong heading level
