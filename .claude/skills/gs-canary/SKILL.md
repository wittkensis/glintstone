---
name: gs-canary
description: Read-only blast-radius recon for a Glintstone bug, symptom, or proposed change. Decides whether it's api-only, app-only, or shared (the api↔app contract, the token CSS, a migration, or a gs-expert domain), names the invariant violated, greps both tiers + the migrations + the CSS tokens, and returns which tier(s) are affected and the cheapest CORRECT tier to fix. Use in the triage phase of a gs-swarm (fan out one per symptom, in parallel) BEFORE any fix, or for any single Glintstone bug that smells like it crosses the two-tier seam. Read-only — never edits. Triggers — canary, blast radius, "this smells systemic", "which tier", "api or app", root cause, triage.
metadata:
  question: "For a Glintstone bug or change, is it api-only, app-only, or shared — and at what tier is the cheapest correct fix?"
  created: 2026-06-25
  modified: 2026-06-25
  context: "Back-ported from fleet--canary-scout (the *.ericwittke.com fleet recon scout) during backlog #29 Phase 3. The fleet version classifies app-local vs kw-system base vs template across cloned apps. This Glintstone version classifies along Glintstone's actual seams instead: api-only vs app-only vs shared (the api↔app HTTP contract, the token CSS, a migration, or a cross-cutting gs-expert domain). It is the read-only complement to the generic canary-in-the-coalmine class-closing loop."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#29"]
  related_skills: [gs-swarm, canary-in-the-coalmine, gs-expert-data-model, gs-expert-ui, gs-expert-integrations, gs-expert-deployment, gs-orient-project]
  supersedes: null
  superseded_by: null
  triggers: [canary, "blast radius", "this smells systemic", "which tier", "api or app", "root cause", triage, scout, "systemic bug"]
---

# Glintstone Canary Scout

## Invocation
Triggers: canary, blast radius, this smells systemic, which tier, api or app, root cause, triage

Read-only recon: before anyone fixes a Glintstone bug, decide **at what tier it should be fixed** so a one-line symptom isn't patched on both tiers (or patched once in the wrong tier). One symptom per dispatch. You **read and measure only — never edit.** This is the Glintstone-tiered front of the generic `canary-in-the-coalmine` loop; it owns *where*, that skill owns *closing the class*.

A bug is a sample from a distribution. The dead canary isn't the problem — it's the warning that a contract, a token, or a migration is wrong everywhere it's consumed.

## Input
One symptom/bug/proposed change (e.g. "translation count shows NULL on the artifact page", "lemma filter returns 500", "add a `confidence` field to annotations", "P-number header wraps on mobile"). If a specific tier/file is named, start there; otherwise start from the **api↔app contract** (the endpoint + the template/JS that consumes it).

## Method
1. **Name the invariant** the bug violates (e.g. "every annotation row carries `annotation_run_id`"; "the app reads counts from the API response, never the DB"; "a new table is `GRANT`ed to `glintstone`"; "P-number headers truncate, not wrap").
2. **Locate the root — which tier owns the cause?**
   - **api/** — endpoint, repository, query, serialization, the JSON shape the app consumes.
   - **app/** — Jinja template, vanilla JS, the httpx call, presentation.
   - **shared / contract** — the api↔app HTTP contract itself (field renamed/removed in `api/` that `app/` still reads), the **token CSS** (`app/static/`), a **migration** (`source-data/migrations/NNN_*.sql`), or a cross-cutting **gs-expert domain** rule (data-model, assyriology, integrations).
   Grep both tiers, the migrations, and the CSS tokens. Distinguish "the code is latent here" from "this tier actually triggers it."
3. **Measure blast radius.** Which tier(s) actually exhibit it, and how many call sites? A renamed API field can break every template that reads it; a missing `GRANT` breaks every app read of that table; a missing token breaks every component using it. Report counts + `file:line`s per tier. "api-only, 1 endpoint" vs "contract drift across 6 templates" changes the fix.
4. **Pick the tier.** api-only (one endpoint/repo) → app-only (template/JS) → shared. For **shared**, name the sub-class:
   | Sub-class | Meaning | Fix at |
   |---|---|---|
   | **Contract drift** | api/ and app/ disagree on the JSON shape | fix the `api/` contract once; update every `app/` consumer |
   | **Token / CSS** | a design token or base style is wrong/missing | fix the token in `app/static/`; re-check every component |
   | **Migration** | schema/grant/index wrong → every consumer affected | new `NNN_*.sql` migration (as `wittkensis`, `GRANT` to `glintstone`) |
   | **gs-expert domain** | a cross-cutting domain rule (attribution, lemma parsing, source quirk) | fix in the domain layer per the owning gs-expert skill |
   Cheapest tier that fixes it everywhere it can occur, without over-reaching.
5. **Codify hook.** If shared, note where it should be guarded so it can't recur — a `gs-audit-hardening` / `gs-audit-frontend` dimension, a pytest assertion on the contract, a `GRANT` check, or a tightening of the owning gs-expert skill. Name the owning gs-expert so the fix lands with the right expert.

## Glintstone-specific traps to check before classifying
- **Two-tier confusion**: a symptom in `app/` whose root is a missing/renamed `api/` field is a **contract** bug, not an app bug — fix the api once, not every template.
- **Missing `GRANT`**: an app-tier read returning empty/500 for a *new* table is usually the `wittkensis`→`glintstone` grant, not app code — that's a **migration** fix.
- **NULLs are expected** (coverage is partial): a "missing data" symptom may be correct behavior (no annotation exists), not a bug. Confirm the row should exist before classifying.
- **Attribution**: a "wrong/overwritten annotation" symptom may be a structural-attribution violation (silently overwrote instead of new `annotation_run_id` run) — a data-model domain bug.

## Return (exactly this shape)
```
INVARIANT: <the rule violated>
CLASSIFICATION: api-only | app-only | shared:contract | shared:token | shared:migration | shared:domain
ROOT: <file:line where the cause lives, by tier>
BLAST RADIUS: <tier(s) that actually exhibit it> / <call-site count per tier>
FIX TIER: <where to fix + why that tier, not lower/higher>
CONTRACT/GRANT IMPACT: <api fields or table grants that must move together / none>
CODIFY: <gs-audit dimension, pytest contract assertion, GRANT check, gs-expert to tighten, or "n/a">
OWNING GS-EXPERT: <gs-expert-data-model | -ui | -integrations | -assyriology | -deployment>
EVIDENCE: <2–4 file:line cites backing the above>
```
TERMINATION: deliver the block above. You are read-only — propose the tier, never apply it; the orchestrator or a swarm-worker (briefed with the owning gs-expert) does the fix.

## Related
- `gs-swarm` — dispatches this in its triage phase (one per symptom, parallel)
- `canary-in-the-coalmine` — generic: the per-bug class-closing loop this feeds (this skill names the tier; that one closes the class)
- `gs-orient-project` — the two-tier architecture + non-negotiables this scout reasons against
