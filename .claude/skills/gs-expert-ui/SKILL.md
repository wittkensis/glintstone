---
name: gs-expert-ui
description: Glintstone web app UI patterns — token enforcement, BEM, flexbox, semantic HTML, accessibility. Anchored to app/static/css/core/tokens.css. Use for any UI work in app/.
metadata:
  question: "How do I write CSS and HTML for Glintstone's web app — tokens, BEM, accessibility, and the patterns this project actually uses?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Merges and re-homes content from skills-disabled/css-patterns and skills-disabled/markup-quality during the 2026-05-11 overhaul. Grounded in app/static/css/core/tokens.css, the project's actual token system. Kenilworth references removed per user direction."
  status: active
  audience: [claude, engineers, designers]
  owners: [eric]
  related_issues: ["#6", "#13"]
  related_skills: [gs-expert-data-model, gs-curator-docs, gs-audit-frontend]
  supersedes: [".claude/skills-disabled/css-patterns/SKILL.md", ".claude/skills-disabled/markup-quality/SKILL.md"]
  superseded_by: null
  triggers: [css, styles, styling, flexbox, tokens, BEM, layout, spacing, html, semantic, accessibility, a11y, markup, "tokens.css", responsive, ui]
---

# Glintstone UI patterns

The web app is server-rendered Jinja2 + vanilla JS + a token-driven CSS system. Two principles drive everything:

1. **Use tokens.** Every hardcoded `#fff`, `16px`, `0.3s` is debt. The token system lives at `app/static/css/core/tokens.css`.
2. **HTML is for structure, CSS is for presentation.** Every `<div>` should justify its existence.

## When to load which file

| Question | File |
|---|---|
| Picking a token, BEM naming, flexbox scrolling, performance patterns | [css-tokens.md](css-tokens.md) |
| Semantic element choice, wrapper reduction, a11y, heading hierarchy, data attributes | [markup-quality.md](markup-quality.md) |

## Anchor: token file

The single source of truth for visual decisions is [`app/static/css/core/tokens.css`](../../../app/static/css/core/tokens.css). Token prefixes:

| Prefix | Purpose |
|---|---|
| `--color-bg-*` | Backgrounds (`base`, `inset`, `elevated`, `deepest`) |
| `--color-text-*` | Text (`primary`, `secondary`, `muted`, `subtle`) |
| `--color-accent-*` | Accent (`base`, `hover`, `muted`) |
| `--color-{success,error,warning,info}` | Semantic state |
| `--color-{border,surface}` | UI elements |
| `--space-*` | 8px scale: `0, 1, 2, 3, 4, 5, 6, 8, 10, 12` |
| `--text-*` | Sizes: `xxs, xs, sm, base, lg, xl, 2xl, 3xl, display` |
| `--font-*` | Families: `sans, mono, serif, cuneiform`; weights |
| `--line-height-*` | `tight, normal, relaxed` |
| `--radius-*` | `xs, sm, md, lg, full` |
| `--shadow-*` | `xs, sm, md, lg, xl, inset` |
| `--transition-*` | `instant, fast, normal, slow, slower` |

## Anchor: component CSS

Before creating any new component, check `app/static/css/components/`:

- `buttons.css` — `.btn--primary`, `.btn--ghost`, `.btn--danger`, `.btn--sm`
- `cards-base.css` — `.card--compact`, `.card--elevated`, `.card-image`
- `badges.css` — `.badge--pos`, `.badge--language`, `.badge--sm`
- `forms.css` — inputs, `.toggle-switch`, `.filter-options`
- `list-items.css` — `.word-list-item`, `.collection-item`

Process: **Check → try existing → extend with modifier → create (last resort)**.

## Non-negotiables

- ❌ Never hardcode colors, sizes, spacings — use tokens
- ❌ Never `!important` (except in utility classes)
- ❌ Never `<div onclick>` — use `<button>` for actions, `<a href>` for navigation
- ❌ Never skip heading levels
- ✅ Always `min-height: 0` on flex children that scroll (see [css-tokens.md](css-tokens.md#flexbox-mastery))
- ✅ Always use semantic elements first, ARIA only when semantics don't exist

## When to bring in another skill

- Rendering tablet content / glossed text / sign typography → also load `gs-expert-assyriology/lexical-model.md` (typography conventions section)
- API data shape for new UI views → `gs-expert-data-model`
- New endpoints to back the UI → `gs-expert-integrations` (server side) or check existing `api/routes/`
- Auditing what's wrong before implementing → `gs-audit-frontend` (identifies findings; this skill implements the fixes)

**Handoff protocol with gs-audit-frontend:** The audit skill identifies violations and writes findings. This skill implements them. When you receive a finding tagged "Implement using gs-expert-ui/css-tokens.md", load this file and apply the token-first rules.

## Open issues that touch this skill

- #6 — UI Systems Componentization (headers, dictionary surfaces inconsistent)
- #13 — Remove Tailwind completely
- #15 — Gut check on frontend framework
- #36 — ATF viewer revamp (mostly shipped)
- #37 — Knowledge sidebar
