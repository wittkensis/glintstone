---
question: "How do I use the CSS token system, BEM, and the flexbox patterns Glintstone's app/ already relies on?"
created: 2026-05-11
modified: 2026-05-11
context: "Migrated from skills-disabled/css-patterns/SKILL.md during the 2026-05-11 overhaul. Trimmed to project-specific guidance; the general advice (use tokens, follow BEM) is in the parent SKILL.md."
status: active
audience: [claude, engineers, designers]
owners: [eric]
related_issues: ["#13"]
related_skills: [gs-expert-ui]
supersedes: ".claude/skills-disabled/css-patterns/SKILL.md"
superseded_by: null
---

# CSS tokens, BEM, flexbox

## Token usage

Replace hardcoded values; reach for the closest token. If none fits, propose adding one to `tokens.css` rather than hardcoding.

```css
/* ❌ BAD */
.component {
  padding: 16px 24px;
  background: #242424;
  color: #fff;
  border: 1px solid #ffffff20;
  transition: all 0.2s;
}

/* ✅ GOOD */
.component {
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  transition: all var(--transition-normal);
}
```

If a value is genuinely unique (one-off animation curve, exact pixel for ATF column alignment), document the exception with a comment.

## BEM

Format: `.block__element--modifier`.

```css
.btn { }              /* Block */
.btn__icon { }        /* Element */
.btn--primary { }     /* Modifier */
```

Real-world from the codebase:

- Buttons: `.btn`, `.btn__icon`, `.btn--primary`, `.btn--ghost`
- Cards: `.card`, `.card-image`, `.card--compact`, `.card--elevated`
- Badges: `.badge`, `.badge--pos`, `.badge--sm`
- ATF: `.atf-viewer`, `.atf-line`, `.atf-token`, `.atf-token--damaged`

Anti-patterns:

- ❌ `.btn.primary` → `.btn--primary`
- ❌ `.card-image-overlay-text` → `.card-overlay__text`
- ❌ `.is-active` class for state → `data-state="active"` attribute (see [markup-quality.md](markup-quality.md#data-attributes-for-state))
- ❌ Deep nesting (>1 element level) → flatten

## Flexbox mastery

Three rules cover 90% of layout bugs.

### 1. `min-height: 0` for scrolling flex children

```css
/* ❌ won't scroll */
.scrollable { flex: 1; overflow-y: auto; }

/* ✅ */
.scrollable { flex: 1; min-height: 0; overflow-y: auto; }
```

Flex items default to `min-height: auto`, which prevents shrinking below content size.

### 2. `min-width: 0` for text truncation

```css
/* ❌ text overflows the row */
.flex-item { flex: 1; }

/* ✅ */
.flex-item { flex: 1; min-width: 0; }
```

### 3. `flex: 1` means grow + shrink + basis 0

```css
flex: 1;           /* grow/shrink, start at 0 */
flex: 0 0 200px;   /* fixed 200px */
flex: 1 0 auto;    /* grow only, never shrink */
```

## Full-height scroll pattern

```css
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.page__header { flex: 0 0 auto; }
.page__main   { flex: 1; min-height: 0; overflow-y: auto; }
.page__footer { flex: 0 0 auto; }
```

## Quick fixes

| Symptom | Fix |
|---|---|
| Won't scroll | Add `min-height: 0` |
| Text overflows | Add `min-width: 0` |
| Won't shrink | `flex-shrink: 1` + `min-width: 0` |
| Uneven spacing | Use `gap`, not margin |

## Performance

```css
/* ✅ Use transform — GPU-accelerated */
.item { transition: transform var(--transition-normal); }
.item:hover { transform: translateX(10px); }

/* ✅ will-change only during animation, not always-on */
.sidebar.is-animating { will-change: transform; }

/* ✅ CSS containment on heavy components */
.card { contain: layout style paint; }

/* ⚠️ Expensive — measure before using */
/* filter: blur(), backdrop-filter, large box-shadows */
```

## Quick reference card

- Token file: `app/static/css/core/tokens.css` (~261 lines)
- BEM: `.block__element--modifier`
- Scroll: `flex: 1; min-height: 0; overflow-y: auto;`
- Component dir: `app/static/css/components/`
- Page dir: `app/static/css/pages/`
- Utility dir: `app/static/css/utils/`
