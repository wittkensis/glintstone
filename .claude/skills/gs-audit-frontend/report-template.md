---
question: "What format should a Glintstone frontend audit report follow?"
created: 2026-05-18
modified: 2026-05-18
context: "Template for the structured report produced in Step 3 of gs-audit-frontend. Mirrors the structure of gs-audit-hardening/report-template.md but adds frontend-specific fields: non-breaking verification, visual regression risk, and the www/app surface label."
status: active
audience: [claude]
owners: [eric]
related_issues: ["#6", "#13", "#83"]
related_skills: [gs-audit-frontend, gs-expert-ui]
supersedes: null
superseded_by: null
---

# Frontend audit report template

Use this structure verbatim for the GitHub issue body. Fill every field — leave no finding without a concrete fix and a non-breaking verification.

---

```markdown
# Frontend & Design Audit — YYYY-MM-DD

> **Previous audit:** [link to prior issue]
> **Surfaces:** app (Jinja2 + token-driven CSS) · www (Tailwind CDN + static HTML)
> **Scope:** tokens · CSS architecture · components · templates · JS · www/app continuity · file hygiene · a11y

---

## Summary

| Phase | Description | Items |
|---|---|---|
| Phase 1 | Critical + High — fix before next significant UI work | N |
| Phase 2 | Token and design-system drift | N |
| Phase 3 | Component and template quality | N |
| Phase 4 | File hygiene, naming, annotations | N |
| Phase 5 | www/app design continuity | N |

**Items resolved since last audit:** N of M
**Net new items:** N

---

## Previously open items

> Mark each item from the prior audit as: ✅ Fixed · 🔄 Partially addressed · ❌ Still open · ⚠️ Fix introduced regression

| # | Finding | Status | Notes |
|---|---|---|---|
| 1 | Description from prior audit | ✅ Fixed | Commit sha or PR |
| 2 | Description | ❌ Still open | Current state |

---

## Phase 1 — Fix before next significant UI work

*Critical or High severity, XS–S effort. Something is silently broken or will break with routine change.*

### 1.1 [Short title] — **Critical · app**

**Area:** CSS architecture
**File:** `app/static/css/main.css`
**Surface:** app

**Problem:** Plain-English description of the exact failure mode. Name what is broken and when it will hurt.

**Fix:**
```css
/* Add missing import to main.css, in the components section */
@import url('components/knowledge-sidebar.css');
```

**Non-breaking verification:** This adds a new import — no existing styles are modified. Verify by loading the page that uses `.knowledge-sidebar` and confirming layout renders. No visual regression risk to other pages.

**Implement using:** `gs-expert-ui/css-tokens.md` for any token decisions in the added file.

---

### 1.2 [Short title] — **High · www**

**Area:** www/app token drift
**File:** `www/index.html` (Tailwind config block, lines ~17–47)
**Surface:** www

**Problem:** …

**Fix:** …

**Non-breaking verification:** …

---

## Phase 2 — Token and design-system drift

*Medium severity, XS–S effort. Hardcoded values that will diverge from the token system over time.*

### 2.1 [Short title] — **Medium · app**

**Area:** CSS token integrity
**File:** `app/static/css/components/[file].css:NN`
**Surface:** app

**Problem:** Hardcoded hex `#1a1a1a` used for background. When `--color-bg` changes, this won't update.

**Fix:**
```css
/* Before */
background: #1a1a1a;

/* After */
background: var(--color-bg);
```

**Non-breaking verification:** Visual should be identical today. Token value and hardcoded value match. Grep for `#1a1a1a` to confirm all instances are replaced.

**Implement using:** `gs-expert-ui/css-tokens.md` — token-first rule.

---

## Phase 3 — Component and template quality

*Medium severity, M effort. Inconsistency or duplication that will accumulate into entropy.*

### 3.1 [Short title] — **Medium · app**

**Area:** BEM naming
**File:** `app/templates/components/_macros.html:NN`, `app/static/css/components/cards-base.css`
**Surface:** app

**Problem:** `card-details card-overlay` is applied as two unrelated classes on the same element. `card-overlay` is not a BEM modifier of `.card` — it reads as a BEM element (`card__overlay`) but lacks the double-underscore. This pattern makes it hard to know which classes come from `cards-base.css` vs `cards-tablet.css` without grepping.

**Fix:**
Rename the class to follow BEM and update all usages:
```html
<!-- Before -->
<div class="card-details card-overlay">

<!-- After -->
<div class="card__details card__overlay">
```

Update `cards-base.css` and `cards-tablet.css` to match. Grep for `card-overlay` across all template files before renaming.

**Non-breaking verification:** This is a pure rename — no style values change. Must update all usages atomically. Risk: if any JS queries `.card-overlay`, that query will break. Check `app/static/js/` for `.card-overlay` before proceeding.

---

## Phase 4 — File hygiene, naming, annotations

*Low–Medium severity, XS–S effort. Naming consistency, comments, and dead files.*

### 4.1 [Short title] — **Low · app**

**Area:** File hygiene
**File:** `app/static/css/pages/auth.css`, `debug.css`, `account.css`
**Surface:** app

**Problem:** These files exist but are not imported in `main.css`. Either they are loaded per-page in `{% block head %}` (and that should be documented), or they are orphaned and wasting deploy bandwidth.

**Fix:**
Confirm whether each is loaded per-template via `{% block head %}`:
- If yes: add a comment to the top of each file: `/* Loaded per-page via block head in templates/auth/login.html */`
- If no: either import in `main.css` or delete.

**Non-breaking verification:** Deleting an unused file has no visual impact. Adding to main.css loads the styles globally — verify no unintended style bleed on other pages.

---

### 4.2 [Short title] — **Low · app/www**

**Area:** Git hygiene — .DS_Store files
**File:** `app/static/`, `app/templates/`, `www/`
**Surface:** app + www

**Problem:** `.DS_Store` files are present in the tracked file tree. They add no value, leak local filesystem structure, and create noise in diffs.

**Fix:**
```bash
find app www -name '.DS_Store' | xargs git rm --cached
```

Add to `.gitignore`:
```
**/.DS_Store
```

**Non-breaking verification:** No CSS, HTML, or behavior changes. Git history cleanup only.

---

## Phase 5 — www/app design continuity

*High leverage items that require coordinating both surfaces.*

### 5.1 [Short title] — **High · www→app**

**Area:** Tailwind/token sync mechanism
**File:** `www/index.html` (Tailwind config block)
**Surface:** www

**Problem:** The Tailwind config manually duplicates values from `tokens.css`. There is no automated sync — when `tokens.css` changes, `www/` silently drifts. As of this audit, `lapis` (`#4a6fa5`) and `clay` (`#c19a6b`) exist in the Tailwind config but have no equivalent tokens in `tokens.css`. Either they should be added as tokens (if they'll be used in app), or documented as www-only.

**Fix option A (short-term):** Add a comment block above the Tailwind config in `www/index.html` listing which values must stay synced with `tokens.css`, and which are www-only. Low effort, prevents silent drift.

**Fix option B (long-term):** Replace Tailwind CDN with a shared CSS file that imports the same tokens. Requires either extracting `tokens.css` to a shared location or copying it to `www/assets/`. This is the right architectural move but requires more work. Deferring to a dedicated issue.

**Non-breaking verification:** Option A: comment-only change, no visual impact. Option B: requires visual regression testing across all www pages.

---

## Appendix: items verified clean

Items from the scope checklist that were explicitly checked and confirmed correct. Include so the next audit knows what was already verified.

- **A.1** Token font families: `--font-sans`, `--font-mono`, `--font-cuneiform`, `--font-serif` — all consistent with www font loads. ✅
- **G.2** Shared fonts (Playfair Display, Noto Sans Cuneiform) — both surfaces load identical Google Fonts URLs. ✅
- …
```

---

## Finding format rules (frontend-specific)

1. **Surface label is mandatory.** Every finding must be tagged `app`, `www`, or `app + www`. This makes it easy to batch findings by surface when implementing.

2. **Non-breaking verification is mandatory.** Every finding must explain why the fix is safe. For CSS: "No style values change — pure rename" or "Token value matches the hardcoded value being replaced." For JS: "Check for querySelector usages before renaming." For templates: "Verify all child templates still render."

3. **Visual regression risk.** If there is any chance the fix changes the visible layout — even slightly — say so and name the pages to test.

4. **Implement pointer.** Every finding that involves CSS or HTML changes should include: "Implement using gs-expert-ui/[css-tokens.md or markup-quality.md]." This keeps the audit from re-inventing implementation guidance that gs-expert-ui already owns.

5. **No vague improvement findings.** "Could be more consistent" is not a finding. "`.card-overlay` is applied to 4 elements in 3 different templates but defined in 2 different CSS files, making it impossible to know which definition wins without checking specificity" is a finding.

6. **Phase 5 findings need both surfaces described.** A design continuity finding must name what exists in app, what exists in www, and what the specific mismatch is.
