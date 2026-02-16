# Data Sources

Glintstone federates cuneiform research data from multiple open-access projects. This document describes each source, what it provides, how it is accessed, and its licensing terms.

Every record imported into Glintstone carries an `annotation_run_id` linking it to the source that produced it. This provenance chain is the backbone of the trust infrastructure -- see [data-quality.md](data-quality.md) for details.

---

## CDLI (Cuneiform Digital Library Initiative)

The largest single source of cuneiform metadata. CDLI provides the universal artifact identifier (P-number) that serves as Glintstone's primary join key.

**License**: CC0 (public domain)

### Catalog

- **File**: `cdli_cat.csv` (bulk export from cdli.earth)
- **Access**: Manual download (no live API for bulk catalog)
- **Records**: 353,283 artifacts with 64 metadata fields
- **Key fields**: P-number, designation, museum number, excavation number, period, provenience, genre, language, material, object type, dimensions, primary publication, collection, dates referenced
- **Update frequency**: Last bulk dump August 2022. CDLI's data pipeline has been frozen upstream.
- **Null rates** (from live database audit):
  - museum_no: 9.2%, excavation_no: 68%, width/height: 82%, thickness: 91%
  - period: 1.8%, provenience: 3.1%, genre: 1.4%, language: 5.2%
- **Schema target**: `artifacts` table (primary), `artifact_identifiers` (museum_no, excavation_no, primary_publication seeded as separate rows)

### ATF (ASCII Transliteration Format)

- **File**: `cdliatf_unblocked.atf` (86 MB)
- **Access**: Bulk download
- **Records**: 135,200 transliterated texts (~3.5M lines)
- **Structure**: Line-oriented notation with `@surface` markers, `#tr.XX:` translation markers, `>>Q` composite references
- **Adds ~33k stub records**: P-numbers present in ATF but absent from catalog CSV
- **Schema targets**: `text_lines` (line-level decomposition), `surfaces` (from @markers), `translations` (from #tr lines), `composites` and `artifact_composites` (from >>Q markers)

### Translations

- **Extracted from**: Inline `#tr.XX:` markers in ATF file
- **Records**: 5,599 translations across 9 languages (en, de, ts, it, fr, es, dk, ca, fa)
- **Schema target**: `translations` table

### Images

- **Access**: On-demand fetch from cdli.earth/dl, cached locally
- **Format**: JPEG photographs and line drawings
- **Coverage**: Varies by collection; many tablets have no published images
- **IIIF**: Not yet implemented. CDLI has partial IIIF support; integration is planned.

### Publications API

- **Access**: REST API (cdli.earth), no authentication, CC0
- **Records**: 16,725 publications, ~390k artifact-publication links
- **Format**: Structured bibliographic data with BibTeX keys
- **Schema targets**: `publications`, `publication_authors`, `artifact_editions`
- **Import order**: API data imported first (confidence 1.0), CSV fallback for gaps

### CSV Supplementary Data

- **Extracted from**: `cdli_cat.csv` freetext fields
- **Provides**: ~20k citation strings, ~4k collation records, ~7k fragment join references
- **Schema targets**: `scholarly_annotations`, `fragment_joins`
- **Confidence**: Lower than API data (0.3-0.7 depending on regex parse quality)

---

## ORACC (Open Richly Annotated Cuneiform Corpus)

The richest source of linguistic annotation for cuneiform texts. ORACC is organized as independent scholarly projects, each covering a specific corpus.

**License**: CC BY-SA 3.0 (per project; some may vary)

### Projects

Glintstone downloads all available ORACC project zip archives. Currently integrated or available:

| Project | Corpus | Coverage |
|---------|--------|----------|
| dcclt | Digital Corpus of Cuneiform Lexical Texts | Lexical lists, school texts |
| epsd2 | electronic Pennsylvania Sumerian Dictionary | Sumerian dictionary (1.8 GB) |
| saao (saa01-saa20) | State Archives of Assyria Online | Neo-Assyrian state correspondence |
| rinap (rinap1-5) | Royal Inscriptions of the Neo-Assyrian Period | Royal inscriptions |
| riao (riao1-3) | Royal Inscriptions of Assyria Online | Earlier Assyrian royal inscriptions |
| etcsri | Electronic Text Corpus of Sumerian Royal Inscriptions | Sumerian royal texts |
| blms | Babylonian Literary and Mythological Texts | Literary texts |
| hbtin | Hellenistic Babylonia: Texts, Iconography, Names | Late Babylonian texts |
| dccmt | Digital Corpus of Cuneiform Mathematical Texts | Mathematical texts |
| ribo | Royal Inscriptions of Babylonia Online | Babylonian royal inscriptions |
| amgg | Akkadian Medicine and Greco-Roman connections | Medical texts |
| ogsl | ORACC Global Sign List | Sign inventory (see below) |

Several additional projects (rime, etcsl, cams, ctij) are known to exist but return server errors when fetched.

### Access method

- **API**: Each project publishes a zip archive at `http://oracc.org/{project}/json`
- **Contents per project**:
  - `catalogue.json` — project-specific artifact metadata with Pleiades geographic IDs
  - `corpus/*.json` — per-text CDL (Chunk-Delimiter-Lemma) trees with sign-level linguistic annotation
  - `glossary/gloss-{lang}.json` — dictionary entries, variant forms, senses
  - `geojson/*.geojson` — archaeological site coordinates (6 projects)

### Lemmatization

- **Records**: ~309k lemma tokens from corpus JSON across all projects
- **Coverage**: ~7,500 texts lemmatized out of 389k total artifacts (approximately 2% coverage)
- **Structure**: CDL trees decompose each text into nested nodes: chunk > lemma > grapheme
- **Language codes**: ISO-style (sux, akk, akk-x-stdbab, akk-x-oldbab, qpn, akk-x-neoass, etc.)
- **Schema targets**: `tokens`, `token_readings`, `lemmatizations`, `morphology`

### Glossaries

- **Records**: ~21k dictionary entries, ~40k variant forms, ~5k entries with sense data
- **Sources**: gloss-sux.json (Sumerian), gloss-akk.json (Akkadian), gloss-akk-x-stdbab.json (Standard Babylonian), gloss-akk-x-oldbab.json (Old Babylonian), gloss-qpn.json (proper nouns)
- **Schema targets**: `glossary_entries`, `glossary_forms`, `glossary_senses`

---

## OGSL (ORACC Global Sign List)

The canonical cuneiform sign inventory used as Glintstone's primary sign identification system.

**License**: Part of ORACC (CC BY-SA 3.0)
**Access**: `ogsl-sl.json` from ORACC zip

- **Signs**: 3,367 entries with Unicode codepoints and all known readings
- **Sign values**: ~15,000 reading values with sub-indices
- **GDL definitions**: JSON structural definitions for compound signs (e.g., |A.AN|)
- **Sign types**: simple, compound (|X.Y|), modified (@g gunu, @t tenu, @s sheshig)
- **Schema targets**: `signs`, `sign_values`, `sign_variants`
- **Concordance role**: OGSL sign_id is the canonical identifier. MZL and ABZ numbers are mapped via Unicode codepoints as a bridge. See [data-quality.md](data-quality.md) for concordance gap details.

---

## CompVis (Cuneiform Sign Detection Dataset)

Sign bounding-box annotations for machine learning training.

**License**: MIT
**Access**: GitHub sub-repo (CompVis/cuneiform-sign-detection-dataset)

- **Tablets**: 81 Neo-Assyrian tablets
- **Annotations**: 8,109 sign bounding boxes (11,070 including metadata rows)
- **Labels**: MZL integer numbers (Borger's Mesopotamisches Zeichenlexikon)
- **Damage codes**: 0=background, 1=intact, 2=broken/uncertain
- **Coordinates**: Pixel-absolute, converted to percentage-based for resolution independence
- **Schema target**: `sign_annotations`
- **Concordance requirement**: MZL labels must be resolved to OGSL sign_ids. ~200-400 remain unresolved after auto-matching via Unicode bridge.

---

## eBL (Electronic Babylonian Literature)

Fragment-level scholarly editions with OCR training data and bibliographic citations.

**License**: Research use (varies by component)
**Access**: GitHub sub-repos + REST API

### OCR Training Data

- **Source**: cuneiform-ocr-data (GitHub)
- **Content**: Annotated tablet images for DETR sign detection model training
- **Classes**: 173 sign classes
- **Schema target**: `sign_annotations` (future)

### Sign Concordance

- **Files**: ebl.txt, mzl.txt
- **Content**: eBL internal names to ABZ numbers to Unicode
- **Role**: Bridge data for MZL/ABZ to OGSL concordance mapping

### Bibliography API

- **Access**: REST API (ebl.lmu.de), may require authentication token
- **Format**: CSL-JSON (Citation Style Language)
- **Content**: Fragment-level citations
- **Schema target**: `publications`, `artifact_editions`
- **Attribution requirement**: "eBL - Electronic Babylonian Literature" must appear when displaying eBL-sourced data

---

## ePSD2 (electronic Pennsylvania Sumerian Dictionary)

Comprehensive Sumerian dictionary, hosted as an ORACC project.

**License**: Part of ORACC (CC BY-SA 3.0)
**Access**: ORACC project zip (epsd2)

- **Size**: 1.8 GB of dictionary data
- **Coverage**: Comprehensive Sumerian lexicon with attestation counts, forms, and senses
- **Schema target**: `glossary_entries`, `glossary_forms`, `glossary_senses`

---

## Citation Enrichment Sources

These sources backfill bibliographic metadata and scholar identification. See [citation-pipeline-summary.md](citation-pipeline-summary.md) for the full pipeline.

### OpenAlex

- **Access**: REST API, no auth, CC0
- **Provides**: DOI backfill for publications (15-30% coverage), ORCID identification for scholars (10-20%)
- **Schema targets**: Enriches `publications.doi` and `scholars.orcid`

### Semantic Scholar

- **Access**: REST API, rate-limited
- **Provides**: Citation graphs for publications with DOIs
- **Schema target**: `entity_relationships` (partially)

### KeiBi (Keilschriftbibliographie)

- **Access**: No API. Manual BibTeX export required (contact Tubingen)
- **Records**: ~90,000 bibliography entries
- **Schema target**: `publications`
- **Note**: Largest single bibliography source, but acquisition requires manual effort

### Scholar Directories

- **Who's Who in Cuneiform Studies**: ~500-1000 scholar records (web scrape)
- **Wikipedia Assyriologists category**: ~200 scholars (web scrape)
- **Schema target**: `scholars`

---

## Not Yet Integrated

### CAD (Chicago Assyrian Dictionary)

- **Status**: PDF digitization tools built (`data/v1-schema-tools/cad-digitization/`), data not yet extracted
- **Content**: 26 volumes covering the complete Akkadian lexicon
- **License**: Public domain (copyright expired)
- **Planned approach**: PDF to text (Google Gemini API), then structured extraction to `glossary_entries`

### BabyLemmatizer Output

- **Status**: Model available, import pathway designed but not yet run
- **Content**: Automated POS-tagging and lemmatization in CoNLL-U format
- **Schema targets**: `lemmatizations`, `morphology` (via annotation_runs with source_type='model')
- **See**: [ml-integration.md](ml-integration.md) for full details

---

## Source Priority and Conflict Resolution

When sources disagree on the same field:

- **Identity metadata** (period, provenience, genre, language): CDLI is authoritative. ORACC enriches with subgenre, supergenre, geographic coordinates, and project membership.
- **Linguistic annotation**: ORACC human annotations at highest confidence. BabyLemmatizer output stored as competing interpretation with lower confidence. Multiple analyses coexist via `is_consensus` flags.
- **Bibliographic data**: CDLI API data imported first (confidence 1.0). CSV-derived data fills gaps at lower confidence. Cross-source deduplication uses cascading match: DOI exact (1.0) > bibtex_key (0.95) > title+year (0.8) > short_title+volume (0.9). Below 0.7 staged for manual review.

For field-level source mappings, see [source-to-v2-mapping.yaml](source-to-v2-mapping.yaml).
