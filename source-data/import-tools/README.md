# Import Pipeline

Numbered scripts run in order. Each step depends on earlier steps.

| Step | Script | What It Does |
|------|--------|-------------|
| 01 | `01_seed_lookup_tables.py` | Seed periods, languages, genres from CDLI catalog |
| 02 | `02_seed_annotation_runs.py` | Register data sources (CDLI, ORACC, eBL, etc.) |
| 03 | `03_import_scholars.py` | Import scholar records |
| 04 | `04_import_signs.py` | Import OGSL sign list and reading values |
| 05 | `05_import_artifacts.py` | Import CDLI artifact catalog (353k records) |
| 05b | `05b_enrich_artifacts_oracc.py` | Enrich artifacts with ORACC metadata |
| 06 | `06_seed_artifact_identifiers.py` | Cross-reference museum/excavation numbers |
| 07 | `07_parse_atf.py` | Parse ATF files into text_lines and tokens |
| 10 | `10_import_token_readings.py` | Extract readings from tokens.gdl_json (Phase A) |
| 11 | `11_import_lemmatizations.py` | Import ORACC lemmatization data |
| 13 | `13_import_glossaries.py` | Import ORACC glossary entries and forms |
| 15 | `15_import_epsd2_unified.py` | Import ePSD2 into unified lexical schema (signs, lemmas, senses) |
| 15b | `15b_cleanup_duplicates.sql` | SQL: Remove duplicate signs and associations (Phase 3 fix) |
| 15c | `15c_cleanup_and_reimport.py` | Run cleanup + re-import (Phase 3 orchestration) |
| 15d | `15d_run_full_fix.py` | Full Phase 3 fix: ALTER schema + cleanup + re-import + verify |
| 15e | `15e_verify_results.py` | Verify Phase 3 results (sign counts, associations, subscripts) |
| 16 | `16_import_oracc_glossaries.py` | Import ORACC glossaries (8 projects, 6 languages, dialects) |
| 17 | `17_test_lexical_api.py` | Test lexical API functions with sample queries |
| 18 | `15_import_compvis_annotations.py` | Import CompVis sign detection bounding boxes |
| 19 | `19_match_translation_lines.py` | Match translations to text_lines by line number |
| 20 | `20_import_collections.py` | Import curated collections |
| 21 | `21_import_oracc_credits.py` | Import ORACC per-text credits into artifact_credits |

See `citations/` for the 10-step citation pipeline (publications, editions, bibliography).

See `data-model/v2/import-pipeline-guide.md` for the full pipeline specification.
