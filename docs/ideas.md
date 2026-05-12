---
question: "What promising ideas, paused features, unbuilt designs, missing data, and unfixed bugs are worth picking up later — and what's the minimum context to get back into each?"
created: 2026-05-11
modified: 2026-05-11
context: "The project doesn't track time-bound exploration in GitHub issues for content that isn't actionable yet. This file consolidates: icebox PRDs (paused product ideas), UX explorations, ML/agentic experiments, schema concerns, data gaps, and bugs that haven't been promoted to issues. Migrated from PLAN/PRDs/icebox-*.md, PLAN/UX Explores/, PLAN/Dictionary Taxonomies/Dictionary UI Design Options.md, and PLAN/PRIVATE-TODO.md during the 2026-05-11 knowledge architecture overhaul."
status: active
audience: [engineers, scholars, claude]
owners: [eric]
related_issues: ["#1", "#2", "#3", "#5", "#11", "#15", "#20", "#22", "#46"]
related_skills: [gs-orient-project, gs-scout-integrations, gs-curator-artifacts]
supersedes: ["PLAN/PRDs/icebox-agentic-layer.md", "PLAN/PRDs/icebox-api-design.md", "PLAN/PRDs/icebox-automated-data-ingestion.md", "PLAN/PRDs/icebox-multilingual-support.md", "PLAN/PRDs/icebox-remaining-data-sources.md", "PLAN/PRDs/icebox-schema-data-quality.md", "PLAN/PRDs/icebox-tech-stack-review.md", "PLAN/UX Explores/Search & Navigation/search-v2-improvements.md", "PLAN/Dictionary Taxonomies/Dictionary UI Design Options.md", "PLAN/PRIVATE-TODO.md"]
superseded_by: null
---

# Glintstone — promising ideas, gaps, and bugs

This is the project's idea backlog. Not actionable yet (that would be a GitHub issue), but worth keeping in one place so they don't get lost. Each entry: what, why, where it came from, and what would unblock it.

When an idea becomes ready to act on, file a GitHub issue and link it from the relevant section.

## How it's organized

1. **Paused product ideas (icebox PRDs)** — features that have been thought through but deprioritized
2. **UX explorations** — design directions that have prototypes or analysis but no implementation slot yet
3. **Schema & data-quality concerns** — ongoing governance questions
4. **Data gaps to close** — sources/datasets identified but not integrated
5. **Lexical & dictionary work** — Phase 6–9 of the lexical roadmap
6. **Quick wins** — small polish that hasn't been picked up
7. **Bugs & data integrity issues** — confirmed defects without an open issue

---

## 1. Paused product ideas (icebox PRDs)

### 1.1 Agentic summary layer (was #11)

Use the Claude API to generate historical/contextual summaries on demand for tablets, composites, collections. Cache aggressively to control cost. Outputs are versioned (`generated_at` + `model_version`) and stored in the DB. System prompts are versioned and visible to administrators.

Specific features it would unlock:
- Knowledge Bar — Tablet History (agentic historical context summary)
- Knowledge Bar — Dictionary (AI-assisted gloss explanation)
- Translation Proposals (suggested translations for unlematized tokens)
- Global Semantic Search (vector embeddings)

Pick up when: core PRDs (Translation Builder, Knowledge Bar, Browse, Tablet Viewer) ship. Anthropic API costs are predictable enough to commit. Decision on whether to host inference on the VPS via Ollama or call Anthropic directly.

Companion skill: `gs-scout-integrations` for evaluating which model size to use.

### 1.2 API design & external versioning (was #1)

The current API is good enough for the web app but isn't yet ready for external scholar consumers. Needs:
- Versioning strategy (`/v1/`, `/v2/` or header-based)
- Annotated OpenAPI / Swagger
- Terminology aligned with CDLI / ORACC / ePSD2 conventions
- Auth + rate limiting for external use
- Changelog + deprecation policy

Pick up post-v1 launch once the surface is stable.

### 1.3 Automated data ingestion (was #5)

Import scripts run manually. Automate via cron / scheduled runs on the VPS:
- Change detection (only re-import what's changed since last run)
- Notification on failures
- Idempotency is already there (`ON CONFLICT`); automation is the missing layer

Pick up after v1, when corpus freshness needs to be < quarterly. CDLI bulk export has been frozen since Aug 2022, which lowers the urgency.

### 1.4 Multilingual UI (was #46)

Scholars in Iraq, Syria, Iran, and Germany are underrepresented. Phase plan:
- Phase 1: German (translations already in DB)
- Phase 2: Arabic, Farsi (requires RTL layout)
- Phase 3: French, Spanish

Challenges: LTR/RTL swap, i18n string extraction (currently no string-table), Jinja2 i18n (babel or equivalent).

Pick up after v1 when the UI is stable enough that strings won't churn.

### 1.5 Remaining data sources to integrate

Several ORACC subprojects failed initial download (`TOPLEVEL_RETRY`):

| Project | Status | Blocker |
|---|---|---|
| cams | Download failed | Retry needed |
| etcsl | Download failed | Retry needed |
| rime | Download failed | Retry needed |
| ctij | Download failed | Retry needed |
| ribo | Subproject portal; download incomplete | Investigate portal format |
| amgg | Empty directory | Retry needed |
| hbtin | Not attempted (priority 3) | — |
| dccmt | Not attempted (priority 3) | — |

Import connectors (lemmatizations, glossaries, norms, credits) already include these projects — no code changes needed, just successful downloads.

Other source candidates listed in `gs-scout-integrations/worked-examples.md`.

### 1.6 Schema governance & language coverage (was #3)

Ongoing concerns, not a discrete feature:
- Mixed-language tablets — tokens that switch between Sumerian, Akkadian, Hittite within a line
- Citation integrity — every data point traceable to annotation run + scholar + publication
- Schema versioning as new sources land
- Hittite: language_map entries exist but lemmatization is sparse
- Elamite, Ugaritic, Hurrian: in `artifacts` but not in lexical layer

Treat as governance; review before each major import.

### 1.7 Tech stack review (was #15)

Options to weigh, post-v1:
- **Stay** with FastAPI + Jinja2 + vanilla JS (no JS build, fast server render, complex interactions need significant vanilla JS)
- **NiceGUI** — Python-native, less HTML/CSS control
- **Reflex** — React-based in Python, more interactive but heavier
- **Partial React** — islands pattern for complex components only (Translation Builder, KB)

Decision criteria: do we hit a wall with vanilla JS in the Translation Builder?

---

## 2. UX explorations

### 2.1 Search v2

V1 search has 8 known issues (no blank state, no Browse vs Detail context, silent scope change, no scoped no-results state, no a11y, low-affordance "128 results" link, scope pill only when open). V2 designs address each. Source: `PLAN/UX Explores/Search & Navigation/search-v2-improvements.md` plus prototypes `search-v2-prototype.html` and `search-v3-prototype.html`.

When this gets picked up, the prototype HTML files should be ported into `app/templates/components/` or treated as design references. Move the prototypes into `docs/prototypes/` or attach to a GitHub issue when filed.

### 2.2 Dictionary UI options (Signs / Lemmas / Glosses)

Detail-page design ideation for signs, lemmas, and glosses, grounded in actual data shapes. Terminology alignment between the Lexicography Terminology report and current schema:

- L0 Sign → `lexical_signs` (missing: `sign_type`, period attestation range)
- L1 Reading → split across 3 tables (gap; readings should be first-class)
- L2 Lemma → `lexical_lemmas` (missing: certainty flag, stem/derivation, root)
- L3 Gloss → `lexical_lemmas.guide_word` + `lexical_senses.definition_parts[]` (rename "Meanings" → "Glosses")
- L4 Attestation → `lemmatizations` + `tokens` + `text_lines`

Key principle: "Gloss for finding, attestation for understanding." Senses are irrecoverable for dead languages; `lexical_senses` actually stores glosses.

The biggest structural gap is **Reading**, which is scattered across `lexical_signs.values[]`, `sign_lemma_associations.reading_type`, and `token_readings`. A future migration could pull these into a dedicated `lexical_readings` table.

### 2.3 ATF viewer continued work

Knowledge Bar variants, ATF viewer overlay options, tablet citation display options. Markdown mockups live in (will move from PLAN to): the mockups attached here:
- knowledge-bar-options.md
- atf-viewer-options.md
- detail-section-structures.md
- tablet-citation-options.md
- adaptive-knowledge-bar.md

When picked up, attach to the relevant tablet-viewer or knowledge-bar GitHub issue.

---

## 3. Schema & data-quality concerns

### 3.1 Readings as first-class entities

Currently distributed across 3 tables. A `lexical_readings` table would simplify joins and make reading-level provenance trackable. Migration would be additive; old code paths can continue reading from current locations during transition.

### 3.2 Mixed-language token handling

ORACC corpus JSON has `%a`, `%sux`, etc. language-shift markers within a single line. Currently parsed but not surfaced consistently in the UI. Token-level `language` exists post migration 011 — verify it's populated for all bilingual tablets.

### 3.3 Period / region / dialect on lemmas

`lexical_lemmas.period`, `region`, `dialect` are empty. Filling them enables filtered dictionary browsing. Data exists in upstream ORACC glossaries (per-project, per-language) — connector update needed.

### 3.4 Sign_type and period attestation on signs

`lexical_signs` is missing `sign_type` (simple/modified/compound) and period attestation range. Data is in OGSL — connector update needed.

---

## 4. Data gaps to close

(Mirror of `gs-scout-integrations/gap-analysis.md` — see there for prioritization.)

Highlights:
- **Lemmatization coverage**: ~2% of artifacts. Highest-impact gap. FactGrid lemma model is a candidate.
- **Sign detection coverage**: 81 tablets (CompVis). DETR scaled, or a HuggingFace candidate.
- **MZL ↔ OGSL concordance**: ~90% done; 200–400 signs need manual curation.
- **Sumerian outside ORACC** projects
- **Akkadian dialects** disambiguated
- **Translations beyond English** (#46 ties in)

---

## 5. Lexical & dictionary roadmap (Phase 6–9)

Migrated from `PLAN/PRIVATE-TODO.md`. Some items may already be partially done; verify before picking up.

### Phase 6 — activate lexical resources

- Populate `lexical_tablet_occurrences` from token data (background job; join through `token_readings` and `lemmatizations`)
- Build REST endpoints for signs/lemmas/senses (planned list in `gs-expert-data-model/lexical-api.md`)
- Token viewer lexical popup (click → show all possible lemmas, senses, signs)

### Phase 7 — Dictionary & Sign Explorer UI

- Search bar w/ autocomplete across 61k lemmas
- Filters: language, POS, source, period, dialect (needs Phase 3.3 above)
- Multi-source comparison view (ePSD2 vs ORACC)
- Source attribution badges
- Sign detail pages with Unicode + Borger + all values + lemmas + composite components + tablet occurrences
- Lemma detail pages with senses, signs that write it, cognates, attestation counts

### Phase 8 — Advanced lexical

- Semantic field classification (12 hierarchical categories already seeded)
- Confidence scoring for token → lemma matches
- Manual curation interface (scholarly verification, flag uncertain, track curator, export to ORACC)
- Cross-language navigation (Sumerogram explorer, cognate chains, etymology)

### Phase 9 — Data quality & expansion

- Tablet occurrence analytics (genre/period/region/co-occurrence)
- Import remaining ORACC projects (Phase 5 dependencies)
- Hittite resources, Elamite dictionaries, CAD integration
- Duplicate detection across sources; conflict resolution interface

---

## 6. Quick wins

Migrated from PRIVATE-TODO. Low effort, high cleanup value:

- **Attribution facets** — filter `/tablets` by `atf_source` / `translation_source`
- **Filter UX polish** — dropdowns, active-state chips, clear-all behavior
- **Verify** eBL translation attribution still renders alongside CDLI/ORACC display
- **"Back to Tablets"** button on Tablet viewer
- **Breadcrumb navigation**
- **Loading states** for API calls
- **Error boundaries and fallbacks**
- **Cache or index filter options** — `get_filter_options()` runs 4 DISTINCT on 353k rows per page load (also in `gs-expert-data-model/query-patterns.md`)
- **Redis** for frequent lookups
- **EXPLAIN ANALYZE pass** on slow queries
- **DB connection pooling** tuning
- **Pagination** for large result sets
- **OpenAPI/Swagger annotation** pass (overlaps with section 1.2)
- **ER diagrams** for the data model
- **Import pipeline troubleshooting guide** (now mostly handled by `gs-expert-integrations/sources.md`)

---

## 7. Bugs & data integrity (not yet filed as issues)

### Translation pipeline backlog

Confirmed but unverified-fixed:

- **Migration 011** (`011_lemmatization_language.sql`) — adds per-word `language` to `lemmatizations`. Need to confirm applied to production and that `11_import_lemmatizations.py` (or its v2 equivalent `oracc_lemmatizations.py`) backfills per-word language from ORACC CDL.
- **Translation panel** must appear on tablets with translations (e.g., P001282, P108651) — verify.
- **Interlinear glosses** — lemma indexing fix was applied; verify render is correct.
- **Bilingual language indicators** appear on ORACC-lemmatized bilingual tablets — verify.

### Data integrity (issue #49 covers some of this)

- 5 confirmed bugs affect data accuracy and will surface in Translation Builder / Knowledge Bar (per PRD-006a). Pinpoint, add regression fixtures to `gs-curator-artifacts/catalog.yaml`.

### Citation phases remaining (#22)

- 8 of 12 citation scripts (03–10) still pending in connector form.
- Many CDLI 302 redirects to handle; CSV fallback planned.

---

## Maintenance

When an idea graduates to actionable work: file a GitHub issue, link the issue here, and either delete the section or mark it `[FILED: #NNN]`. When a bug is fixed: remove from section 7 and add a regression fixture (`gs-curator-artifacts/catalog.yaml`).

`gs-curator-docs` doesn't enforce freshness on this file specifically — it's a backlog, not an authority — but bump `modified:` when sections change meaningfully.
