---
question: "What is the current health of the frontend — CSS architecture, component quality, template structure, and www/app design continuity?"
created: 2026-06-07
modified: 2026-06-07
context: "Audit conducted after PRD-017 UI overhaul (7-worker swarm, 15+ template/CSS files including new compositions, dictionary, scholars, and dashboard pages). Previous audit: 2026-05-18 (issue #83)."
status: active
audience: [eric, engineers]
owners: [eric]
related_issues: ["#83"]
related_skills: [gs-audit-frontend, gs-expert-ui]
supersedes: null
superseded_by: null
---

# Frontend & Design Audit — 2026-06-07

**Scope:** CSS token integrity, CSS architecture and imports, component inventory, template structure, JavaScript organization, form system, accessibility, www/app design continuity, Tailwind removal status.

**Previous audit:** 2026-05-18 → [GitHub issue #83](https://github.com/wittkensis/glintstone/issues/83)

---

## Previous audit cross-check (issue #83)

| Finding | Status |
|---------|--------|
| #8 — `btn btn-primary` flat name in templates | ✅ Fixed — all templates correctly use `btn btn--primary` (BEM modifier) |
| #9 — `btn-sm` vs `btn--sm` naming mismatch | ✅ Fixed — `buttons.css` now defines `btn--sm` (BEM modifier); templates match |
| #10 — Phantom form classes in `collections/form.html` | ✅ Fixed — `forms.css` now defines `form-card`, `form-group`, `form-label`, `form-input`, `form-textarea`, `form-actions` with full coverage |
| #11 — `form { display: flex }` global selector | ✅ Fixed — removed from `forms.css` |
| #12 — Missing input types in base selector | ✅ Fixed — `forms.css` now covers email, password, search, url, textarea; disabled/invalid/error states defined |
| Tailwind CDN in `www/index.html` | ✅ Fixed — `www/index.html` now loads `css/home.css`; no Tailwind CDN anywhere in `www/` |
| Inline scripts in `_macros.html` | ✅ Fixed — `_macros.html` contains only Jinja2 macros; no `<script>` blocks |

All Phase 1–2 frontend items from the prior audit are resolved. One new dead-code finding (F-1) introduced by PRD-017.

---

## Phase 1 — Fix Before Next Significant UI Work (Medium / XS effort)

### F-1 — `parallel.css` is dead code (Medium)

**Files:** `app/static/css/components/atf-viewer/index.css:10`, `app/static/css/components/atf-viewer/parallel.css`, `app/static/js/atf-viewer.js:491–492`

`atf-viewer/index.css` imports `parallel.css`:
```css
@import 'parallel.css';
```

But PRD-017 removed parallel mode from the viewer. `atf-viewer.js:491` documents this explicitly:
```js
// 'parallel' mode was removed — inline translations replace the side panel
if (mode === 'parallel') return;
```

The mode guard at line 492 means the `atf-viewer--mode-parallel` class is never applied. All CSS rules inside `parallel.css` that depend on that class are dead — the file is loaded over the network and parsed by every browser but none of its rules fire.

**Concrete impact:** Wasted bytes on every page load; confusion if a future developer sees `parallel.css` in the import and assumes parallel mode is active.

**Non-breaking change verification:** `parallel.css` only contains `.atf-viewer--mode-parallel` scoped rules. Removing the import cannot affect any currently-rendered styles.

**Fix:**
1. Remove `@import 'parallel.css';` from `atf-viewer/index.css`.
2. Delete `parallel.css` from the repo.
3. Confirm `git grep 'mode-parallel'` returns zero results before deleting.

---

### F-2 — `btn-group` has `gap: -1px` — invalid CSS (Medium)

**File:** `app/static/css/components/buttons.css:203`

```css
.btn-group {
    gap: -1px;
}
```

`gap` does not accept negative values. This property is silently ignored by all browsers (it resolves to `gap: 0`). The intended effect — overlapping adjacent button borders so the group looks like one unified control — is not being achieved.

**Concrete impact:** Button groups (stage filters on the tablet list page, for example) have a 1px gap between buttons instead of merged borders. It's a subtle visual regression that makes the group look like individual buttons.

**Non-breaking change verification:** The fix changes visual appearance; the buttons remain functional. No template changes required.

**Fix:** Replace `gap: -1px` with `margin-left: -1px` on adjacent items, or use an `outline` approach:
```css
.btn-group {
    /* gap: -1px is invalid — use margin to collapse adjacent borders */
    display: flex;
}
.btn-group .btn:not(:first-child) {
    margin-left: -1px;
}
.btn-group .btn:not(:first-child):focus {
    position: relative; /* bring into view over the overlapping left border */
}
```

---

## Phase 2 — Token & Style Drift (Low / XS effort)

### F-3 — Raw numeric values in PRD-017 CSS files (Low)

**Files:** `app/static/css/pages/compositions.css`, `app/static/css/pages/dictionary.css`

PRD-017 added two new page CSS files with several raw numeric font-size and spacing values instead of design tokens.

| File | Line | Value | Correct token |
|------|------|-------|---------------|
| `compositions.css` | 300, 637 | `font-size: 1rem` | `var(--text-base)` |
| `compositions.css` | 99 | `gap: 2px` | `var(--space-0-5)` (= 2px) |
| `compositions.css` | 578 | `gap: 3px` | No token at 3px — use `var(--space-1)` (4px) or `var(--space-0-5)` (2px) |
| `dictionary.css` | 413 | `font-size: 3rem` | `var(--text-display)` if that token exists, or add one |
| `dictionary.css` | 469 | `font-size: 4rem` | No token at 4rem — add `--text-display-lg: 4rem` or use `clamp()` |

The `3rem`/`4rem` sizes are cuneiform sign display sizes in the dictionary — they are intentionally large. If the display sizes are not represented in `tokens.css`, add them now so they can be adjusted globally.

**Non-breaking change verification:** Replacing raw values with tokens is visually identical; only the authoring surface changes.

**Fix:** Add `--text-display-lg: 4rem` to `tokens.css` if 4rem is an intentional display tier, and update both files. For `gap: 3px`, decide whether to round to `var(--space-1)` (4px) or `var(--space-0-5)` (2px).

---

### F-4 — Inline `style="font-style: normal"` in dictionary template (Low)

**File:** `app/templates/dictionary/index.html:273, 292`

Two `<span>` elements use `style="font-style: normal;"` to override an inherited italic style on sign names / guide words. These should be CSS classes.

**Non-breaking change verification:** Extracting to a class is visually identical.

**Fix:** Add `.dict-sign-name, .dict-guide-word { font-style: normal; }` to `pages/dictionary.css`, replace inline style with class.

---

## Phase 3 — Architecture & Ongoing Patterns (Low, documented)

### F-5 — Inline auth IIFE in `base.html` (Low, known)

**File:** `app/templates/base.html:91–120` (approx)

The header avatar/login state is driven by an inline `<script>` IIFE that calls `/_me` via `fetch` on every page load. This is the documented recurring pattern from issue #83.

**Status:** Unchanged since the prior audit. The behavior is correct — it's a fast `/_me` call and the fallback (no avatar shown) is graceful. It remains in `base.html` because it's tightly coupled to the header HTML structure.

**Action (post-MVP):** Extract to `app/static/js/header-auth.js`. Low priority; document in `base.html` with a comment explaining why it's inline.

---

### F-6 — `login.html` is a fully standalone page with large inline `<style>` (Low, by design)

**File:** `app/templates/auth/login.html`

The login page is ~373 lines, of which ~255 are an inline `<style>` block. It defines `.gate-*` classes that exist nowhere else. This is the documented pattern from the previous audit (login was rebuilt with inline styles after the old `auth.css` was removed).

**Status:** This is intentional. The login page being self-contained has resilience benefits (renders correctly even if `main.css` fails to load — the fallback token block at the top confirms this is deliberate). The page explicitly documents this in the CSS comment: *"Fallback tokens — in case main.css fails to load (e.g. nginx misconfiguration)"*.

**No action required.** Document intent in `CLAUDE.md` if not already noted.

---

## Phase 4 — www / App Design Continuity

### F-7 — Tailwind removal: COMPLETE for MVP scope (Resolved)

`www/index.html` loads `css/home.css` with no Tailwind CDN. There is one HTML file in `www/` (index.html). The docs pages mentioned in the previous audit as a Tailwind removal target do not exist — `www/` contains only `index.html`, `css/`, `js/`, `img/`, and `assets/`.

The `www/assets/style.css` path mentioned in the skill's migration goal does not exist (the directory exists but has no `style.css`). This is fine — `home.css` serves the current need and is already Tailwind-free.

**Status:** Complete for MVP. No action required.

---

## Summary scorecard

| Finding | Severity | Phase | Action |
|---------|----------|-------|--------|
| F-1: `parallel.css` is dead code | **Medium** | 1 | Remove `@import 'parallel.css'` from `atf-viewer/index.css`; delete file |
| F-2: `btn-group gap: -1px` invalid CSS | **Medium** | 1 | Replace with `margin-left: -1px` on non-first children |
| F-3: Raw font-size/gap values in PRD-017 CSS | Low | 2 | Replace with tokens; add `--text-display-lg` if needed |
| F-4: Inline `style="font-style: normal"` in dictionary template | Low | 2 | Move to `dictionary.css` class |
| F-5: Inline auth IIFE in `base.html` | Low | 3 | Extract to `header-auth.js` (post-MVP) |
| F-6: `login.html` inline `<style>` block | Low | 3 | No action — by design |
| F-7: Tailwind CDN in `www/` | N/A | — | Resolved |

**Highest-priority action (10 minutes):**

```bash
# 1. Confirm no parallel mode references remain
git grep 'mode-parallel'

# 2. Remove the import
# In app/static/css/components/atf-viewer/index.css:
# Delete the line: @import 'parallel.css';

# 3. Delete the dead file
rm app/static/css/components/atf-viewer/parallel.css
```

This is the smallest fix with the cleanest payoff — dead code confirmed by the viewer itself.
