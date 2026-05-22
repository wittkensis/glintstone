---
name: gs-audit-frontend
description: Frontend & design audit — systematic review of CSS tokens, component architecture, template quality, JS organization, www/app design continuity, Tailwind removal, form system completeness, and file hygiene. Produces a structured findings report and GitHub issue. Use when asked to audit, review, clean up, or improve the frontend.
metadata:
  question: "How do I conduct a thorough, consistent audit of Glintstone's frontend — design system, templates, CSS, JS, www/app continuity, and file hygiene?"
  created: 2026-05-18
  modified: 2026-05-18
  context: "Created after surveying the full frontend. Key structural facts: app/ uses a layered token-driven CSS system; www/ uses Tailwind CDN (www/index.html + all docs pages) and goal is full removal replaced with shared token-driven CSS and a shared header component. The Tailwind config — an active drift risk. Several CSS files exist but are not imported in main.css. Inline scripts live inside Jinja macros."
  status: active
  audience: [claude, engineers, designers]
  owners: [eric]
  related_issues: ["#6", "#13", "#83"]
  related_skills: [gs-expert-ui, gs-audit-hardening, gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: [frontend, "design audit", "design system", "css audit", "template audit", "design review", "ui audit", "style audit", "design consistency", "file hygiene", "frontend entropy", "clean up the frontend"]
---

# Glintstone frontend & design audit

This skill governs how frontend audits are scoped, conducted, and reported. Run it when asked to do a design/frontend pass, after significant UI changes, or when the frontend feels inconsistent or hard to navigate. It produces a structured report and a GitHub issue.

**Previous audit:** 2026-05-18 → [GitHub issue #83](https://github.com/wittkensis/glintstone/issues/83) (includes frontend findings)

---

## Skill conflict map — read before auditing

This skill overlaps with two others. Understand the handoff protocol before starting.

| Skill | Owns | This audit's role |
|---|---|---|
| **gs-expert-ui** | Implementation: token enforcement, BEM patterns, flex layout, semantic HTML, a11y rules | Identify violations. Do NOT re-implement patterns — link to gs-expert-ui for the fix. |
| **gs-audit-hardening** | Infrastructure, deploy pipeline, static asset delivery, nginx caching | Defer asset delivery and cache-header findings to that audit. Flag the overlap explicitly in findings. |
| **gs-curator-docs** | YAML header freshness on `.md` files | Not in scope here. |

**Handoff rule for implementation:**
When a finding requires a CSS or HTML fix, write the finding with a concrete description of what to change, then note: *"Implement using patterns from gs-expert-ui/css-tokens.md"* or *"gs-expert-ui/markup-quality.md."* Do not inline gs-expert-ui's full implementation guidance inside an audit finding.

**Non-breaking change rule:**
This audit must NOT introduce breaking changes. Every fix recommendation should:
1. State what it changes and why it is safe.
2. Note any visual regression risk.
3. For CSS: confirm the class is not used elsewhere before removing it.
4. For template changes: confirm the block structure is compatible with all child templates.

---

## Two surfaces, one design system

The project has two distinct frontend surfaces with different constraints:

| | **app/** | **www/** |
|---|---|---|
| Purpose | Scholarly research application | Marketing site + public docs |
| Template engine | Jinja2 (server-rendered) | Static HTML |
| CSS approach | Token-driven (tokens.css → main.css → layered imports) | Tailwind CDN + inline config |
| Fonts | Playfair Display, Noto Sans Cuneiform, system-ui | Same (loaded from Google Fonts) |
| Color palette | `app/static/css/core/tokens.css` is authoritative | Tailwind config in `www/index.html` manually mirrors token values |
| Spacing | `--space-*` (8px scale) | Tailwind utilities — may diverge |
| Shared state | None — separate servers, no shared CSS | — |

**The migration goal:** Full removal of Tailwind CDN from all www/ pages (index.html + ~25 docs pages). Replacement: `www/assets/style.css` imports `tokens.css` directly (or a copy), and a shared semantic-HTML header component is used on both app/ and www/ surfaces. See audit findings F-TW1 through F-TW4 for the phased removal plan.

**The core continuity risk:** `www/index.html` has a hand-coded Tailwind config object that mirrors app token values. When `tokens.css` changes, `www/index.html` must be updated manually. There is no automated sync. This is the single biggest design-system drift mechanism until Tailwind is removed.

---

## When to run

- After any significant UI change or new page/component added
- When the frontend feels inconsistent or components are being reimplemented from scratch
- When file count in `app/static/css/` or `app/templates/` grows and navigation gets hard
- After the `www/` content is significantly updated
- On request ("audit the frontend", "clean up the css", "review the design system")

---

## How to conduct the audit

### Step 1 — Load context (do not skip)

```bash
git log --oneline -10                           # recent changes
git diff HEAD~1 HEAD -- app/static/ app/templates/ www/
```

Then read in this order:
1. `app/static/css/core/tokens.css` — the authoritative design token source
2. `app/static/css/main.css` — the import manifest; reveals orphaned CSS files
3. All files in `app/static/css/components/` — one pass to note naming and patterns
4. **`app/static/css/components/forms.css`** — check control coverage, global selectors, state completeness
5. **`app/static/css/components/buttons.css`** — check variant/size naming consistency
6. `app/templates/base.html` — the root layout and global script/style loading
7. `app/templates/components/_macros.html` — all reusable components
8. Two or three page templates: `tablets/list.html`, `tablets/detail.html`, `index.html`
9. **All templates with forms** — `collections/form.html`, `account/index.html`, `auth/login.html` — check for class name mismatches against CSS definitions
10. `www/index.html` — the Tailwind config block and structure; inventory Tailwind utility classes
11. `www/assets/style.css` — current state (empty or populated)
12. Sample docs pages — check CDN usage and layout approach

### Step 2 — Work through the scope checklist

See [scope-checklist.md](scope-checklist.md). Cover every section. "Looks fine" is not an answer — verify.

### Step 3 — Write the report

Use [report-template.md](report-template.md). Every finding needs:
- Severity (Critical / High / Medium / Low)
- Specific file(s) and line(s) involved
- Root cause in plain English (what is wrong and why it matters)
- A concrete fix (what to change, not just what direction to go)
- A non-breaking change verification note

Do not include vague findings like "could be more consistent." Every finding must have a specific, verifiable problem and a specific, implementable fix.

### Step 4 — Cross-check against previous audit

Load GitHub issue #83 via `gh issue view 83`. Look specifically for any UI/frontend items. Mark each:
- ✅ Fixed — note the commit or PR
- 🔄 Partially addressed — what remains
- ❌ Still open — current status

### Step 5 — Create the GitHub issue

After presenting the report and incorporating feedback:

```bash
gh issue create \
  --title "Frontend & Design Audit — <YYYY-MM-DD>" \
  --label "enhancement,documentation" \
  --body "$(cat report.md)"
```

---

## Severity definitions

| Severity | Meaning | Frontend examples |
|---|---|---|
| **Critical** | Actively broken or will silently break on next code change | CSS file imported in main.css that doesn't exist; orphaned class referenced in template with no definition |
| **High** | Will cause visible problems under normal use or routine change | Tailwind config drift from tokens.css; hardcoded hex colors outside of tokens; JS behavior encoded in inline scripts with no tests |
| **Medium** | Causes friction, inconsistency, or future maintenance cost | Duplicate component patterns; inconsistent BEM; inline `<style>` blocks; unused CSS files |
| **Low** | Minor hygiene — cosmetic, naming, annotation | Missing file-header comments; snake_case/kebab-case inconsistency; minor duplication |

---

## Phasing convention

| Phase | Criteria |
|---|---|
| **Phase 1** | Critical or High, XS–S effort. Fix before next significant UI work. |
| **Phase 2** | Token and design-system drift. Medium severity, XS–S effort. |
| **Phase 3** | Component and template quality. Medium severity, M effort. |
| **Phase 4** | File hygiene, naming, and annotations. Low–Medium, XS–S effort. |
| **Phase 5** | www / app design continuity. High leverage but requires coordination. |

---

## Domain areas to audit

Full question list per area: [scope-checklist.md](scope-checklist.md)

| Area | Primary files |
|---|---|
| CSS token integrity | `app/static/css/core/tokens.css`, all component/page CSS files |
| CSS architecture & imports | `app/static/css/main.css`, `app/static/css/` tree |
| Component inventory | `app/static/css/components/`, `app/templates/components/_macros.html` |
| Template structure | `app/templates/base.html`, `app/templates/*/` |
| JavaScript organization | `app/static/js/*.js`, inline scripts in templates and macros |
| www design system | `www/index.html`, `www/assets/style.css`, `www/docs/**/*.html` |
| www / app continuity | Token values, fonts, colors, spacing rhythm, brand voice |
| **Tailwind removal** | All `www/**/*.html` — CDN script tags, utility class inventory, shared header plan |
| **Form system** | `app/static/css/components/forms.css`, `app/static/css/components/buttons.css`, all templates with `<form>`, `<input>`, `<select>`, `<textarea>`, `<button>` |
| File naming & hygiene | All `app/static/css/` and `app/templates/` files |
| Inline annotations | CSS section headers, macro docstrings, JS function comments |
| Accessibility | Landmark roles, heading hierarchy, ARIA, focus management |
| Responsive & mobile | Media queries, viewport assumptions, touch targets |

---

## Known recurring failure modes

Patterns that have appeared in this codebase — check these first:

1. **Tailwind/token drift** — `www/index.html` has a Tailwind config object with manually-copied color values from `tokens.css`. Any change to accent, background, or text tokens must be reflected in both files. No automated sync exists. Goal: full Tailwind removal.
2. **Orphaned CSS files** — files exist in `app/static/css/pages/` or `app/static/css/components/` but are not imported in `main.css`. These get deployed but never applied (examples as of 2026-05-18: `auth.css` is dead code — login page was rebuilt with inline `.gate-*` styles).
3. **Inline scripts in macros** — `_macros.html` includes `<script>` blocks inside macro bodies (filter sidebar auto-submit, "show all" button, animation). These are hard to test and make the macro file do double duty as a JS module.
4. **Mixed BEM naming** — `card-details card-overlay` uses two space-separated classes where one should be a BEM element (`card__details`) and the other a modifier (`card--overlay`). Inconsistency accumulates across components.
5. **Inline auth check in base.html** — the header's avatar/login state is driven by an inline IIFE that calls `/_me` via `fetch`. This is correct behavior but its inline position in `base.html` mixes presentation logic into the layout template.
6. **www docs pages inherit nothing from app tokens** — docs pages under `www/docs/` link only to Tailwind CDN. Goal: replace with `www/assets/style.css` that imports tokens and a shared docs layout.
7. **`--color-bg-rgb` / `--color-bg-inset-rgb` raw values** — these manually-declared RGB triplets must stay in sync with their companion hex tokens. A hex change without updating the RGB triplet creates a subtle visual inconsistency in rgba() usage.
8. **`btn-primary` vs `btn--primary` class name split** — four templates use `btn btn-primary` (flat), which doesn't exist in CSS. The correct class is `btn--primary` (BEM). Collection submit and action buttons are visually broken (fall back to base `.btn` gray). Check every form template on each audit.
9. **`btn-sm` vs `btn--sm` naming** — CSS defines `.btn-sm` (flat) but templates use `btn--sm` (BEM modifier) in 5+ places. Button size reduction is silently not applied.
10. **Phantom form classes** — `.form-card`, `.form-group`, `.form-label`, `.form-input`, `.form-textarea`, `.form-actions` are used in `collections/form.html` but defined nowhere in the CSS tree. The collection create/edit form has no layout or label styles.
11. **`form { display: flex }` global selector** — `forms.css` applies flex to ALL `<form>` elements site-wide. This overrides block-level default for every form and must be removed in favor of opt-in classes.
12. **Missing input types in base selector** — `forms.css` only styles `input[type="text"]` and `input[type="number"]`. Missing: `email`, `password`, `search`, `url`, `textarea` (not in selector — requires `.form-textarea`). No disabled, invalid, or error states defined.
