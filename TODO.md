# UI
- Reincorporate lost homepage styling
- Add section to homepage that addresses academics

# Data
- Support multiple CDLI images
- Add about page with schema and CC licenses
- Add academic publishing associations

# Import Status (as of 2026-02-18)

## Currently Running
- **Citation Phase 2** (02_cdli_artifact_editions.py): ~0.5s/artifact × 353k = ~49h.
  Monitor: `tail -f /tmp/citation_pipeline.log`
  Resume if interrupted: `cd source-data/import-tools/citations && bash run_citation_import.sh`
  (no --reset flag; checkpoint resumes where it left off)

## Citation Phases Still Pending (auto-run by orchestrator after Phase 2)
- 03_ebl_bibliography.py — eBL bibliography
- 04_oracc_editions.py — ORACC artifact-edition links
- 05_cdli_csv_supplementary.py — CSV publication_history fallback
- 06_enrich_openalex.py — OpenAlex DOI/abstract enrichment
- 07_import_keibi.py — KeiBi .bib files (skips gracefully if absent)
- 08_enrich_semantic_scholar.py — Semantic Scholar enrichment
- 09_import_scholars_directory.py — Scholar directory
- 10_seed_supersessions.py — Publication supersession chains

## Import Steps Not Yet Built
- **eBL sign annotations**: `source-data/sources/ebl-annotations/cuneiform_ocr_data/heidelberg/`
  contains XML bounding box annotations. Build a script like Step 15 to populate
  `sign_annotations` with annotation_run_id for "ebl-annotations".
- **Named entities** (Step 16): extract PN/GN/DN/RN/WN entries from `glossary_entries`
  and insert into `named_entities` table.
- **Pipeline status views** (Step 19): materialized views for import coverage stats.

## Data Quality — Investigate When Time Allows

### Lemmatization Match Rate (38%)
- 65,906 lemmas inserted; 99,224 "no line match" (line in CDL not found in text_lines)
- Spot-check: `SELECT COUNT(*) FROM text_lines WHERE p_number = 'P000001'` vs CDL file
  `ORACC/dcclt/json/dcclt/corpusjson/P000001.json` — likely many dcclt tablets have
  only partial ATF in the CDLI bulk dump (expected behavior, not a script bug)

### CompVis Unmatched Tablets (12 tablets, ~1,000 annotations lost)
- K01057, K08396, K09237Vs, ND02486 — British Museum / Nimrud tablets absent from Aug 2022 dump
- VAT10601, VAT10657 — VAT tablets not in catalog
- P313634, P314346, P314355, P393668, P404881 — verify these P-numbers exist:
  `SELECT p_number FROM artifacts WHERE p_number IN ('P313634','P314346','P314355','P393668','P404881')`
- P336663b — 'b' suffix (disambiguator) not handled in museum_no lookup

### Surface Type Precision (@edge / @face → "unknown")
- ATF @edge and @face markers stored as "unknown" (CHECK constraint limitation)
- To fix: add 'edge' and 'face' to `surface_canon` table and schema CHECK clause,
  then re-run the ATF parser for affected tablets only

### Citation API 302 Redirects
- Many artifact IDs return HTTP 302 (artifact merged/moved in CDLI); treated as
  "no publications". CSV fallback phase (05) will cover most of these.

## DB State (2026-02-18 ~09:30AM)
| Table                | Count             |
|----------------------|-------------------|
| artifacts            | 353,283           |
| surfaces             | 216,272           |
| text_lines           | 1,395,668         |
| tokens               | 3,957,240         |
| translations         | 43,777            |
| scholars             | 20,490            |
| signs / sign_values  | 3,367 / 10,312    |
| glossary_entries     | 45,572            |
| lemmatizations       | 65,906            |
| sign_annotations     | 7,145             |
| publications         | 16,725            |
| artifact_editions    | ~3,000 (growing)  |
| artifact_identifiers | 1,095,502         |