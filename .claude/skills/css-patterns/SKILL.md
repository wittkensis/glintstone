---
triggers: [css, styles, flexbox, tokens, bem, layout, spacing, colors, performance, responsive, ui, optimize, refactor]
description: Token enforcement, flexbox mastery, BEM consistency, and CSS performance patterns
---

# CSS Patterns - Tokens, Flexbox & Component Quality

## Core Principle

**"Use tokens, follow BEM, master flexbox"**

- Every hardcoded value (`#fff`, `16px`, `0.3s`) is a maintenance burden → use tokens
- Reuse existing components before creating new ones → check `/components/*.css`
- Flexbox scrolling needs `min-height: 0` → don't forget this critical pattern
- BEM naming keeps CSS predictable → `.block__element--modifier`

## Token Enforcement

**Location:** `/app/static/css/core/tokens.css` (261 lines - comprehensive system)

### All Token Categories

#### Colors
```css
/* Backgrounds */
--color-bg             /* #1a1a1a - base background */
--color-bg-inset       /* #0a0a0a - sunken areas */
--color-bg-elevated    /* #242424 - raised surfaces */
--color-bg-deepest     /* #000000 - deepest black */
--color-surface        /* #303030 - cards, panels */

/* Text */
--color-text           /* #e8e6e3 - primary text */
--color-text-secondary /* #888888 - secondary text */
--color-text-muted     /* #a0a0a0 - de-emphasized */
--color-text-subtle    /* #707070 - labels, captions */

/* Accent (warm sand/gold) */
--color-accent         /* #c9a962 */
--color-accent-hover   /* #d4b97a */
--color-accent-muted   /* #8b7642 */

/* Semantic */
--color-success        /* #6b8e6b - green */
--color-error          /* #b85c5c - red */
--color-warning        /* amber */
--color-info           /* #7ba4c4 - blue */

/* UI */
--color-border         /* #404040 */
```

#### Spacing (8px-based scale)
```css
--space-0   /* 0 */
--space-1   /* 4px */
--space-2   /* 8px */
--space-3   /* 12px */
--space-4   /* 16px */
--space-5   /* 20px */
--space-6   /* 24px */
--space-8   /* 32px */
--space-10  /* 40px */
--space-12  /* 48px */
```

#### Typography
```css
/* Sizes */
--text-xxs      /* 10px */
--text-xs       /* 12px */
--text-sm       /* 14px */
--text-base     /* 16px */
--text-lg       /* 18px */
--text-xl       /* 20px */
--text-2xl      /* 24px */
--text-3xl      /* 28px */
--text-display  /* 48px */

/* Families */
--font-sans       /* system-ui stack */
--font-mono       /* SF Mono, Monaco */
--font-serif      /* Playfair Display */
--font-cuneiform  /* Noto Sans Cuneiform */

/* Weights */
--font-normal     /* 400 */
--font-medium     /* 500 */
--font-semibold   /* 600 */
--font-bold       /* 700 */

/* Line heights */
--line-height-tight   /* 1.2 */
--line-height-normal  /* 1.5 */
--line-height-relaxed /* 1.6 */
```

#### Radius
```css
--radius-xs    /* 2px */
--radius-sm    /* 4px */
--radius-md    /* 8px */
--radius-lg    /* 12px */
--radius-full  /* 9999px - pills */
```

#### Shadows
```css
--shadow-xs    /* subtle */
--shadow-sm    /* small */
--shadow-md    /* medium */
--shadow-lg    /* large */
--shadow-xl    /* extra large */
--shadow-inset /* inset shadow */
```

#### Transitions
```css
--transition-instant  /* 0.05s */
--transition-fast     /* 0.1s */
--transition-normal   /* 0.2s */
--transition-slow     /* 0.3s */
--transition-slower   /* 0.45s */
```

### Detection Patterns

**Find hardcoded values:**
```bash
# In your terminal:
grep -r "#[0-9a-f]\{3,6\}" app/static/css/  # Hex colors
grep -r "rgba\?(" app/static/css/            # RGB(A) colors
grep -r "[0-9]\+px" app/static/css/          # Pixel values
grep -r "[0-9.]\+s" app/static/css/          # Timing values
```

**Replace with tokens:**
```css
/* ❌ BAD: hardcoded values */
.component {
  padding: 16px 24px;
  background: #242424;
  color: #e8e6e3;
  border: 1px solid #404040;
  border-radius: 4px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* ✅ GOOD: token-based */
.component {
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-elevated);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-sm);
}
```

### When Tokens Don't Exist

**If you need a value not in tokens:**
1. Check if existing token is close enough (use closest)
2. If truly unique, consider adding to `tokens.css`
3. Document why hardcoded value is needed (comment in CSS)

```css
/* ✅ ACCEPTABLE: documented exception */
.atf-cuneiform-glyph {
  /* Custom size for cuneiform readability - not in token scale */
  font-size: 2.75rem; /* Between --text-3xl and --text-display */
}
```

## Flexbox Mastery

### The Three Critical Rules

**1. `min-height: 0` for scrolling flex children**

When a flex child needs to scroll, it MUST have `min-height: 0`:

```css
/* ❌ BAD: scrolling won't work */
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;  /* Won't scroll! */
}

/* ✅ GOOD: min-height: 0 enables scrolling */
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scrollable-content {
  flex: 1;
  min-height: 0;      /* Critical! */
  overflow-y: auto;
}
```

**Why:** Flex items have implicit `min-height: auto`, which prevents shrinking below content size.

**2. `flex: 1` means grow + shrink + basis 0**

```css
/* ❌ CONFUSING: what does this mean? */
.item { flex: 1; }

/* ✅ EXPLICIT: same as above */
.item {
  flex-grow: 1;     /* Grow to fill space */
  flex-shrink: 1;   /* Shrink if needed */
  flex-basis: 0;    /* Start from 0, not content size */
}

/* Common alternatives: */
.fixed-size { flex: 0 0 200px; }        /* Don't grow/shrink, 200px wide */
.grow-only { flex: 1 0 auto; }          /* Grow but don't shrink */
.no-grow { flex: 0 1 auto; }            /* Shrink but don't grow */
```

**3. `min-width: 0` prevents text overflow in flex items**

```css
/* ❌ BAD: long text overflows container */
.flex-item {
  flex: 1;
}

.flex-item__text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;  /* Won't truncate! */
}

/* ✅ GOOD: min-width: 0 allows truncation */
.flex-item {
  flex: 1;
  min-width: 0;  /* Critical for text truncation */
}

.flex-item__text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;  /* Now works! */
}
```

### Full-Height Scrolling Layout Pattern

**The standard full-height page with scrollable content:**

```css
/* Page container (fills viewport) */
.page-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
}

/* Fixed header */
.page-header {
  flex: 0 0 auto;  /* Don't grow/shrink */
  height: 60px;
}

/* Scrollable main content */
.page-main {
  flex: 1;           /* Grow to fill */
  min-height: 0;     /* Critical for scrolling */
  overflow-y: auto;  /* Enable scrolling */
}

/* Fixed footer */
.page-footer {
  flex: 0 0 auto;  /* Don't grow/shrink */
}
```

**Example from tablet detail page:**

```css
.tablet-detail-viewer {
  display: flex;
  height: 100%;
}

.viewer-panel {
  flex: 1 1 0;        /* Grow to fill */
  min-height: 0;      /* Critical */
  overflow: hidden;
}

.atf-panel {
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
}

.atf-viewer__main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;      /* Enables .atf-content to scroll */
  overflow: hidden;
}

.atf-content {
  flex: 1;
  min-height: 0;      /* Critical */
  overflow-y: auto;   /* Scrollable content */
}
```

### Common Flexbox Issues & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Flex child won't scroll | Missing `min-height: 0` | Add `min-height: 0` to scrollable child |
| Content overflows container | Implicit `min-width: auto` | Add `min-width: 0` to flex item |
| Item won't shrink | `flex-shrink: 0` or content forcing size | Use `flex-shrink: 1` or `min-width: 0` |
| Item won't grow | `flex-grow: 0` | Use `flex: 1` or `flex-grow: 1` |
| Uneven spacing | Using margin | Use `gap` property instead |

### Debugging Flexbox

```css
/* Temporarily add borders to visualize layout */
.debug * {
  outline: 1px solid red !important;
}

/* Check computed flex values in DevTools */
/* Elements → Computed → filter "flex" */
```

## BEM Consistency

**Format:** `.block__element--modifier`

### Naming Rules

- **Block** - Independent, reusable component (`.btn`, `.card`, `.badge`)
- **Element** - Part of block, no standalone meaning (`.btn__icon`, `.card__title`)
- **Modifier** - Variation of block/element (`.btn--primary`, `.card--elevated`)

### When to Use Each

```css
/* BLOCK: Independent component */
.btn {
  padding: var(--space-2);
  background: var(--color-surface);
}

/* ELEMENT: Part of block */
.btn__icon {
  margin-right: var(--space-2);
}

/* MODIFIER: Variation */
.btn--primary {
  background: var(--color-accent);
  color: var(--color-bg);
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--color-border);
}
```

### Examples from Glintstone Codebase

```css
/* Buttons */
.btn                      /* Block */
.btn__icon                /* Element */
.btn--primary             /* Modifier */
.btn--ghost               /* Modifier */
.btn--icon-left           /* Modifier */

/* Cards */
.card                     /* Block */
.card-image               /* Element (dash separator ok for sub-components) */
.card-details             /* Element */
.card-primary             /* Element */
.card--compact            /* Modifier */
.card--elevated           /* Modifier */

/* Badges */
.badge                    /* Block */
.badge--pos               /* Modifier (part of speech) */
.badge--language          /* Modifier */
.badge--sm                /* Modifier (size) */
```

### Anti-Patterns

❌ **Avoid:**
```css
.btn.primary              /* Use --primary modifier */
.card-image-overlay-text  /* Too many levels, break into elements */
.is-active                /* Generic state class, use data attribute */
```

✅ **Prefer:**
```css
.btn--primary
.card-overlay__text       /* card-overlay block, text element */
[data-state="active"]     /* Data attribute for state */
```

### Max 1 Element Level

**Avoid deeply nested BEM:**

```css
/* ❌ BAD: too deep */
.block__element__subelement__subsubelement

/* ✅ GOOD: flatten or create new block */
.block__element
.subelement              /* New block if it makes sense */
.block__subelement       /* Or keep flat */
```

## Component Reuse

**Before creating a new component, check existing:**

### Reusable Components Checklist

Located in `/app/static/css/components/`:

| Component | File | Variants Available |
|-----------|------|-------------------|
| Buttons | `buttons.css` | `.btn--primary`, `.btn--ghost`, `.btn--danger`, `.btn--toggle`, `.btn-sm` |
| Cards | `cards-base.css` | `.card--compact`, `.card--elevated`, `.card-image`, `.card-overlay` |
| Badges | `badges.css` | `.badge--pos`, `.badge--language`, `.badge--frequency`, `.badge--sm` |
| Forms | `forms.css` | inputs, `.toggle-switch`, `.filter-options` |
| List items | `list-items.css` | `.word-list-item`, `.collection-item` |
| Page header | `page-header.css` | `.page-header-main`, `.page-header-actions` |

### Decision Process

**Example: Need an outlined button?**

1. ✅ **Check:** Does `.btn--ghost` exist? (Yes - transparent bg, border)
2. ✅ **Try it:** Can ghost variant work with minor tweaks?
3. ⚠️ **Extend:** If different, add `.btn--outline` modifier
4. ❌ **Last resort:** Create `.outlined-button` from scratch

**Example: Need a metadata display?**

1. ✅ **Check:** Does page-header have metadata pattern? (Yes - `.page-header-metadata`)
2. ✅ **Reuse:** Use existing `.meta-item` structure
3. ✅ **Extend:** Add project-specific modifier if needed (`.meta-item--inline`)

### Extending vs Creating

```css
/* ✅ GOOD: Extend existing component */
.btn--outline {
  /* Inherits all .btn styles */
  background: transparent;
  border: 2px solid var(--color-accent);
}

/* ❌ BAD: Duplicate entire component */
.outline-button {
  padding: var(--space-2);      /* Duplicates .btn */
  border-radius: var(--radius-sm);  /* Duplicates .btn */
  /* ... */
}
```

## Performance Patterns

### Prefer Transform for Animations

```css
/* ❌ SLOW: triggers layout */
.item {
  transition: left 0.3s;
}
.item:hover {
  left: 10px;
}

/* ✅ FAST: GPU-accelerated */
.item {
  transition: transform var(--transition-normal);
}
.item:hover {
  transform: translateX(10px);
}
```

### Use will-change Sparingly

```css
/* ❌ BAD: always on (wastes memory) */
.sidebar {
  will-change: transform;
}

/* ✅ GOOD: only during animation */
.sidebar:hover {
  will-change: transform;
}
.sidebar.is-animating {
  will-change: transform;
}
.sidebar {
  will-change: auto;  /* Remove after animation */
}
```

### Minimize Repaints

```css
/* Group related property changes */
.element {
  /* Layout properties together */
  width: 100%;
  height: 200px;

  /* Visual properties together */
  background: var(--color-surface);
  color: var(--color-text);
}
```

### CSS Containment

```css
/* Isolate component rendering */
.card {
  contain: layout style paint;
}

/* For lists of items */
.list-item {
  contain: layout;
}
```

### Avoid Expensive Properties

```css
/* ⚠️ EXPENSIVE: use sparingly */
box-shadow: 0 0 50px rgba(0,0,0,0.5);
filter: blur(10px);
backdrop-filter: blur(20px);

/* ✅ PREFER: simpler effects */
box-shadow: var(--shadow-sm);  /* Pre-defined, optimized */
```

## Anti-Patterns

### NEVER

❌ **Hardcode colors/spacing**
```css
/* BAD */
color: #e8e6e3;
padding: 16px;

/* GOOD */
color: var(--color-text);
padding: var(--space-4);
```

❌ **Use !important (except utilities)**
```css
/* BAD */
.component {
  color: red !important;
}

/* GOOD */
.component {
  color: var(--color-error);
}

/* ACCEPTABLE: utility classes */
.hidden {
  display: none !important;
}
```

❌ **Deep nesting (>3 levels)**
```css
/* BAD */
.page .container .section .item .content {
  /* Too specific */
}

/* GOOD */
.item__content {
  /* BEM, specific enough */
}
```

❌ **Magic numbers**
```css
/* BAD: what is 47? */
.offset {
  margin-top: 47px;
}

/* GOOD: use token or document why */
.offset {
  margin-top: var(--space-12);  /* Or header height + gap */
}
```

### ALWAYS

✅ **Check existing components first** - Search `/components/*.css`

✅ **Follow BEM naming** - `.block__element--modifier`

✅ **Use CSS variables from tokens.css** - All colors, spacing, typography

✅ **Add `min-height: 0` for scrolling flex children** - Critical pattern

✅ **Document exceptions** - If hardcoding value, explain why

## Quick Reference

**Token location:** `/app/static/css/core/tokens.css`

**Spacing scale (8px-based):**
- `--space-2` = 8px
- `--space-4` = 16px
- `--space-6` = 24px
- `--space-8` = 32px

**Common colors:**
- `--color-text` - Primary text
- `--color-accent` - Brand accent (warm gold)
- `--color-bg-elevated` - Raised surfaces
- `--color-border` - Borders, dividers

**BEM format:**
```
.block__element--modifier
```

**Flexbox scroll pattern:**
```css
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scrollable {
  flex: 1;
  min-height: 0;    /* Critical! */
  overflow-y: auto;
}
```

**Check components before creating:**
- Buttons: `/components/buttons.css`
- Cards: `/components/cards-base.css`
- Forms: `/components/forms.css`
- Badges: `/components/badges.css`
