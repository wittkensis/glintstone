# Glintstone: Cuneiform Research Platform

## Vision

A collaborative platform providing a unified "raw tablet → full translation" experience for cuneiform research. The ecosystem is currently fragmented across 6+ platforms—Glintstone federates them into a single coherent workflow.

**Core Value Proposition:**
1. Federated search across CDLI, ORACC, eBL, and local data
2. Complete 5-stage pipeline view for every tablet: Image → OCR → ATF → Lemmas → Translation
3. Gap identification with tools to fill them (human + AI contributions)
4. Quality transparency with clear indicators of consensus and confidence
5. Support for all major cuneiform languages: Akkadian, Sumerian, and Elamite

---

## Project Structure

```
/Volumes/Portable Storage/CUNEIFORM/
├── app/                      # Glintstone web application
│   └── public_html/          # PHP frontend (Hostinger-ready)
│       ├── api/              # REST endpoints (atf, glossary, thumbnail)
│       ├── tablets/          # List, detail, search views
│       ├── includes/         # Shared PHP (db.php, header, footer)
│       └── assets/           # CSS, JS, fonts
│
├── database/                 # Separated from app for portability
│   ├── glintstone.db         # SQLite database (144MB)
│   └── images/               # Local tablet images + thumbnails
│
├── data-tools/               # ETL scripts (Python)
│   ├── download/             # Source data fetchers
│   ├── import/               # Database importers
│   ├── parse/                # ATF/JSON parsers
│   └── validate/             # Data validation
│
├── downloads/                # Raw source data (not in git)
│   ├── CDLI/                 # Catalog, ATF files, metadata
│   ├── ORACC/                # Project corpora, glossaries
│   ├── ePSD2/                # Sumerian dictionary
│   ├── eBL/                  # Electronic Babylonian Literature
│   └── CAD/                  # Chicago Assyrian Dictionary
│
├── ML_MODELS/                # Machine learning models
│   ├── akkademia/            # Translation models (ready to use)
│   ├── deepscribe/           # Elamite OCR (code only)
│   └── ebl_ocr/              # Akkadian/Sumerian OCR (needs download)
│
├── _progress/                # Download tracking
├── _logs/                    # Application logs
└── Brief.md                  # This file
```

---

## Data Sources

### Primary Sources

| Source | Content | Records | Status |
|--------|---------|---------|--------|
| **CDLI** | Tablet catalog + ATF transliterations | 10,215 artifacts, 135,200 inscriptions | Imported |
| **CDLI ATF** | Full transliteration file (86MB) | 135,200 tablets with ATF | Imported |
| **CDLI Translations** | Inline `#tr.XX:` in ATF | 5,434 tablets, 9 languages | Imported |
| **ORACC/DCCLT** | Lexical text corpus | 4,980 texts | Imported |
| **OGSL** | Sign list with Unicode mappings | 3,367 signs | Imported |
| **Glossaries** | Dictionary entries (sux, akk) | 21,054 entries | Imported |
| **CDLI Images** | Remote tablet photos | On-demand via API | Working |

### Data Relationships

```
artifacts (P-number)
    ├── inscriptions (ATF text, multiple versions)
    ├── translations (by language: en, de, ts, etc.)
    ├── lemmas (word-by-word annotations)
    ├── pipeline_status (completeness tracking)
    └── artifact_composites → composites (Q-number)

signs (OGSL)
    └── sign_values (readings)

glossary_entries (ePSD2, ORACC glossaries)
```

### Pipeline Status Tracking

Each tablet has a `pipeline_status` row tracking:
- `has_image` — Local file exists OR fetched from CDLI
- `has_atf` — Transliteration available
- `has_lemmas` — Word annotations exist
- `has_translation` — Translation in any language
- `quality_score` — Weighted completeness (0.0–1.0)

**Quality Score Formula:**
```
quality_score = (has_image × 0.2) + (has_atf × 0.3) + (has_lemmas × 0.25) + (has_translation × 0.25)
```

---

## Architecture Decisions

### Tech Stack
- **Frontend:** PHP + vanilla JS (Hostinger shared hosting compatible)
- **Database:** SQLite (portable, no server needed)
- **Styling:** Kenilworth dark theme (custom CSS variables)
- **ML API:** Python FastAPI (separate service on Railway/Render)

### Key Design Choices

1. **Data/App Separation:** Database and images in `/database/`, not inside `/app/`. Enables independent backup and deployment.

2. **On-Demand Fetching:** Images and ATF fetched from CDLI when needed, then cached locally. Avoids massive upfront downloads.

3. **Pipeline-First UI:** Every view shows the 5-stage pipeline status. Users immediately see what's complete vs. missing.

4. **Local-First, API-Enhanced:** Core functionality works offline. External APIs add breadth (full CDLI catalog) but aren't required.

5. **Translation Extraction:** Translations parsed from inline `#tr.XX:` markers in ATF files (CDLI convention), not a separate data source.

---

## Current Implementation Status

### Completed (This Session)

- [x] Project reorganization (data-tools, downloads, database separation)
- [x] CDLI ATF import (135,200 inscriptions from 86MB file)
- [x] Translation extraction (5,434 tablets, 9 languages)
- [x] Pipeline status tracking with quality scores
- [x] Thumbnail API with CDLI fallback chain
- [x] On-demand ATF fetching from CDLI API
- [x] Tablet list with pipeline filters
- [x] Tablet detail with full pipeline view
- [x] Translation display on detail page
- [x] Glossary word popups (click ATF word → definition)
- [x] Search page with results

### Database Stats

| Table | Records |
|-------|---------|
| artifacts | 10,215 |
| inscriptions | 135,200 |
| translations | 5,599 (5,434 unique tablets) |
| lemmas | 308,610 |
| signs | 3,367 |
| glossary_entries | 21,054 |
| pipeline_status | ~135,000 |

### Translation Languages
- English (en): 5,370
- Transliteration Sumerian (ts): 133
- German (de): 60
- Italian (it): 25
- French (fr): 7
- Spanish (es): 1
- Danish (dk): 1
- Catalan (ca): 1
- Persian (fa): 1

---

## Remaining Work

### Phase 1: Polish Local POC
- [ ] Add lemma display to detail page
- [ ] Improve ATF syntax highlighting
- [ ] Add sign popup (click sign → OGSL data)
- [ ] Handle edge cases in ATF parsing

### Phase 2: ML Integration
- [ ] Test Akkademia models locally
- [ ] Create Python ML API wrapper
- [ ] Add "Generate AI Translation" button
- [ ] Display confidence scores

### Phase 3: Collaboration Features
- [ ] User registration/login
- [ ] Contribution submission
- [ ] Voting system
- [ ] Discussion threads
- [ ] Quality dashboard

### Phase 4: Production Deployment
- [ ] Deploy PHP to glintstone.org (Hostinger)
- [ ] Migrate SQLite → MySQL
- [ ] Deploy ML API to Railway
- [ ] Configure CORS and caching

### Phase 5: Federated Search
- [ ] CDLI API client for full catalog
- [ ] ORACC JSON fetcher
- [ ] ePSD live lookups
- [ ] Unified search merging all sources

---

## File Reference

### Import Scripts
- `data-tools/import/import_cdli_atf.py` — ATF transliterations
- `data-tools/import/import_translations.py` — Extract `#tr.XX:` lines
- `data-tools/import/import_to_sqlite.py` — Full data import

### API Endpoints
- `/api/thumbnail.php?p=P000001&size=200` — Square thumbnails
- `/api/atf.php?p=P000001&fetch=1` — ATF with CDLI fetch
- `/api/glossary.php?q=lugal` — Dictionary lookup
- `/api/glossary-check.php` — Batch definition check

### Key PHP Files
- `includes/db.php` — Database connection + query functions
- `tablets/list.php` — Paginated tablet grid with filters
- `tablets/detail.php` — Full pipeline view
- `tablets/search.php` — Text search

---

## External Platform Comparison

| Platform | Strengths | Gaps Glintstone Fills |
|----------|-----------|----------------------|
| **CDLI** | 390K tablet catalog, images | No inline dictionary, no ML, no lemma display |
| **ORACC** | Deep linguistic annotation | Separate from images, complex interface |
| **eBL** | Live editions, fragment joining | First millennium only, no translation workflow |
| **ePSD2** | Comprehensive Sumerian dictionary | Standalone, no corpus integration |
| **Babylonian Engine** | AI translation (96.7% accuracy) | Web-only, no CDLI integration |

**Glintstone's Unique Value:** Single interface showing complete pipeline status, identifying gaps, and providing tools to fill them with both human expertise and AI assistance.

---

## Deployment Target

**Domain:** glintstone.org (Hostinger shared hosting)

**Architecture:**
```
glintstone.org (Hostinger)
├── PHP frontend
├── MySQL database (migrated from SQLite)
└── Static assets

api.glintstone.org or Railway
└── Python ML API (Akkademia, future OCR)
```

---

## Contact & Resources

- **CDLI:** https://cdli.earth
- **ORACC:** https://oracc.museum.upenn.edu
- **eBL:** https://www.ebl.lmu.de
- **ePSD2:** http://oracc.org/epsd2
- **Akkademia:** https://github.com/gaigutherz/Akkademia
- **DeepScribe:** https://github.com/edwardclem/deepscribe
