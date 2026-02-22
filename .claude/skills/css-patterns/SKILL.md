---
triggers: [css, styles, styling, flexbox, tokens, bem, layout, spacing, colors, performance, responsive, ui, optimize, refactor]
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

### Token Categories

Use tokens from `/app/static/css/core/tokens.css` organized by prefix:

```css
/* Colors */
--color-bg-*          /* Backgrounds: base, inset, elevated, deepest */
--color-text-*        /* Text: primary, secondary, muted, subtle */
--color-accent-*      /* Accent colors: base, hover, muted */
--color-success       /* Semantic: success, error, warning, info */
--color-error
--color-warning
--color-info
--color-border        /* UI elements */
--color-surface

/* Spacing (8px-based scale) */
--space-0 through --space-12   /* 0, 4px, 8px, 12px, 16px... 48px */

/* Typography */
--text-*              /* Sizes: xxs, xs, sm, base, lg, xl, 2xl, 3xl, display */
--font-*              /* Families: sans, mono, serif, cuneiform */
--font-*              /* Weights: normal, medium, semibold, bold */
--line-height-*       /* tight, normal, relaxed */

/* Radius */
--radius-*            /* xs, sm, md, lg, full */

/* Shadows */
--shadow-*            /* xs, sm, md, lg, xl, inset */

/* Transitions */
--transition-*        /* instant, fast, normal, slow, slower */
```

### Usage

**Replace hardcoded values:**
```css
/* ❌ BAD */
.component {
  padding: 16px 24px;
  background: #242424;
  color: #fff0;              /* Alpha hex */
  border: 1px solid #ffffff00;  /* 8-digit alpha */
  transition: all 0.2s;
}

/* ✅ GOOD */
.component {
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-elevated);
  color: transparent;
  border: 1px solid var(--color-border);
  transition: all var(--transition-normal);
}
```

**When tokens don't exist:** Use closest match, or document why value is unique.

## Flexbox Mastery

### Critical Rules

**1. `min-height: 0` for scrolling flex children**
```css
/* ❌ BAD: won't scroll */
.scrollable { flex: 1; overflow-y: auto; }

/* ✅ GOOD */
.scrollable { flex: 1; min-height: 0; overflow-y: auto; }
```
**Why:** Flex items default to `min-height: auto`, preventing shrink below content.

**2. `min-width: 0` for text truncation**
```css
/* ❌ BAD: text overflows */
.flex-item { flex: 1; }

/* ✅ GOOD */
.flex-item { flex: 1; min-width: 0; }
```

**3. `flex: 1` = grow + shrink + basis 0**
```css
flex: 1;           /* Grow/shrink, start at 0 */
flex: 0 0 200px;   /* Fixed 200px */
flex: 1 0 auto;    /* Grow only */
```

### Full-Height Scroll Pattern

```css
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header { flex: 0 0 auto; }
.main { flex: 1; min-height: 0; overflow-y: auto; }
.footer { flex: 0 0 auto; }
```

### Common Issues

| Problem | Solution |
|---------|----------|
| Won't scroll | Add `min-height: 0` |
| Text overflows | Add `min-width: 0` |
| Won't shrink | `flex-shrink: 1` + `min-width: 0` |
| Uneven spacing | Use `gap` not margin |

## BEM Consistency

**Format:** `.block__element--modifier`

- **Block** - Independent component (`.btn`, `.card`)
- **Element** - Part of block (`.btn__icon`, `.card__title`)
- **Modifier** - Variation (`.btn--primary`, `.card--elevated`)

```css
.btn { }                 /* Block */
.btn__icon { }           /* Element */
.btn--primary { }        /* Modifier */
```

**Examples:**
- Buttons: `.btn`, `.btn__icon`, `.btn--primary`, `.btn--ghost`
- Cards: `.card`, `.card-image`, `.card--compact`, `.card--elevated`
- Badges: `.badge`, `.badge--pos`, `.badge--sm`

**Anti-patterns:**
- ❌ `.btn.primary` → Use `.btn--primary`
- ❌ `.card-image-overlay-text` → Use `.card-overlay__text`
- ❌ `.is-active` → Use `[data-state="active"]`
- ❌ Deep nesting → Max 1 element level

## Component Reuse

**Check `/app/static/css/components/` before creating new:**

- **Buttons** (`buttons.css`): `.btn--primary`, `.btn--ghost`, `.btn--danger`, `.btn--sm`
- **Cards** (`cards-base.css`): `.card--compact`, `.card--elevated`, `.card-image`
- **Badges** (`badges.css`): `.badge--pos`, `.badge--language`, `.badge--sm`
- **Forms** (`forms.css`): inputs, `.toggle-switch`, `.filter-options`
- **Lists** (`list-items.css`): `.word-list-item`, `.collection-item`

**Process:** Check → Try existing → Extend with modifier → Create (last resort)

## Performance Patterns

```css
/* ✅ Use transform (GPU-accelerated) */
.item { transition: transform var(--transition-normal); }
.item:hover { transform: translateX(10px); }

/* ✅ will-change only during animation */
.sidebar:hover { will-change: transform; }

/* ✅ CSS containment for components */
.card { contain: layout style paint; }

/* ⚠️ Avoid expensive properties */
/* filter: blur(), backdrop-filter, large box-shadows */
```

## Rules

**NEVER:**
- ❌ Hardcode values → Use tokens
- ❌ `!important` (except utilities)
- ❌ Deep nesting (>3 levels) → Use BEM
- ❌ Magic numbers → Document exceptions

**ALWAYS:**
- ✅ Check existing components first
- ✅ Follow BEM (`.block__element--modifier`)
- ✅ Use tokens from `tokens.css`
- ✅ Add `min-height: 0` for scrolling flex children

## Quick Reference

**Token location:** `/app/static/css/core/tokens.css`

**Token prefix patterns:**
- Colors: `--color-bg-*`, `--color-text-*`, `--color-accent-*`
- Spacing: `--space-*` (8px scale: 0, 1, 2, 3, 4, 5, 6, 8, 10, 12)
- Typography: `--text-*`, `--font-*`, `--line-height-*`
- Radius: `--radius-*`
- Shadows: `--shadow-*`
- Transitions: `--transition-*`

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
