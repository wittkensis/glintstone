---
question: "What non-obvious findings, dead ends, and decisions came out of building the agentic summarization + translation-suggestion system?"
created: 2026-05-26
modified: 2026-05-26
context: "Running record kept while building Phase 1 (artifact summaries) and Phase 2 (line translation suggestions) — captures schema gaps, competing genre tables, and the deploy double-compression bug so they aren't rediscovered."
status: active
audience: [engineers, claude]
owners: [eric]
related_issues: []
related_skills: [gs-expert-data-model, gs-expert-agentic]
supersedes: null
superseded_by: null
---

# Agentic System — Implementation Learnings

Running record of non-obvious findings, dead ends, and decisions made while building Phase 1 (artifact summaries) and Phase 2 (line translation suggestions).

---

## 2026-05-26

### annotation_runs has no `trust` column

During design we planned to add a trust signal (uncertain flag when `annotation_runs.trust < 0.7`). The column doesn't exist in any migration; the baseline schema has no such field. Deferred: either add migration 040 to add `trust REAL DEFAULT 1.0` to `annotation_runs`, or use `source_type` as a proxy (`model` runs implicitly less certain than `human`).

**Decision for Phase 1**: Use `source_type = 'human'` vs `source_type = 'model'` as the trust proxy. Emit `(source: human annotation)` vs `(source: model annotation)` in fact text. No schema change needed.

### text_lines has no `atf_language` column

We planned to detect mixed-language by scanning ATF language markers (`%sux`, `%akk`) in `text_lines`. The column doesn't exist; the language signal is embedded in `raw_atf` as inline `%lang` markers, and per-word in `lemmatizations.language`.

**Decision**: Use DISTINCT `lemmatizations.language` for the artifact to detect language mix. This is more reliable than regex on `raw_atf` and already normalized. Cover: only artifacts with lemmatization (completeness ≥ 3).

### genre_canon vs canonical_genres — two parallel genre systems

Two genre lookup tables exist side-by-side:
- `genre_canon(raw_genre, canonical, supergenre)` — baseline table, maps CDLI raw strings
- `canonical_genres(id, name)` + `artifact_genres(p_number, genre_id)` — migration 015, many-to-many junction

`canonical_genres` is the normalized system; `genre_canon` is a lookup helper. For fact assembly, use `artifact_genres` → `canonical_genres` as this is what the ingestion pipeline populates.

### agent_outputs unique index omits model column

`uq_agent_outputs_target` in migration 025 covers `(target_type, target_id, output_type, focus, prompt_version)` but not `model`. Two outputs for the same artifact from Haiku vs Sonnet would silently collide.

Fixed in migration 039: drop + recreate with `model` included.

### deploy.sh double-compression bug

`pg_dump -Fc` (custom format) uses zlib compression internally. The deploy script was also piping through `gzip`, creating double-compressed output with no size benefit but significantly longer runtime. This caused the CI timeout (15 min limit). Fixed in commit `cc0d640`: removed `| gzip`, renamed `.dump.gz` → `.dump`, bumped `timeout-minutes` from 15 to 25.

---

## Schema quick-reference (verified 2026-05-26)

| Need | Column / Table |
|---|---|
| Artifact genre | `artifact_genres` → `canonical_genres.name` |
| Primary language | `artifacts.language_normalized` |
| Per-word language + dialect | `lemmatizations.language` (e.g. `akk-x-oldbab`, `sux`) |
| Composite membership | `artifact_composites.q_number` → `composites` |
| Annotation source type | `annotation_runs.source_type` (`human`/`model`/`hybrid`/`import`) |
| Competing lemmatizations | Multiple rows in `lemmatizations` per `token_id` (different `annotation_run_id`) |
