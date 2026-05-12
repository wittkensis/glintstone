---
question: "What ETL steps populate the schema from source data, and which connectors implement them?"
created: 2026-02-22
modified: 2026-05-11
context: "Updated during the 2026-05-11 knowledge architecture overhaul. The original opening pointed at the retired ingestion/connectors/ path and described 'SQLite' storage; both are wrong — connectors live in ingestion/connectors/ and storage is PostgreSQL. This file remains the human-readable overview; the full spec is in import-pipeline.yaml."
status: active
audience: [engineers, claude]
owners: [eric]
related_issues: []
related_skills: [gs-expert-integrations, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Import Pipeline Guide

This document summarizes the ETL process for populating the schema from source data. For the full technical specification (dependencies, row estimates, validation thresholds), see [import-pipeline.yaml](import-pipeline.yaml).

---

## Architecture

The pipeline follows four stages:

1. **Extract** — source-specific parsers read raw data files (CSV, JSON, ATF, BibTeX)
2. **Transform** — normalization via lookup tables and sign concordance mapping
3. **Load** — upsert into **PostgreSQL** with `annotation_run_id` provenance on every record
4. **Derive** — computed tables, materialized views, `pipeline_status` refresh

All connectors live in [`ingestion/connectors/`](../../ingestion/connectors/) and are subclasses of `SourceConnector` (or `ModelConnector` for ML runs). The connector framework is documented in `.claude/skills/gs-expert-integrations/`. Run via `python -m ingestion.cli`.

---

## Shared Infrastructure

### normalize.py

Canonical mapping functions for the five normalization lookup tables:

- `normalize_period("Old Babylonian (ca. 1900-1600 BC)")` -> `"Old Babylonian"`
- `normalize_provenience("Nippur (mod. Nuffar)")` -> `"Nippur"`
- `normalize_genre("administrative")` -> `"Administrative"`
- `normalize_language("Sumerian")` -> `"sux"`
- `normalize_surface("@obverse")` -> `"obverse"`

### concordance.py

Sign system bridge functions:

- `mzl_to_ogsl(839)` -> `"KA"` (via Unicode codepoint matching)
- `abz_to_ogsl("ABZ123")` -> OGSL sign_id
- `ogsl_to_unicode("KA")` -> `"U+12157"`

Auto-match via Unicode covers ~90% of signs. ~200-400 require manual curation.

### checkpoint.py

`ImportCheckpoint` class for resumable imports:

- SIGINT/SIGTERM signal handling with graceful state save
- Atomic state file writes (JSON in `_progress/` directory)
- Source checksums detect upstream changes since last run
- Progress reporting: processed / inserted / updated / skipped / errors

### annotation_run.py

Every import step creates an `annotation_runs` record before writing data. All rows carry the `annotation_run_id` FK. Fields: `source_name`, `source_version`, `tool_name`, `tool_version`, `started_at`, `completed_at`, `config_snapshot`, `row_count`.

---

## 19-Step Sequence

### Stage 1: Foundation (Steps 1-4)

| Step | Target Tables | Source | Estimated Rows |
|------|--------------|--------|----------------|
| 1. Seed lookup tables | period_canon, language_map, genre_canon, provenience_canon, surface_canon | Manual curation from live data audit | ~500 total |
| 2. Create retroactive annotation_runs | annotation_runs | Manual (13 records for existing v1 data sources) | 13 |
| 3. Seed scholars | scholars | ORACC project metadata, CDLI credits | 200-500 |
| 4. Import signs + concordance | signs, sign_values, sign_variants | OGSL sign list + MZL/ABZ bridge data | 3,367 signs, ~15k values |

### Stage 2: Core Data (Steps 5-10)

| Step | Target Tables | Source | Estimated Rows |
|------|--------------|--------|----------------|
| 5. Import artifacts | artifacts | CDLI catalog CSV + ORACC enrichment | 389,715 |
| 6. Seed artifact identifiers | artifact_identifiers | artifacts.museum_no, .excavation_no, etc. | ~500k |
| 7. Parse surfaces | surfaces | ATF @surface markers + CompVis view_desc | ~300k |
| 8. Parse text_lines | text_lines | ATF line-by-line decomposition + ORACC CDL | ~2M |
| 9. Import tokens | tokens | ORACC CDL nodes + ATF tokenizer | ~5M |
| 10. Import token_readings | token_readings | ORACC CDL grapheme-level data | ~8M |

### Stage 3: Linguistic Layer (Steps 11-14)

| Step | Target Tables | Source | Estimated Rows |
|------|--------------|--------|----------------|
| 11. Import lemmatizations | lemmatizations | ORACC corpus (86k real identifications) | ~86k |
| 12. Parse morphology | morphology | ORACC morph strings, structured decomposition | ~50k |
| 13. Import glossary | glossary_entries, glossary_forms, glossary_senses | ORACC glossary JSON (all projects) | ~30k entries, ~50k forms, ~5k senses |
| 14. Import translations | translations | ATF #tr.XX: markers | ~8k |

### Stage 4: Annotations and Knowledge (Steps 15-17)

| Step | Target Tables | Source | Estimated Rows |
|------|--------------|--------|----------------|
| 15. Import sign annotations | sign_annotations | CompVis (MZL -> OGSL concordance resolution) | 11,070 |
| 16. Derive named entities | named_entities, entity_mentions | glossary_entries POS tags | ~5k entities, ~20k mentions |
| 17. Import composites | composites, artifact_composites | ATF >>Q markers | 857 composites, 3,771 links |

### Stage 5: Citations and Views (Steps 18-19)

| Step | Target Tables | Source | Status |
|------|--------------|--------|--------|
| 18. Citation pipeline | publications, scholars, artifact_editions, fragment_joins, scholarly_annotations | 9 external sources | **BUILT** (10 scripts in `ingestion/connectors/citations/`) |
| 19. Refresh views | pipeline_status, materialized views | Computed from all tables | Design only |

---

## Execution

### Orchestrator

`run_full_import.sh` runs all steps in dependency order:

```bash
# Full import (all steps)
./ingestion/connectors/run_full_import.sh

# Resume from step N
./ingestion/connectors/run_full_import.sh --from 8

# Dry run (validate sources, no writes)
./ingestion/connectors/run_full_import.sh --dry-run

# Reset database and reimport
./ingestion/connectors/run_full_import.sh --reset
```

### Dependencies

Steps must run in order. Key dependencies:
- Signs (step 4) before sign_annotations (step 15) -- concordance needed
- Artifacts (step 5) before surfaces (step 7), text_lines (step 8)
- Tokens (step 9) before lemmatizations (step 11)
- Publications (step 18) before annotation_runs.publication_id backfill
- All data steps before pipeline_status refresh (step 19)

### Validation

Every step runs post-import checks:
- Row count vs expected (warning if deviation > 5%)
- NULL audit on critical columns
- FK integrity verification
- annotation_run_id NOT NULL enforcement

---

## Current Status

- **Step 18 (citation pipeline)**: Built and tested. 10 scripts + shared libraries + verification scripts in `ingestion/connectors/citations/`.
- **Steps 1-17, 19**: Designed in import-pipeline.yaml. Not yet implemented.
- **Shared infrastructure**: Specified but not coded (normalize.py, concordance.py, checkpoint.py -- pattern established by citation pipeline's `lib/` directory).

For field-level source mappings and transform rules, see [source-mapping.yaml](source-mapping.yaml).
