# Search Navigation — V2 UX Improvements

## Issues in V1

### 1. Blank state is not helpful
"Search tablets, signs, words…" gives no scaffolding to a user without a specific query in mind. First-time users and explorers get nothing.

### 2. No differentiation between Browse and Detail contexts
On a Browse page, search helps you *navigate to* something. On a Tablet Detail page, users often want to *search within* the current tablet (find a word in the ATF, jump to a specific line). V1 uses the same bar for both, with no affordance for local search. The user doesn't know whether typing will navigate them away or search in-place.

### 3. Scope auto-sets silently
Navigating to a page silently changes the scope (e.g., → Tablets page → scope becomes "Tablets"). Useful, but a user who set a deliberate scope earlier could lose it without noticing.

### 4. Single query example makes it hard to evaluate the component
Only "Gilgamesh" is shown. It's unclear how the component handles:
- Period names ("Ur III") — mostly tablet/collection results, no lemma matches
- Topical phrases ("ration distribution") — tablets + lemmas
- Direct P-number lookups ("P3928244") — single confident result, no need for categories
- Scoped search with zero results — no state exists for this

### 5. No-results state is missing
If a scoped search returns nothing, the dropdown silently empties. No feedback, no recovery path offered.

### 6. Accessibility gaps
- No ARIA roles (combobox, listbox, option)
- No keyboard navigation through results (↑↓ arrows, Enter to select)
- No screen reader announcements for scope changes or result counts
- Focus not managed when dropdown opens or closes
- Scope option buttons have no accessible labels beyond their text content
- No visible focus ring on result rows

### 7. "128 results" link is low-affordance
A small underlined text link doesn't communicate that there are substantially more results available. Users may miss it or not recognise it as actionable.

### 8. The scope pill only appears when the dropdown is open
Users don't know search is currently scoped to "Tablets" unless they've already opened the dropdown. The active scope should be visible even when the search is at rest.

---

## V2 Improvements

### 1. Rich blank state
When focused with no query:
- **Recent searches** — 3 most recent queries (per-session in prototype, real app would persist)
- **Contextual suggestions** — 3 suggestions relevant to current scope/page (e.g., on Tablets: "Try: ration distribution, Ur III admin, Old Babylonian lit")
- **Keyboard hints** — Tab to cycle scope, ↑↓ to navigate, Enter to select, Esc to close

### 2. Browse vs Detail search differentiation
**Browse pages:** search navigates *to* content, scope follows page context.

**Detail page:** adds a **search mode selector** below the input bar:
- **Everywhere** — global search, navigates away to matching content
- **In P334357** — local ATF search within the current tablet; shows matching lines in context, no page navigation

The mode selector uses the same visual language as the scope bar. Default on entering the Detail page is "In P334357" (most contextually relevant action), with "Everywhere" one click away.

### 3. Scope pill always visible at rest
A small, subtle scope badge appears to the left of the search placeholder even when unfocused (not just when the dropdown is open). Clicking it opens/focuses the search directly into the scope bar.

### 4. Scope change feedback
When scope auto-sets on page navigation, the pill briefly pulses/highlights to signal the change. Scope changes within the dropdown are instant (CSS re-filter, no loading) — this is a filter, not a new query.

### 5. Real input with debounced loading
V2 uses a real `<input>` element:
- Typing any character → 400ms debounce → 600ms loading skeleton → results
- This lets the user type naturally and see multiple query types
- Preset queries are mapped by keyword; unknown queries fall back to a generic result set

### 6. Multiple query examples
Four query types are reachable by typing:
- `gilgamesh` — proper noun, cross-type (collections, tablets, lemmas, signs)
- `ur iii` — period name, mostly tablets and collections, no lemma matches
- `ration` — topical keyword, tablets + lemmas, fewer collections
- `P3928244` — direct ID lookup, single confident result with high-confidence badge

### 7. No-results state
When a scoped search finds nothing:
- "No [tablets/collections/scholars] match '[query]'"
- "Try searching All types" (button that resets scope to All)
- Suggests checking spelling or broadening scope

### 8. Keyboard navigation (ARIA combobox)
- `role="combobox"` on search container, `aria-expanded`, `aria-haspopup="listbox"`
- `role="listbox"` on dropdown, `role="option"` on each result
- `role="group"` + `aria-label` on section headers
- `aria-live="polite"` region announces result count when results load
- ↑↓ arrow keys navigate results; Enter selects; Escape closes and returns focus to input
- Tab cycles scope when dropdown is open (announced to screen readers)

### 9. "View all" CTA
Replace underlined "128 results" with a clearly styled "View all 128 →" button-link inside the results section.

---

## Open Questions

1. **Local search scope**: Should "In P334357" also search the composite's other tablets, or strictly this physical tablet?
2. **Scope persistence**: Should scope reset to "All" when the user clears the query and re-focuses, or persist the last explicit scope choice?
3. **Search from the detail page going back**: If a user searches globally from the Detail page and picks a new tablet, does Back return to the original tablet or to the Browse page?
4. **Lemmas in the Dictionary scope**: Should "Dictionary" scope include glosses and signs, or only lemmas? Current V1 groups all three together.
5. **Confidence badge for P-number lookup**: Is the "Direct match" badge appropriate UX, or does it imply other results are less reliable?
