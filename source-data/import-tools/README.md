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
| 15b | `15_import_compvis_annotations.py` | Import CompVis sign detection bounding boxes |
| 19 | `19_match_translation_lines.py` | Match translations to text_lines by line number |
| 20 | `20_import_collections.py` | Import curated collections |

See `citations/` for the 10-step citation pipeline (publications, editions, bibliography).

See `data-model/v2/import-pipeline-guide.md` for the full pipeline specification.
