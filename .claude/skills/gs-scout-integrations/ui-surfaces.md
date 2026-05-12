---
question: "If we integrate this new resource, which UI surface would expose it to scholars?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Knowing the placement up front constrains the data shape and the API contract."
status: active
audience: [claude, engineers, designers]
owners: [eric]
related_issues: ["#9", "#33", "#36", "#37", "#54", "#55", "#56", "#58"]
related_skills: [gs-scout-integrations, gs-expert-ui]
supersedes: null
superseded_by: null
---

# UI surfaces — where new data lands

The web app has a small number of well-defined surfaces. Pick one before designing the connector.

## Surface inventory

### 1. Tablet detail page

- **Where**: `/tablets/<P-number>`
- **What lives there**: metadata panel, ATF viewer, translation pipeline, related composites
- **Good fit for**: per-tablet annotations (sign bounding boxes, per-token lemmatization, per-line translations)
- **Issues**: #9 (ATF viewer revamp), #58 (Tablet Viewer PRD), #36

### 2. Knowledge Bar (right rail)

- **Where**: slides in next to tablet detail or translation builder
- **What lives there**: contextual dictionary lookups, sign info, source attribution
- **Good fit for**: lookups keyed to a focused token or sign (lemma cards, sense distinctions, attestation counts)
- **Issues**: #37, #55 (Tablet Details Knowledge Bar PRD), #56 (Translation Assistant PRD)

### 3. Translation Builder

- **Where**: separate workspace for sustained translation work
- **What lives there**: side-by-side ATF + translation columns with token-level interaction
- **Good fit for**: per-token confidence, alternate lemma candidates, scholar suggestions, ML predictions with confidence
- **Issues**: #54

### 4. Browse Tablets (list/grid)

- **Where**: `/tablets`
- **What lives there**: filter sidebar + cards
- **Good fit for**: new filter dimensions (period, provenience, genre, language, pipeline stage), card-level metadata (thumbnails, status badges)
- **Issues**: #57

### 5. Dictionary

- **Where**: `/dictionary`
- **What lives there**: search, browse, lemma/sign/sense detail
- **Good fit for**: new lemma sources, cognate networks, etymology chains, semantic field navigation
- **Issues**: #33

### 6. Global / Semantic search

- **Where**: header search → results page
- **What lives there**: type-aware search across tablets, scholars, lemmas, signs, collections
- **Good fit for**: new entity types to search, semantic embeddings, fuzzy matching
- **Issues**: #25, #38

### 7. Pipeline / Coverage views

- **Where**: planned, not fully built
- **What lives there**: pipeline-stage transparency (which tablets at which stage)
- **Good fit for**: cross-source coverage maps, ML-vs-human comparisons, gap visualization
- **Issues**: #40

### 8. Source / Provenance overview

- **Where**: planned
- **What lives there**: per-source metadata (CDLI, ORACC project X, eBL release Y)
- **Good fit for**: making attribution legible to scholars; surfacing license / freshness
- **Issues**: #39, #41

### 9. Collections

- **Where**: `/collections`
- **What lives there**: curated groupings of tablets
- **Good fit for**: hand-curated demo sets, regression-test scenarios, scholar-shared lists
- **Issues**: #43 (Dynamic Collections)

### 10. Admin / Ingestion dashboard

- **Where**: `/admin/ingestion`
- **What lives there**: connector status, dead-letters, run history
- **Good fit for**: surfacing new connectors so the operator can trigger them

## How to pick

Ask:

1. **Per-tablet** or **per-corpus**?
   - Per-tablet → surfaces 1, 2, 3
   - Per-corpus → surfaces 4, 5, 6, 7

2. **Discovery** or **deep-dive**?
   - Discovery (where to start) → surfaces 4, 6, 9
   - Deep-dive (already on a thing) → surfaces 1, 2, 3, 5

3. **Authoritative reference** or **predicted / contested**?
   - Authoritative → main surface
   - Predicted / contested → surface AS an annotation layer with confidence + source

## When a new resource doesn't fit any surface

That's a signal to:

- Question whether to integrate at all
- Or design a new surface (file an issue first; don't sprinkle UI ad-hoc)

The 10 surfaces above cover ~95% of imaginable integrations. If you keep needing surface #11, scope creep is happening.

## Cross-references

- For the patterns guiding HOW the integration writes to Postgres: [patterns.md](patterns.md)
- For where gaps actually exist: [gap-analysis.md](gap-analysis.md)
- For the visual/markup conventions of each surface: `gs-expert-ui/markup-quality.md`
