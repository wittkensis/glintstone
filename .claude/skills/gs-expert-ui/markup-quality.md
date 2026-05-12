---
question: "How do I write semantic HTML, reduce wrappers, and make Glintstone's pages accessible?"
created: 2026-05-11
modified: 2026-05-11
context: "Migrated from skills-disabled/markup-quality/SKILL.md during the 2026-05-11 overhaul. Anchored to actual codebase examples from app/templates/."
status: active
audience: [claude, engineers, designers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-ui]
supersedes: ".claude/skills-disabled/markup-quality/SKILL.md"
superseded_by: null
---

# Semantic markup & accessibility

## Element selection

| Content type | Element | Why |
|---|---|---|
| Metadata, key-value pairs | `<dl><dt><dd>` | Description lists are semantic; div-soup is not |
| Navigation | `<nav><ul><li><a>` | Screen readers find `<nav>` directly |
| Page sections | `<section>`, `<article>` | Outline algorithm + screen-reader navigation |
| Tangential content | `<aside>` | Sidebar, related info |
| Action | `<button>` | Keyboard-accessible, semantic |
| Navigation link | `<a href>` | Goes somewhere, not does something |
| Collapsible | `<details><summary>` | Native, no JS |
| Tabular data | `<table>` | Headers + cells, not divs |

## The metadata pattern (tablet detail page)

```html
<!-- ❌ div soup -->
<div class="metadata">
  <div class="meta-row">
    <div class="meta-label">Language</div>
    <div class="meta-value">Akkadian</div>
  </div>
</div>

<!-- ✅ semantic description list -->
<dl class="tablet-meta">
  <div class="tablet-meta__row">
    <dt>Language</dt>
    <dd>Akkadian</dd>
  </div>
  <div class="tablet-meta__row">
    <dt>Period</dt>
    <dd>Old Babylonian</dd>
  </div>
</dl>
```

Use `<dl>` for anything that's a key-value pair: tablet metadata, glossary entries, term definitions.

## Page structure

```html
<main class="page-content">
  <article class="tablet-detail">
    <section class="tablet-intro">...</section>
    <section class="tablet-transliteration">...</section>
  </article>
  <aside class="knowledge-sidebar">...</aside>
</main>
```

- `<main>` — exactly one per page, primary content
- `<article>` — self-contained, could stand alone (a tablet, a lemma entry)
- `<section>` — thematic grouping with a heading
- `<aside>` — tangential (knowledge bar, filter panel)

## Wrapper reduction

For every `<div>`, ask:

1. Does it provide semantic meaning? → Use the semantic element instead.
2. Does it enable a flex/grid layout? → Could the parent handle it?
3. Does it have only one child? → Probably unnecessary.
4. Is it just for styling? → Could CSS go on another element?

Real example from the codebase (composite panel header):

```html
<!-- ❌ BEFORE (4 levels) -->
<div class="composite-panel__header">
  <div class="composite-panel__title-group">
    <h2 class="composite-panel__title">
      <div class="title-wrapper">{{ designation }}</div>
    </h2>
  </div>
</div>

<!-- ✅ AFTER (2 levels) -->
<div class="composite-panel__header">
  <h2 class="composite-panel__title">{{ designation }}</h2>
  <span class="composite-panel__count">{{ count }} tablets</span>
</div>
```

Flex/grid + `gap` eliminates spacing wrappers:

```html
<!-- ❌ -->
<div class="list">
  <div class="item-wrapper"><div class="item">A</div></div>
  <div class="item-wrapper"><div class="item">B</div></div>
</div>

<!-- ✅ -->
<div class="list" style="display: flex; gap: var(--space-4);">
  <div class="item">A</div>
  <div class="item">B</div>
</div>
```

## Heading hierarchy

- Single `<h1>` per page (the page title)
- Never skip levels — h2 follows h1, h3 follows h2
- Visual size ≠ semantic level — use CSS to style, don't downshift the heading

```html
<!-- Tablet detail -->
<h1>{{ tablet.p_number }}</h1>      <!-- Page title -->
<h2>Metadata</h2>                    <!-- Major section -->
<h3>Physical Description</h3>        <!-- Subsection -->
<h3>Provenance</h3>
<h2>Transliteration</h2>
```

Quick browser check: `document.querySelectorAll('h1').length > 1` should be `false`.

## Data attributes for state

State doesn't belong in class names. Use data attributes:

```html
<!-- ❌ -->
<aside class="sidebar is-open expanded">

<!-- ✅ -->
<aside class="sidebar" data-state="open" data-mode="expanded">
```

CSS:

```css
.sidebar[data-state="closed"] { flex: 0 0 48px; }
.sidebar[data-state="open"]   { flex: 0 0 348px; }
.atf-viewer[data-mode="raw"] .atf-word__gloss { display: none; }
```

Conventions used in the codebase:

- `data-state` — `open | closed | active | inactive | loading | loaded`
- `data-view-mode` — `grid | list | compact | expanded`
- `data-expanded` — `true | false`
- `data-active-tab` — which tab is active
- `data-mode` — `interactive | raw | parallel`

## ARIA — only when semantics don't suffice

```html
<!-- Tabs -->
<nav role="tablist" aria-label="Knowledge panels">
  <button role="tab" aria-selected="false" data-tab="dictionary">
    Dictionary
  </button>
</nav>

<!-- Expandable region -->
<button aria-expanded="false" aria-controls="meta-secondary" id="meta-toggle">
  More
</button>
<div id="meta-secondary" hidden>...</div>
```

## Accessibility checklist (every new component)

- [ ] Semantic HTML used (no div/span soup)
- [ ] ARIA labels where semantics don't carry the meaning
- [ ] Keyboard navigation works (Tab, Enter, Space)
- [ ] Focus ring clearly visible
- [ ] Screen-reader-tested if non-trivial
- [ ] Form labels associated via `for` or wrapping
- [ ] Button vs link chosen correctly
- [ ] Heading hierarchy valid
- [ ] Color contrast ≥ WCAG AA (4.5:1 for body text)
- [ ] Interactive elements visually identifiable

## Anti-patterns

- ❌ `<div>` instead of `<nav>`, `<button>`, `<article>` …
- ❌ Multiple `<h1>` per page
- ❌ Heading levels skipped
- ❌ Empty wrappers only for styling
- ❌ `onclick` on `<div>` or `<span>` (not keyboard-accessible)
