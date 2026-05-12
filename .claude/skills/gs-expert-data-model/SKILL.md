---
name: gs-expert-data-model
description: Glintstone schema expert — 5-layer model, migration workflow + freshness, query patterns, lexical-API reference. Use for schema, migrations, repository code, or the lexical lookup functions in core/lexical.py.
metadata:
  question: "What does Glintstone's schema look like, what tables matter, and what skill file should I open for migrations / queries / lexical API?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Created during the 2026-05-11 knowledge architecture overhaul. Owns migration freshness: every commit touching source-data/migrations/ must also touch this skill's migrations.md and data-model/glintstone-schema.yaml. The lexical-api content migrated here from PLAN/lexical-api.md."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#3", "#22"]
  related_skills: [gs-expert-integrations, gs-expert-assyriology, gs-curator-docs, gs-curator-artifacts]
  supersedes: null
  superseded_by: null
  triggers: [schema, migration, postgres, psycopg, query, repository, "data model", "schema", lexical, "lexical_lemmas", "lexical_signs", "core/lexical", "core.lexical", "cross-filter", glintstone-schema]
---

# Glintstone data model

The 5-layer schema, the migration workflow, the repository pattern, and the lexical API.

## When to load which file

| Question | File |
|---|---|
| "Add a new migration / what's already applied / how do GRANTs work?" | [migrations.md](migrations.md) |
| "How do I write a repository query? How do cross-filter counts work? What psycopg gotchas exist?" | [query-patterns.md](query-patterns.md) |
| "How do I look up a lemma by form / get all senses for a sign / walk the sign→lemma→sense chain?" | [lexical-api.md](lexical-api.md) |

## 5-layer model

The schema is intentionally layered so each annotation type carries its own provenance:

```
1. Physical    artifacts → surfaces → surface_images          (CDLI catalog, CompVis, eBL OCR)
2. Graphemic   signs, sign_values, sign_annotations            (OGSL, ML vision)
3. Reading     text_lines → tokens → token_readings            (ATF parser)
4. Linguistic  lemmatizations → morphology → translations      (ORACC, BabyLemmatizer)
5. Semantic    glossary_entries → glossary_senses              (ePSD2, ORACC glossaries)
               glossary_relationships, semantic_fields,
               named_entities, knowledge graph
```

Every row in every table carries `annotation_run_id` linking it to its origin (source name, tool version, timestamp).

## Key tables (current scale, as-of 2026-05-11)

| Table | Rows | Notes |
|---|---|---|
| `artifacts` | 353,283 | Every known cuneiform tablet (CDLI catalog) |
| `surfaces` | 216,272 | obverse/reverse/edges per artifact |
| `text_lines` | 1,395,668 | ATF decomposed |
| `tokens` | 3,957,240 | Individual word-tokens |
| `token_readings` | varies | Per-grapheme readings (Phase A) |
| `translations` | 43,777 | English/German/Arabic/Persian glosses |
| `lemmatizations` | 65,906 | ORACC token→lemma links |
| `signs` / `sign_values` | 3,367 / 10,312 | Legacy OGSL |
| `lexical_signs` | 2,093 | Unified ePSD2 sign inventory |
| `lexical_lemmas` | 61,435 | ePSD2 + 8 ORACC projects |
| `lexical_senses` | 155,491 | Polysemy expanded |
| `lexical_sign_lemma_assoc` | 2,972 | Many-to-many bridge |
| `glossary_entries` | 45,572 | Legacy, migrating to lexical_lemmas |
| `scholars` | 20,490 | Researcher registry |
| `publications` | 16,725 | Academic bibliography |
| `artifact_credits` | 4,501 | ORACC per-text credits |
| `artifact_identifiers` | 1,095,502 | Museum/excavation cross-refs |
| `collections` / `collection_members` | 14 / 335 | Curated tablet groupings |
| `annotation_runs` | varies | Provenance for every row |

## Canon (normalization) tables

These are the bridge between messy source data and canonical filter values:

| Table | Purpose |
|---|---|
| `period_canon` | "Ur III" → group "Third Millennium" |
| `provenience_canon` | "Nippur (mod. Nuffar)" → "Nippur" |
| `language_map` | "sux-x-emesal" → "Sumerian" |
| `genre_canon` | Various genre strings → canonical |
| `surface_canon` | `@obverse` → `obverse` etc. |

Seeded by `ingestion/connectors/lookup_tables.py`.

## Non-negotiables

- **`annotation_run_id` on every row.** This is structural.
- **`wittkensis` owns tables; `glintstone` is the app user.** Run migrations as `wittkensis`. New tables need explicit `GRANT` (see [migrations.md](migrations.md)).
- **No direct DB access from `app/`.** Web layer calls API via httpx.
- **psycopg rollback trap**: `conn.rollback()` undoes ALL uncommitted changes in the transaction. Use `ON CONFLICT` or `NOT EXISTS`, not try/except.

## Canonical schema files

- `data-model/glintstone-schema.yaml` — full spec
- `data-model/glintstone-schema-api.yaml` — API surface
- `data-model/source-mapping.yaml` — field mappings per source
- `data-model/import-pipeline.yaml` — ETL specification
- `docs/data-model/data-issues.md` — known gaps

## Freshness contract

This skill owns these doc-stay-fresh rules (enforced by `gs-curator-docs`):

- Any commit touching `source-data/migrations/*.sql` must also touch [migrations.md](migrations.md) (the rolling migrations table) AND `data-model/glintstone-schema.yaml`.
- Any new table in a migration must add a fixture scenario to `gs-curator-artifacts/catalog.yaml`.
- Row-count changes >5% should refresh the table above and the matching table in `gs-orient-project/SKILL.md`.
