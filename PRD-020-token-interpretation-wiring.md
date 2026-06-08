---
question: "What does this specific cuneiform word mean in context?"
created: 2026-06-07
modified: 2026-06-07
context: "Generated from a full code audit of app/static/js/token-popover.js + api/services/agent_service.py + core/agent/fact_assembly.py on 2026-06-07. The backend is complete; the UI path is completely disconnected."
status: draft
audience: [eric]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic, gs-expert-assyriology, gs-expert-ui]
supersedes: null
superseded_by: null
---

# PRD-020 — Token Interpretation: Wire or Descope

## Harness fingerprint
| Field | Value |
|-------|-------|
| PRD template | PRD-agentic v1.0 |
| Authored | 2026-06-07 |
| Prompt version | `interpret-token.v1` |
| API route | `GET /api/v2/tokens/{token_id}/interpret` |

---

## 1. North star

**Job: Comprehension.** A scholar reading a line of cuneiform clicks a word they're unsure about. Instead of just seeing the dictionary entry, they want to know: what does this token mean *in context* — given the grammar, the parallel texts, the known lemmatizations by other scholars? This is the "why does this sign appear here" question.

---

## 2. The disconnect (audit 2026-06-07)

The backend is fully built. The frontend is fully built. They don't connect.

**Backend:**
- `assemble_token_facts(conn, p_number, token_id)` assembles facts for a token given its integer primary key from the `tokens` table
- `do_interpret_token` runs the synthesis loop with `interpret-token.v1.md` and returns a `ChainPayload` (JSON with steps + hypotheses)
- Lazy-persist via `agent_outputs`
- Route: `GET /api/v2/tokens/{token_id}/interpret` — takes an integer `token_id`

**Frontend:**
- `token-popover.js` opens when a scholar clicks an `.atf-word` element
- The element has `data-lookup` (the citation form, e.g. `"ilu[god]N"`) and `data-surface-form` (the raw ATF text)
- The popover calls `GET /api/v2/artifacts/{p}/lemmas?lookup={form}` and `GET /api/v2/artifacts/{p}/competing-lemmas?lookup={form}` — lexical endpoints that return database lemma records
- The popover never calls `/tokens/{token_id}/interpret`
- There is no `data-token-id` attribute on `.atf-word` elements

**Root cause:** ATF word elements are rendered by `atf-viewer.js` from the ATF normalized text endpoint. That endpoint returns the citation form (`data-lookup`) and surface form (`data-surface-form`) for each word, but not the integer `token_id` from the `tokens` database table. So the popover has no ID to hand to the interpret endpoint.

---

## 3. Decision gate (answer before building)

There are two MVP paths. Choose one before implementing anything.

### Option A — Wire it up (4-6 hours of work)

Add `token_id` to the ATF text API response, pass it through the viewer into the DOM, and call the interpret endpoint from the popover.

**Steps:**
1. `api/routes/tablets.py` (or wherever the normalized-text endpoint is): add `token_id` to each word object in the response JSON.
2. `app/static/js/atf-viewer.js` → `renderWord()` or equivalent: add `data-token-id="${word.token_id}"` to the rendered `.atf-word` element.
3. `token-popover.js` → `show()`: read `el.dataset.tokenId`. If present and non-zero, after populating lexical data, also fetch `/tokens/{tokenId}/interpret` and render the chain steps below the dictionary panel.
4. `detail.html`: confirm `token-popover.js` is loaded (it is, as of PRD-017).

**Tradeoffs:**
- Each word click triggers a Claude call (unless the output is already in `agent_outputs` cache). Response time: 2-5 seconds.
- The result is contextual (considers neighboring tokens, attested readings, grammar) — meaningfully different from the lexical panel already shown.
- Must add an "AI interpretation" section to the popover, clearly labeled, below the lexical data. The lexical data must remain visible even while the AI result is loading.

### Option B — Descope from MVP (0 hours of work)

The token popover as built already shows lexical data (guide word, POS, competing readings) from the database. This is valuable on its own. The AI interpretation layer adds context but isn't required for a useful MVP.

**When to choose Option B:**
- The beta user persona (Dr. Al-Rashid, Aisha Okonkwo) hasn't asked for this yet
- The popover is already shipping and showing real data
- Option A has risk (2-5s latency on every word click is bad UX if the user is just scanning)

**Recommendation for MVP: Option B.** The popover is useful without AI. Wire up Option A after you've tested the popover with beta users and confirmed they want deeper context per token. The backend is ready; you can ship Option A in an afternoon when the signal is there.

---

## 4. Implementation (if Option A is chosen)

### 4.1 API change — add `token_id` to normalized-text response

Find the normalized-text endpoint (likely `api/routes/tablets.py` → something like `/artifacts/{p}/normalized-text` or similar). The response currently returns word objects with at least `lookup` (citation form) and `surface_form`. Add `token_id: int` to each word.

The SQL that drives this response already joins to `tokens` — the `token_id` column is the PK of that table.

### 4.2 ATF viewer — stamp `data-token-id` on words

In `app/static/js/atf-viewer.js`, wherever `.atf-word` elements are created:
```js
// Before (example):
wordEl.dataset.lookup = word.lookup;
wordEl.dataset.surfaceForm = word.surface_form;

// After:
wordEl.dataset.lookup = word.lookup;
wordEl.dataset.surfaceForm = word.surface_form;
if (word.token_id) wordEl.dataset.tokenId = word.token_id;
```

### 4.3 Token popover — add AI panel

In `token-popover.js` → `show()`, after resolving lexical data:
```js
const tokenId = el.dataset.tokenId;
if (tokenId && tokenId !== '0') {
    TokenPopover._fetchInterpretation(popover, pNumber, tokenId, apiUrl);
}
```

Add `_fetchInterpretation(popover, pNumber, tokenId, apiUrl)`:
- Append a loading section to the popover body
- Fetch `${apiUrl}/tokens/${tokenId}/interpret`
- On success: render `data.data.steps` as a numbered list, each with label + value + source attribution
- Render `data.data.hypotheses` (if any) as provisional readings, clearly marked with "Hypothesis:"
- On error: remove the loading section silently

### 4.4 CSS additions

Add `.token-popover__ai-panel` styles to `app/static/css/components/atf-viewer/words.css`:
- Hairline separator between lexical panel and AI panel
- `font-size: var(--text-xs)` for the AI panel (it's supplementary, not primary)
- `.token-popover__ai-loading` spinner
- `.token-popover__hypothesis` — muted, italic, with a "Hypothesis" prefix

---

## 5. Done criteria (Option A)

- [ ] Normalized-text API response includes `token_id` on each word object
- [ ] `.atf-word` elements in rendered ATF have `data-token-id` attribute
- [ ] Clicking a word with a valid `token_id` shows loading indicator in popover
- [ ] AI interpretation renders below lexical panel with step-by-step chain
- [ ] Hypotheses render as clearly provisional ("Hypothesis: …")
- [ ] AI panel has "AI-generated" attribution label
- [ ] Lexical data always visible; AI panel appears in addition to, not instead of
- [ ] Second click on same word uses cached `agent_outputs` result (fast)
- [ ] Popover degrades gracefully if interpret endpoint returns error (shows lexical only)

## Done criteria (Option B — descope)

- [ ] Decision documented in this PRD
- [ ] Token popover ships as-is (lexical data only)
- [ ] Backlog item filed to revisit after beta user feedback

---

## 6. Out of scope

- Batch interpretation of all tokens on a surface (would require significant UX rethink)
- Exporting interpretations to a scholar's annotation set (future feature)
- Sign-level interpretation (below the token level — post-MVP)
