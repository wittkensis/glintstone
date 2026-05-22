---
question: "What exactly should I check in each area of a Glintstone frontend audit?"
created: 2026-05-18
modified: 2026-05-18
context: "Companion to SKILL.md — the per-area question list that drives frontend audit coverage. Each question maps to a class of finding discovered by surveying the actual codebase on 2026-05-18."
status: active
audience: [claude]
owners: [eric]
related_issues: ["#6", "#13", "#83"]
related_skills: [gs-audit-frontend, gs-expert-ui]
supersedes: null
superseded_by: null
---

# Frontend audit scope checklist

Work through every section. Answer each question explicitly — "yes/verified", "no/gap found", or "N/A". A gap is a finding; write it up.

---

## A. CSS token integrity (`app/static/css/core/tokens.css`)

- [ ] Are there any hardcoded hex colors (`#1a1a1a`, `rgba(...)`, etc.) anywhere in component or page CSS files that should be a token? (grep for `#[0-9a-fA-F]{3,6}` in `app/static/css/`)
- [ ] Do the raw-RGB companion tokens (`--color-bg-rgb`, `--color-bg-inset-rgb`) still match their hex counterparts? (They must stay in sync for rgba() usage.)
- [ ] Are there any duplicate token declarations — the same semantic name defined more than once?
- [ ] Are `--color-lang-sux` and `--color-lang-akk` and their opacity variants all used consistently in the ATF viewer? Or are some hardcoded?
- [ ] Are any tokens declared in `tokens.css` that are never referenced in any other CSS file? (Unused token bloat.)
- [ ] Are any hardcoded `px` values used for spacing where a `--space-*` token would apply?
- [ ] Are any hardcoded `rem` / `em` sizes used for font sizes where a `--text-*` token would apply?
- [ ] Is the `--site-header-height: 60px` value duplicated anywhere in component CSS rather than referenced as the token?

## B. CSS architecture and import manifest (`app/static/css/main.css`)

- [ ] Does every file in `app/static/css/components/` appear in `main.css`? List any that don't. (Known orphans as of 2026-05-18: `knowledge-sidebar.css`.)
- [ ] Does every file in `app/static/css/pages/` appear in `main.css`? List any that don't. (Known orphans as of 2026-05-18: `auth.css`, `debug.css`, `account.css`.)
- [ ] Are orphaned page CSS files loaded via `{% block head %}` in their corresponding templates instead? If so, is this intentional and documented?
- [ ] Are there any CSS files in the tree that contain only comments or placeholder text?
- [ ] Is the import order in `main.css` (core → layout → components → pages) still correct? Are any components depending on styles from a later layer?
- [ ] Are there any files in `app/static/css/` that are not imported anywhere? (Find with `find app/static/css -name '*.css' | xargs grep -L "import"` cross-referenced against main.css.)
- [ ] Does the ATF viewer have its own CSS subdirectory (`components/atf-viewer/`)? Is its `index.css` imported in `main.css` or from within the subdirectory?

## C. Component architecture and naming

- [ ] Does every Jinja macro in `_macros.html` have a corresponding CSS component file? (And vice versa — does every component CSS file have a corresponding macro or template usage?)
- [ ] Are BEM class names consistent? Specifically: are `__element` and `--modifier` suffixes applied uniformly? Check `card-details`, `card-overlay`, `card-badges`, `card-eyebrow` — are these BEM elements (`card__details`) or utility classes?
- [ ] Is there any component that exists in CSS but is implemented ad-hoc in templates (without a macro) — creating two parallel implementations of the same pattern?
- [ ] Are modifier classes always applied alongside the base class? (e.g., `.pipeline--compact` should never appear without `.pipeline`)
- [ ] Do any component CSS files define styles for page-level selectors (body, html, h1) rather than scoped component classes?
- [ ] Are there any component CSS files where a class name conflicts with a class name in another component file? (Risk of unintentional style bleed.)
- [ ] Does the `atf-viewer/` component group have a clear index file that imports its sub-parts, or do the sub-files get imported individually and out of order?

## D. Template structure and Jinja patterns (`app/templates/`)

- [ ] Does `base.html` define all expected blocks? (`head`, `content`, `scripts`) Are any blocks that child templates need missing from the base?
- [ ] Does every page template extend `base.html` (or a sub-base)? Are any templates standalone HTML files that should be inheriting the base?
- [ ] Are there any hardcoded strings in templates that should be variables or macros (e.g., the same HTML button pattern written inline in multiple templates)?
- [ ] Is the global search logic in `base.html` (the long `{% set _path %}` block with scope detection) accurate for all current routes? Are any new routes missing from the scope map?
- [ ] Are the `_debug/` templates excluded from production deploys? (Check rsync excludes in `deploy.sh` — `.claude/` is excluded but `_debug/` may not be.)
- [ ] Is there a consistent naming convention for template directories? (`snake_case` for dirs, matching route names)
- [ ] Does `partials/` only contain true partials (fragments included via `{% include %}`)? Or does it contain page templates too?
- [ ] Is the inline IIFE in `base.html` (the auth/avatar fetch) the right place for that logic? Could it live in `app.js` instead?

## E. JavaScript organization and quality (`app/static/js/`)

- [ ] Does every `.js` file have a clear single responsibility? Are there files doing more than one thing?
- [ ] Does `app.js` serve as a true global bootstrap, or has it accumulated unrelated feature code?
- [ ] Are there inline `<script>` blocks in any template or macro file that should be extracted to a standalone `.js` file? (Known: `_macros.html` has two script blocks for filter sidebar and dictionary filter sidebar behavior.)
- [ ] Is each JS file named consistently with the feature it controls? (kebab-case, matching the route or component it serves)
- [ ] Is `atf-viewer-integration.js` clearly differentiated from `atf-viewer.js` in purpose? Would a rename make this clearer?
- [ ] Does any JS file use `var` where `const`/`let` would be cleaner and safer? (The inline scripts and `app.js` use `var`.)
- [ ] Are there any JS event listeners attached to elements that may not exist on the current page (causing silent no-ops or errors)?
- [ ] Does `zoombox.js` have any dependencies on global state or CSS classes that must remain stable?
- [ ] Is there any JavaScript that queries the DOM by hardcoded strings (class names, IDs) that could silently break if the HTML is refactored?

## F. www design system (`www/index.html`, `www/assets/style.css`, `www/docs/`)

- [ ] Does the Tailwind config in `www/index.html` match the current token values in `app/static/css/core/tokens.css`? Specifically verify: `g.accent` = `--color-accent`, `g.bg` = `--color-bg`, `g.text` = `--color-text`, `g.elevated` = `--color-bg-elevated`, `g.border` = `--color-border`.
- [ ] Does `www/index.html` reference any color aliases (`lapis`, `clay`) that don't correspond to an app token? If so, are they intentionally www-only?
- [ ] Is `www/assets/style.css` still a placeholder? If so, is there a plan for it? If it has content, does it use tokens or hardcoded values?
- [ ] Do any `www/docs/*.html` pages use inline styles that contradict the Tailwind design system?
- [ ] Do the docs pages define their own color scheme, or do they inherit from the Tailwind config in `index.html`? (They do not — docs pages are separate HTML files with no shared base.)
- [ ] Is the `<style>` block in `www/index.html` (smooth scrolling, `line-height!important`) the right mechanism? Or should this go into `www/assets/style.css`?
- [ ] Is the `!important` on `line-height` in `www/index.html` still necessary, or is it overriding a Tailwind default that could be configured instead?

## G. www / app design continuity

- [ ] Do `www/` and `app/` use the same fonts at the same weights? (Both load Playfair Display + Noto Sans Cuneiform — verify the weights in each `<link>` match.)
- [ ] Does the visual language feel cohesive when switching between `glintstone.org` and `app.glintstone.org`? (Open both and compare: dark backgrounds, accent gold, serif headings.)
- [ ] Is the Glintstone logomark present in both surfaces? (app: SVG in base.html; www: check index.html)
- [ ] Do error states (404, 500) in the app look consistent with the www 404 experience? (Or is there no www 404 page yet?)
- [ ] Is there any marketing copy in `www/` that describes features not yet built, or that contradicts the current app's capabilities?
- [ ] Are navigation links between www and app correct? (e.g., "Sign in" links to `app.glintstone.org`, "Docs" links to `glintstone.org/docs`)

## H. File naming and hygiene

- [ ] Do all CSS files in `app/static/css/` use kebab-case names? (`cards-tablet.css` ✓, not `cards_tablet.css`)
- [ ] Do all JS files in `app/static/js/` use kebab-case names?
- [ ] Do all template files use snake_case? (`tablet_detail.html` ✓)
- [ ] Are there any template files with ambiguous names that could be confused with each other? (e.g., `detail.html` exists in both `tablets/` and `collections/` — is this intentional?)
- [ ] Are there any `.DS_Store` files committed in `app/static/` or `app/templates/`? (Known: several exist — should be gitignored, not tracked.)
- [ ] Does `.gitignore` exclude `.DS_Store` everywhere, including inside `app/`?
- [ ] Are there any unused image files in `app/static/images/`? (Check collection cover images against actual collections in the DB.)
- [ ] Are there any `TODO` comments in CSS or JS that have not been tracked as GitHub issues?

## I. Inline annotations and code clarity

- [ ] Does `tokens.css` have section headers for each category? (It does — verify they're accurate and up-to-date.)
- [ ] Does each CSS component file have a header comment explaining what it styles and what HTML context it expects? (Or is the filename sufficient?)
- [ ] Do complex Jinja macros have a `{# Brief description of params and expected data shape #}` comment? (The macros are long — `pipeline`, `filter_sidebar`, `tablet_card` are all undocumented except by their signatures.)
- [ ] Do JS files have a top-of-file comment explaining what they do and what they attach to?
- [ ] Are inline CSS sections with non-obvious decisions annotated? (e.g., the `--color-bg-rgb` raw triplets, the `--z-overlay` and `--z-dropdown` being equal)
- [ ] Is the `onerror` fallback chain on tablet images in `_macros.html` documented? (It has a 4-level fallback: R2 → legacy API → CDLI photo → CDLI lineart → placeholder. Complex enough to need a comment.)

## J. Accessibility audit

- [ ] Does `base.html` have a skip-to-content link? (Keyboard users can't skip the header nav without one.)
- [ ] Are all landmark regions present: `<header>`, `<main>`, `<footer>`, `<nav>`, `<aside>`? Or are pages using unlabelled `<div>` wrappers?
- [ ] Does every `<img>` have a meaningful `alt` attribute? Are decorative images (`alt=""`) correctly marked?
- [ ] Does the global search drawer have proper ARIA roles (`role="dialog"`, `aria-modal`, `aria-label`)?
- [ ] Are tab order and focus trapping correct in the global search drawer?
- [ ] Do interactive elements (buttons, links) have visible focus styles? (Check for `outline: none` without a replacement focus indicator.)
- [ ] Is heading hierarchy (h1 → h2 → h3) consistent across templates? Or do pages skip from h1 directly to h3?
- [ ] Do all custom toggle switches (`.toggle-switch`) have visible labels and are they correctly associated via `<label>`?
- [ ] Are the pipeline segment spans (`<span class="pipeline__segment">`) accessible to screen readers? They convey pipeline status but may have no text content.

## K. Responsive design and mobile readiness

- [ ] Does the two-column layout (`two-column.css`) collapse to a single column at a reasonable breakpoint?
- [ ] Is the filter sidebar hidden or collapsed on mobile? What breakpoint?
- [ ] Does the global search drawer work on mobile (tap-to-open, keyboard-safe)?
- [ ] Are touch targets (buttons, filter checkboxes) at least 44×44px on mobile?
- [ ] Is the tablet card grid responsive? What happens at narrow widths?
- [ ] Is the ATF viewer layout readable on mobile, or does it require horizontal scrolling?
- [ ] Does `www/index.html` have responsive layout? (Tailwind responsive utilities should handle this — verify the key sections.)
