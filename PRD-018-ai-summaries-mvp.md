---
question: "What does this tablet contain, and can I trust that summary?"
created: 2026-06-07
modified: 2026-06-07
context: "Generated from a full code audit of core/agent/ + api/services/agent_service.py + artifact-summary.js on 2026-06-07. Covers the gap between 'built' and 'correct on production'."
status: active
audience: [eric]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic, gs-expert-assyriology, gs-expert-deployment]
supersedes: null
superseded_by: null
---

# PRD-018 — AI Summaries: Ship to MVP

## Harness fingerprint
| Field | Value |
|-------|-------|
| PRD template | PRD-agentic v1.0 |
| Authored | 2026-06-07 |
| Prompt versions in play | `synthesis.v1` (active), `synthesis.v2` (built, not wired) |
| Companion PRD | PRD-agentic-translation.md (origin spec) |

---

## 1. North star

**Job: Triage.** "Which artifacts should I study?" A scholar lands on an artifact detail page and needs a plain-English orientation before reading the cuneiform. The AI summary is the first thing they read; it must be accurate, clearly attributed, and honest about uncertainty.

---

## 2. What Is Already Built (audit 2026-06-07)

Everything in this list is confirmed present in the working codebase:

| Component | File | State |
|-----------|------|-------|
| Fact assembly | `core/agent/fact_assembly.py` → `assemble_artifact_facts` | Done |
| Synthesis loop | `core/agent/synthesis.py` → `synthesize_artifact_summary` | Done |
| v2 semantic checks | `synthesis.py` → `_validate_v2_semantics` | Done but not invoked |
| Lazy-persist | `api/services/agent_service.py` → `do_summarize_artifact` | Done |
| Degraded fallback | `_degraded_summary_from_facts` | Done |
| API route | `GET /api/v2/artifacts/{p}/summary?focus=general` | Done |
| Frontend panel | `app/static/js/artifact-summary.js` | Done |
| Pipeline bar + lang badge | `artifact-summary.js` → `renderHeader` | Done |
| Hypothesis display | `artifact-summary.js` → `renderSummary` | Done |
| Thumbs feedback | `artifact-summary.js` + `POST /agentic/feedback` | Done |
| Best-guess extraction | `agent_service.py` → `_extract_best_guess` | Done |
| Retry on grounding error | `synthesis.py` → `_run_loop` (2 attempts) | Done |

---

## 3. The Bugs

### Bug 1 — v1 prompt hardcoded in service layer (HIGH)

`do_summarize_artifact` in `api/services/agent_service.py` line 268:
```python
prompt_version = "synthesis.v1"
```

But `synthesize_artifact_summary` in `synthesis.py` defaults to `synthesis.v2`. The v2 prompt adds:
- Dialect code translation (raw `akk-x-oldbab` → "Old Babylonian Akkadian")
- Enforcement that mixed-language character is mentioned
- Enforcement that scholarly disagreements are qualified, not stated as fact

These are exactly the scholarly-accuracy improvements that matter for MVP. The v1 prompt doesn't have them; the v2 validation checks exist but never run because the service layer never asks for v2.

**Fix:** Change `prompt_version = "synthesis.v1"` to `prompt_version = "synthesis.v2"` in `do_summarize_artifact`. The `find_fresh` cache lookup uses `prompt_version` as a key, so existing v1 cached outputs won't be returned; summaries will regenerate on next request.

**Risk:** v2 has stricter grounding rules and will hit `SynthesisGroundingError` more often on unusual tablets. The degraded fallback handles this, so it won't break — it just means some summaries show fact-list text instead of narrative. Monitor `agent_outputs` for `best_guess_flag` frequency after switching.

### Bug 2 — ANTHROPIC_API_KEY not verified on VPS (HIGH)

`do_summarize_artifact` calls `_get_anthropic()`, which reads `ANTHROPIC_API_KEY` from the environment. If that key isn't set in `/var/www/glintstone/current/.env` on the VPS, every summary request raises a runtime error and returns HTTP 500.

**Fix:** Before any other step, verify the key is present: `cat /var/www/glintstone/current/.env | grep ANTHROPIC_API_KEY`.

### Bug 3 — Lazy-persist TTL unknown (MEDIUM)

`agent_outputs.find_fresh` determines whether a cached output is still valid. The TTL (how old an output can be before we regenerate) is set inside `core/agent/agent_outputs.py`. This was not audited. If the TTL is very short (e.g., 24h) or very long (e.g., 90 days) it affects cost and freshness differently.

**Fix:** Read `agent_outputs.py`, find the TTL constant, and confirm it's set to something reasonable for MVP (30 days is a sensible default — facts don't change that fast).

### Bug 4 — Line suggestions have no caching (HIGH, cost risk)

This is documented here because it shares the agentic cost budget with summaries. `do_suggest_line_translation` in `agent_service.py` has no `find_fresh` / `agent_outputs.insert` path — it calls Claude on every request. The frontend `line-suggestions.js` fetches up to 5 lines per scroll window. On a 40-line tablet, the first page load can trigger 5+ live Claude calls simultaneously.

This is unsustainable for beta. See §6 for the fix approach.

---

## 4. Missing DOM verification

The `artifact-summary.js` script references these element IDs in `detail.html`:
- `knowledge-sidebar` (needs `data-p-number` and `data-api-url` attributes)
- `artifact-summary-loading`
- `artifact-summary-content`
- `artifact-summary-header`
- `artifact-summary-unsupported`
- `artifact-summary-text`
- `artifact-summary-hypothesis`
- `artifact-summary-meta`
- `artifact-summary-error`

These must all exist in `app/templates/tablets/detail.html`. This was not verified in the code audit. If any are missing, the script fails silently (the `if (!el)` guards prevent crashes, but the panel shows nothing).

**Fix:** Before testing on VPS, grep `detail.html` for each ID.

---

## 5. Implementation sequence for MVP

### Phase A — Local verification (pre-deploy)

1. Grep `detail.html` for all 9 element IDs above. Fix any missing.
2. Start local API + web servers. Navigate to any artifact with Sumerian or Akkadian text (e.g., P346213). Open sidebar. Confirm:
   - Loading spinner appears
   - Summary loads (or degraded fallback appears with fact list)
   - Pipeline bar and language badge render
   - Thumbs buttons appear after load
3. Check browser console for JS errors.

### Phase B — v2 prompt switch

4. In `api/services/agent_service.py`, change `synthesis.v1` → `synthesis.v2`.
5. Clear any existing cached summaries for test tablets (or just wait — the TTL key mismatch means v1 outputs won't be served as v2).
6. Re-test with a mixed-language tablet (a bilingual Sumerian-Akkadian text if one exists in local DB) and a tablet with competing lemmatizations. Confirm the v2 checks fire.

### Phase C — Deploy and verify on VPS

7. Deploy: `bash ops/deploy/deploy.sh`
8. SSH to VPS. Confirm `ANTHROPIC_API_KEY` is in `.env`.
9. Curl the summary endpoint directly: `curl http://localhost:8001/api/v2/artifacts/P346213/summary?focus=general`
10. Confirm response has `synthesis` field with `[n]` markers and `interaction_id`.
11. Open the web app in browser. Navigate to P346213 detail page. Open sidebar. Confirm summary renders.

### Phase D — Line suggestion caching (before beta invite)

12. Add `agent_outputs.insert` to `do_suggest_line_translation`, using `output_type="line_suggestion"`, `target_id=f"{p_number}::{surface_name}::{line_number}"`.
13. Add `agent_outputs.find_fresh` at the top of the function (same pattern as `do_summarize_artifact`).
14. Test: request the same line twice. Second request should be instant (cache hit).

---

## 6. Done criteria

- [ ] All 9 DOM IDs present in `detail.html`
- [ ] Local smoke test: summary renders for P346213 in sidebar
- [ ] `synthesis.v2` is the live prompt version in `do_summarize_artifact`
- [ ] VPS: `ANTHROPIC_API_KEY` confirmed present
- [ ] VPS: `/api/v2/artifacts/P346213/summary` returns HTTP 200 with non-empty `synthesis`
- [ ] VPS: Summary panel renders in browser on artifact detail page
- [ ] Line suggestions: `agent_outputs.insert` added (caching enabled)
- [ ] Line suggestions: second request for same line returns cached result

---

## 7. Out of scope for this PRD

- Changing the synthesis prompt content (new facts, new structure) → propose a new PRD
- Translation suggestions quality tuning → see PRD-agentic-translation.md §Phase 2
- Token interpretation wiring → PRD-020
- Semantic search → PRD-019
