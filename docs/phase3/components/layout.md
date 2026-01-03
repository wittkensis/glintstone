# Layout Components

**Component Category:** Foundation
**Document Version:** 1.0

Layout components provide the structural foundation for all Glintstone interfaces. These components manage spacing, alignment, and responsive behavior without imposing visual styling.

---

## Container

### Purpose and Use Cases

Container constrains content width and centers it within the viewport. Use for:
- Page-level content containment
- Section-level width constraints
- Readable line lengths for text content

### Anatomy

```html
<div class="container" data-size="default">
  <!-- Content -->
</div>
```

### Variants

| Variant | Max Width | Use Case |
|---------|-----------|----------|
| narrow | 640px | Text-focused content, forms |
| default | 1024px | Standard page content |
| wide | 1280px | Dashboard layouts |
| full | 100% | Edge-to-edge layouts |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-size | string | "default" | Width constraint variant |
| data-padding | boolean | true | Include horizontal padding |
| data-center | boolean | true | Center within viewport |

### HTML Structure

```html
<!-- Standard container -->
<div class="container">
  <main>Page content</main>
</div>

<!-- Narrow container for forms -->
<div class="container" data-size="narrow">
  <form>Form content</form>
</div>

<!-- Wide container for dashboards -->
<div class="container" data-size="wide">
  <div class="dashboard">Dashboard content</div>
</div>
```

### Accessibility

- No specific ARIA requirements
- Ensure content remains readable at all viewport widths
- Horizontal scrolling should be avoided

### Behavior

- Maintains max-width at all viewport sizes
- Adds responsive horizontal padding (larger on desktop)
- Centers within available space

---

## Stack

### Purpose and Use Cases

Stack creates consistent vertical spacing between child elements. Use for:
- Form field groups
- Card content
- Any vertical list of elements

### Anatomy

```html
<div class="stack" data-space="md">
  <div>Child 1</div>
  <div>Child 2</div>
  <div>Child 3</div>
</div>
```

### Variants

| Variant | Gap | Use Case |
|---------|-----|----------|
| xs | 4px | Tight groupings |
| sm | 8px | Related elements |
| md | 16px | Default content spacing |
| lg | 24px | Section breaks |
| xl | 32px | Major sections |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-space | string | "md" | Gap between children |
| data-dividers | boolean | false | Add visual dividers |
| data-recursive | boolean | false | Apply to nested stacks |

### HTML Structure

```html
<!-- Default stack -->
<div class="stack">
  <h2>Heading</h2>
  <p>Paragraph content</p>
  <p>More content</p>
</div>

<!-- Tight stack for form fields -->
<div class="stack" data-space="sm">
  <label>Email</label>
  <input type="email">
  <span class="hint">We'll never share your email</span>
</div>

<!-- Stack with dividers -->
<div class="stack" data-dividers>
  <article>Item 1</article>
  <article>Item 2</article>
  <article>Item 3</article>
</div>
```

### Accessibility

- No specific ARIA requirements
- Maintain logical reading order
- Consider using semantic list elements when appropriate

### Behavior

- Only applies spacing between elements (not before first or after last)
- Handles margin collapse automatically
- Works with any child element types

---

## Cluster

### Purpose and Use Cases

Cluster groups elements horizontally with automatic wrapping. Use for:
- Tag groups
- Button groups
- Icon + text combinations
- Badge collections

### Anatomy

```html
<div class="cluster" data-space="sm" data-align="center">
  <span>Item 1</span>
  <span>Item 2</span>
  <span>Item 3</span>
</div>
```

### Variants

| Alignment | Description |
|-----------|-------------|
| start | Align items to start |
| center | Center items |
| end | Align items to end |
| space-between | Distribute with space between |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-space | string | "sm" | Gap between items |
| data-align | string | "start" | Horizontal alignment |
| data-justify | string | "start" | Vertical alignment |
| data-wrap | boolean | true | Allow wrapping |

### HTML Structure

```html
<!-- Tag cluster -->
<div class="cluster" data-space="xs">
  <span class="tag">Sumerian</span>
  <span class="tag">Administrative</span>
  <span class="tag">Ur III</span>
</div>

<!-- Button group -->
<div class="cluster" data-align="end">
  <button type="button">Cancel</button>
  <button type="submit">Submit</button>
</div>

<!-- Icon + text -->
<div class="cluster" data-space="xs" data-align="center">
  <svg aria-hidden="true"><!-- icon --></svg>
  <span>Label text</span>
</div>
```

### Accessibility

- Use appropriate roles for button groups (role="group")
- Ensure logical tab order
- Consider aria-label for grouped controls

### Behavior

- Wraps to new line when space exhausted
- Maintains consistent gaps horizontally and vertically
- Centers vertically by default

---

## Grid

### Purpose and Use Cases

Grid creates multi-column layouts with responsive behavior. Use for:
- Card grids
- Feature sections
- Gallery layouts
- Dashboard widgets

### Anatomy

```html
<div class="grid" data-columns="3" data-gap="md">
  <div>Cell 1</div>
  <div>Cell 2</div>
  <div>Cell 3</div>
</div>
```

### Variants

| Columns | Description |
|---------|-------------|
| 2 | Two-column grid |
| 3 | Three-column grid |
| 4 | Four-column grid |
| auto-fit | As many as fit (min 250px) |
| auto-fill | Fill available space |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-columns | string | "auto-fit" | Number of columns |
| data-gap | string | "md" | Gap between cells |
| data-min | string | "250px" | Minimum cell width (auto modes) |

### HTML Structure

```html
<!-- Responsive card grid -->
<div class="grid" data-columns="auto-fit" data-min="280px">
  <article class="card">Card 1</article>
  <article class="card">Card 2</article>
  <article class="card">Card 3</article>
  <article class="card">Card 4</article>
</div>

<!-- Fixed 3-column grid -->
<div class="grid" data-columns="3">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>

<!-- Statistics grid -->
<div class="grid" data-columns="3" data-gap="lg">
  <div class="stat-card">Stat 1</div>
  <div class="stat-card">Stat 2</div>
  <div class="stat-card">Stat 3</div>
</div>
```

### Responsive Behavior

| Viewport | Columns |
|----------|---------|
| < 480px | 1 |
| 480-768px | 2 |
| > 768px | As specified |

### Accessibility

- Ensure reading order makes sense when stacked
- Consider using CSS order carefully (visual vs DOM order)
- Grid items should have clear boundaries

### Behavior

- Automatically collapses to fewer columns on small screens
- Maintains equal column widths
- Centers incomplete rows

---

## Sidebar

### Purpose and Use Cases

Sidebar creates a two-column layout with one flexible and one fixed column. Use for:
- Navigation sidebar + content
- Tablet image + transcription
- Main content + context panel

### Anatomy

```html
<div class="sidebar" data-side="left" data-width="300px">
  <aside>Sidebar content</aside>
  <main>Main content</main>
</div>
```

### Variants

| Side | Description |
|------|-------------|
| left | Sidebar on left |
| right | Sidebar on right |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-side | string | "left" | Which side for sidebar |
| data-width | string | "25%" | Sidebar width |
| data-min-content | string | "50%" | Minimum main content width before stacking |
| data-gap | string | "lg" | Gap between columns |

### HTML Structure

```html
<!-- Left sidebar navigation -->
<div class="sidebar" data-side="left" data-width="240px">
  <nav aria-label="Main navigation">
    <!-- Navigation items -->
  </nav>
  <main>
    <!-- Page content -->
  </main>
</div>

<!-- Right sidebar for context -->
<div class="sidebar" data-side="right" data-width="320px">
  <article>
    <!-- Main content -->
  </article>
  <aside aria-label="Context information">
    <!-- Context panel -->
  </aside>
</div>

<!-- Tablet viewer layout -->
<div class="sidebar" data-width="50%" data-gap="xl">
  <div class="tablet-viewer">
    <!-- Tablet image -->
  </div>
  <div class="transcription-panel">
    <!-- Transcription -->
  </div>
</div>
```

### Responsive Behavior

When viewport is too narrow (main content would be < min-content):
- Stacks to single column
- Sidebar appears above or below based on DOM order

### Accessibility

- Use appropriate landmark elements (aside, nav, main)
- Ensure focus order matches expected reading order
- Consider skip links for long sidebars

### Behavior

- Sidebar maintains fixed width until breakpoint
- Main content fills remaining space
- Stacks vertically when constrained

---

## Switcher

### Purpose and Use Cases

Switcher displays children in a row when space permits, stacking when constrained. Use for:
- Form layouts (horizontal on desktop, stacked on mobile)
- Two-column content that should stack
- Adaptive button groups

### Anatomy

```html
<div class="switcher" data-threshold="480px">
  <div>Column 1</div>
  <div>Column 2</div>
</div>
```

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-threshold | string | "480px" | Width at which to switch |
| data-space | string | "md" | Gap between items |
| data-limit | number | 4 | Maximum items before always stacking |

### HTML Structure

```html
<!-- Two-column form section -->
<div class="switcher" data-threshold="600px">
  <div class="form-group">
    <label>First Name</label>
    <input type="text">
  </div>
  <div class="form-group">
    <label>Last Name</label>
    <input type="text">
  </div>
</div>

<!-- Action buttons -->
<div class="switcher" data-threshold="320px">
  <button type="button">Secondary Action</button>
  <button type="submit">Primary Action</button>
</div>

<!-- Stat display -->
<div class="switcher" data-threshold="480px" data-limit="3">
  <div class="stat">15 Tasks</div>
  <div class="stat">3 Tablets</div>
  <div class="stat">87% Accuracy</div>
</div>
```

### Accessibility

- Content should make sense in both layouts
- Tab order should be logical in both orientations
- Consider visual hierarchy changes when stacked

### Behavior

- Uses CSS container queries or viewport width
- Switches between row and column layout
- All children have equal width in row mode

---

## Usage Guidelines

### Composition Patterns

**Page Layout:**
```html
<div class="container">
  <div class="stack" data-space="xl">
    <header class="header">...</header>
    <div class="sidebar" data-side="left">
      <nav>...</nav>
      <main class="stack">
        <!-- Page sections -->
      </main>
    </div>
    <footer>...</footer>
  </div>
</div>
```

**Card Grid:**
```html
<section class="stack" data-space="lg">
  <h2>Section Title</h2>
  <div class="grid" data-columns="auto-fit">
    <article class="card stack" data-space="sm">
      <!-- Card content -->
    </article>
  </div>
</section>
```

**Form Layout:**
```html
<form class="stack" data-space="lg">
  <div class="switcher">
    <div class="stack" data-space="xs">
      <label>Field 1</label>
      <input type="text">
    </div>
    <div class="stack" data-space="xs">
      <label>Field 2</label>
      <input type="text">
    </div>
  </div>
  <div class="cluster" data-align="end">
    <button type="button">Cancel</button>
    <button type="submit">Submit</button>
  </div>
</form>
```

### When to Use Each

| Component | Use When |
|-----------|----------|
| Container | Constraining content width |
| Stack | Vertical spacing between elements |
| Cluster | Horizontal grouping with wrap |
| Grid | Multi-column card/item layouts |
| Sidebar | Fixed + flexible column layouts |
| Switcher | Adaptive row/column layouts |

### Anti-Patterns

- Do not nest many levels of layout components
- Do not use Grid for simple two-column layouts (use Sidebar or Switcher)
- Do not override layout spacing with custom margins
- Do not use Container inside Container

---

## Implementation Notes

### CSS Architecture

Layout components should use:
- CSS custom properties for spacing values
- CSS Grid and Flexbox for layouts
- Container queries where supported (with fallback)
- No fixed pixel values except breakpoints

### Example CSS Pattern

```css
.stack {
  display: flex;
  flex-direction: column;
}

.stack > * + * {
  margin-block-start: var(--stack-space, var(--space-md));
}

.stack[data-space="sm"] {
  --stack-space: var(--space-sm);
}

.stack[data-space="lg"] {
  --stack-space: var(--space-lg);
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial layout components |
