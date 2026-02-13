# Glintstone

Federated cuneiform research platform. Raw tablet to full translation in a single interface.

## Why Glintstone

Cuneiform research is fragmented across CDLI (catalog and images), ORACC (linguistic annotations), eBL (editions and fragment joining), ePSD2 (dictionaries), and others. No single platform shows you the complete picture for a tablet -- what's been photographed, transliterated, annotated, and translated -- or tells you what's missing.

Glintstone federates these sources into one interface built around a 5-stage pipeline: **Image > OCR > ATF > Lemmas > Translation**. Every tablet shows its pipeline status so you can see at a glance what exists and where gaps remain.

**For Assyriologists:** Unified search across sources, dictionary lookups inline with transliterations, quality transparency per tablet, and gap identification showing where human expertise is needed most.

**For ML researchers:** Structured training data linking sign annotations to linguistic ground truth, a sign detection inference pipeline (DETR), and a schema designed to connect OCR outputs back to lexical databases.

---

## Data Sources

### Integrated

| Source | Provides | Records | Notes |
|--------|----------|---------|-------|
| **CDLI** catalog | Tablet metadata (P-numbers, museum numbers, period, provenience, genre, language) | 10,215 artifacts | CSV export from cdli.earth |
| **CDLI** ATF | Transliterations in ATF format | 135,200 inscriptions | Parsed from `cdliatf_unblocked.atf` (86 MB) |
| **CDLI** translations | Multi-language translations | 5,599 translations across 9 languages | Extracted from inline `#tr.XX:` markers in ATF |
| **ORACC/DCCLT** glossaries | Dictionary entries (Sumerian, Akkadian, Old Babylonian, Standard Babylonian, proper nouns) | 21,054 entries, ~40,000 variant forms | From DCCLT gloss-*.json files |
| **OGSL** (via ORACC) | Cuneiform sign inventory with Unicode codepoints and all known readings | 3,367 signs, ~15,000 sign values | ogsl-sl.json |
| **ORACC** lemmas | Word-by-word linguistic annotations (citation form, part of speech, language) | 308,610 lemmas | From ORACC project corpora. Only a fraction of available ORACC data is imported -- dozens of project zip archives (rime, ribo, rinap, saao, cams, etcsl, etc.) are publicly available and downloaded to `data/sources/ORACC/` but not yet ingested. This is a high-priority next step. |
| **CompVis** | Sign bounding-box annotations for ML training | 81 tablets, 8,109 annotations | cuneiform-sign-detection-dataset |
| **eBL** OCR data | Sign detection training data | Annotated tablet images | cuneiform-ocr-data |

### Not Yet Integrated

| Source | Status |
|--------|--------|
| **CAD** (Chicago Assyrian Dictionary) | PDF digitization tools exist (`data/tools/cad-digitization/`), data not yet imported |
| **Live ML inference** | DETR model trained (173 sign classes, mAP@50 = 43.1%) but runs in mock mode due to mmcv ARM64 incompatibility. Akkademia translation model available but not yet wired to UI. Both are ready to activate with minor infrastructure work. |

---

## Data Schema

All data converges on the **P-number** (CDLI artifact identifier) as the universal join key. Each source contributes a layer to the pipeline.

### Layer 1: Tablet Identity (CDLI)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `artifacts` | p_number (PK), designation, museum_no, period, provenience, genre, language | Core metadata for every tablet |
| `composites` | q_number (PK), designation, exemplar_count_cache | Multi-tablet composite texts (Q-numbers) |
| `artifact_composites` | p_number, q_number (compound PK) | Links individual tablets to composites |

### Layer 2: Text (CDLI ATF)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `inscriptions` | p_number (FK), atf, transliteration_clean, source, is_latest | Raw ATF markup and searchable clean text. Multiple versions possible; `is_latest=1` marks current. |
| `translations` | p_number (FK), translation, language, source | Human translations. Languages: en, de, ts, it, fr, es, dk, ca, fa. Unique per (p_number, language, source). |

### Layer 3: Linguistics (ORACC)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `lemmas` | p_number (FK), lang, cf (citation form), form (tablet spelling), pos | Word-by-word annotations. `form` contains sign tokens with compound signs, determinatives, and subscripts. |
| `glossary_entries` | entry_id (PK), headword, citation_form, guide_word, language, pos, icount | Dictionary headwords. Languages: sux, akk, akk-x-stdbab, akk-x-oldbab, qpn. |
| `glossary_forms` | entry_id (FK), form, count | Variant spellings for each dictionary entry |

### Layer 4: Signs (OGSL)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `signs` | sign_id (PK), utf8, unicode_hex, sign_type, most_common_value | Cuneiform sign inventory. Types: simple, compound (`\|A.AN\|`), variant (`A@g`). |
| `sign_values` | sign_id (FK), value, sub_index, frequency | All known readings for a sign. Frequency computed from lemma corpus. |
| `sign_word_usage` | sign_id (FK), entry_id (FK), sign_value, usage_count, value_type | Links signs to dictionary words. `value_type`: logographic, syllabic, or determinative. Derived from parsing lemma forms. |

### Layer 5: Machine Learning

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `sign_annotations` | p_number (FK), sign_label, bbox (x/y/w/h as %), confidence, source, image_type | Bounding-box detections on tablet images. Sources: compvis, ebl, manual, ml. |
| `pipeline_status` | p_number (PK), has_image, has_ocr, has_atf, has_lemmas, has_translation | Tracks 5-stage completeness per tablet |

### Layer 6: Application

| Table | Purpose |
|-------|---------|
| `collections`, `collection_members` | User-created tablet groupings |
| `language_stats`, `period_stats`, `provenience_stats`, `genre_stats` | Pre-aggregated filter counts for UI performance |
| `museums`, `excavation_sites` | Reference lookup tables (museum codes, site codes) |

### How It Connects

```
artifacts (P-number) ─────────────────────────────────────────
  ├── inscriptions         ATF text from CDLI
  ├── translations         human translations from CDLI ATF
  ├── lemmas               word annotations from ORACC
  ├── sign_annotations     bounding boxes from CompVis/eBL/ML
  ├── pipeline_status      computed completeness
  └── artifact_composites ── composites (Q-number)

signs (OGSL) ─────────────────────────────────────────────────
  ├── sign_values          all readings per sign
  └── sign_word_usage ──── glossary_entries (ORACC/DCCLT)
                              └── glossary_forms
```

---

## Design Philosophy

- **Pipeline-first visibility** -- every view foregrounds the 5-stage pipeline so researchers immediately see what's complete and what's missing
- **Data/app separation** -- the SQLite database lives in `database/`, independent of the web app in `app/`. Either can be backed up, moved, or replaced without affecting the other
- **On-demand fetching** -- images and ATF data are fetched from CDLI when first requested, then cached locally. No massive upfront downloads required
- **Gap identification** -- pipeline indicators highlight where human expertise or ML contribution would have the most impact
- **Academic attribution** -- every data point traces back to its originating project and the researchers who produced it. Glintstone federates but does not obscure -- the scholars and institutions behind CDLI, ORACC, eBL, and ePSD2 built the foundation this platform stands on, and their contributions must remain visible and credited throughout the interface. *The current UI is lacking here -- making source attribution and academic credit more prominent is a critical next step.*
- **Source provenance** -- every data point tracks its origin (CDLI, ORACC, CompVis, etc.) so researchers can assess reliability

---

## Project Structure

```
CUNEIFORM/
├── app/
│   └── public_html/           PHP web application
│       ├── api/               REST endpoints (ATF, glossary, thumbnails, ML, dictionary)
│       ├── tablets/           Tablet list, detail, search views
│       ├── dictionary/        Dictionary and sign browsers
│       ├── includes/          Shared PHP (db.php, components, helpers)
│       └── assets/            CSS (Kenilworth tokens), JS (vanilla), images
│
├── database/
│   ├── glintstone.db          SQLite database (~300 MB)
│   └── images/                Cached tablet images and thumbnails
│
├── data/
│   ├── sources/               Raw source data (see SETUP.md files in each sub-repo)
│   │   ├── CDLI/              Catalog CSV, ATF file, images
│   │   ├── ORACC/             Project corpora, glossaries, OGSL
│   │   ├── eBL/               Electronic Babylonian Literature fragments
│   │   ├── ePSD2/             Sumerian dictionary data
│   │   ├── compvis-annotations/   Sign detection dataset (sub-repo)
│   │   └── ebl-annotations/       OCR training data (sub-repo)
│   └── tools/
│       ├── download/          Data fetcher scripts
│       ├── import/            Database import scripts (Python)
│       ├── validate/          Data quality checks
│       ├── cad-digitization/  CAD PDF processing tools
│       └── image-library/     Image management utilities
│
├── ml/
│   ├── service/               FastAPI sign detection service (localhost:8000)
│   │   ├── app.py             4 endpoints: /health, /classes, /detect-signs, /detect-signs-by-path
│   │   ├── inference.py       DETR model wrapper
│   │   └── sign_mapping.json  173 sign classes with OGSL + Unicode mappings
│   └── models/                ML model repos (see SETUP.md in each)
│       ├── akkademia/         Akkadian transliteration (sub-repo)
│       ├── deepscribe/        Elamite OCR (sub-repo)
│       └── ebl_ocr/           DETR sign detection checkpoint
│
├── ops/
│   ├── setup.sh               One-time environment setup (~15 min)
│   ├── start.sh               Start all services (Valet + ML)
│   ├── stop.sh                Stop all services
│   └── SERVER-SETUP.md        Manual setup and troubleshooting
│
└── RESEARCH/                  Domain research, personas, reference materials
```

---

## Getting Started

### Prerequisites

- macOS with Homebrew
- PHP 8.4+
- Python 3.9+ (for ML service)
- Composer (installed by setup script)

### First-Time Setup

```bash
./ops/setup.sh
```

Installs Homebrew dependencies, Composer, Laravel Valet, and links the project. Takes about 15 minutes.

### Daily Use

```bash
./ops/start.sh
```

Starts Valet (Nginx + PHP-FPM), the ML detection service, and opens http://glintstone.test.

Press Ctrl+C or run `./ops/stop.sh` to stop everything.

### Data Setup

Source data is not included in the repository. To populate:

1. Download source data using scripts in `data/tools/download/`
2. Clone sub-repos (see SETUP.md files in `ml/models/` and `data/sources/`)
3. Run import pipeline: `data/tools/import/run_full_import.sh`

---

## ML Models

| Model | Task | Architecture | Training Data | Status |
|-------|------|-------------|---------------|--------|
| [Akkademia](https://github.com/gaigutherz/Akkademia) | Akkadian transliteration | BiLSTM (also HMM, MEMM) | RINAP corpora via ORACC | Available, 96.7% accuracy. Not yet connected to UI. |
| [DeepScribe](https://github.com/oi-deepscribe/deepscribe) | Elamite cuneiform OCR | CNN/ResNet | Persepolis Fortification Archive (100K+ annotations) | Code only, no trained weights. |
| eBL OCR | Cuneiform sign detection | Deformable DETR + ResNet-50 | eBL annotations (173 classes, 1000 epochs) | Trained (mAP@50 = 43.1%). Mock mode on macOS ARM64. |

See `SETUP.md` in each model directory for clone/download instructions.

---

## Architecture

```
Browser
  |
Valet (Nginx + PHP-FPM)
  |
  +-- PHP app (app/public_html/)
  |     |
  |     +-- SQLite (database/glintstone.db) -- read-only, WAL mode
  |     |
  |     +-- CDLI remote (on-demand image/ATF fetch, cached locally)
  |
  +-- ML Service (ml/service/, FastAPI on localhost:8000)
        |
        +-- DETR model (ml/models/ebl_ocr/)
```

---

## Links

| Resource | URL |
|----------|-----|
| CDLI | https://cdli.earth |
| ORACC | https://oracc.museum.upenn.edu |
| eBL | https://www.ebl.lmu.de |
| ePSD2 | http://oracc.org/epsd2 |
| OGSL | http://oracc.org/ogsl |
| Akkademia | https://github.com/gaigutherz/Akkademia |
| DeepScribe | https://github.com/oi-deepscribe/deepscribe |
| CompVis annotations | https://github.com/CompVis/cuneiform-sign-detection-dataset |
| eBL OCR data | https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data |
