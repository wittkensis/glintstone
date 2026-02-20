# Glintstone

Five thousand years of writing. Less than 2% translated.

Glintstone unifies the open cuneiform record -- CDLI, ORACC, eBL, and a dozen more sources -- into one platform where scholars can see exactly what's understood, what isn't, and where effort matters most. Every artifact is tracked through a five-stage pipeline: **Captured > Recognized > Transcribed > Lemmatized > Translated**.

This project would not exist without the decades of scholarship behind [CDLI](https://cdli.earth), [ORACC](https://oracc.museum.upenn.edu), [eBL](https://www.ebl.lmu.de), [ePSD2](http://oracc.org/epsd2), [OGSL](http://oracc.org/ogsl), and the [CompVis](https://github.com/CompVis/cuneiform-sign-detection-dataset) and [eBL OCR](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data) teams. Credit and source attribution are structural requirements.

We are early. There is a great deal to learn about the domain, and it will take sustained iteration -- with input from working Assyriologists -- to get this right.

---

## What Glintstone Does

Cuneiform research data is fragmented across incompatible systems. Glintstone compounds what CDLI, ORACC, and the broader scholarly ecosystem have built -- making each resource more queryable, more connected, and more meaningful.

**Exploration** -- New views across existing data. Search and use the API across all open data: artifacts, composites, signs, readings, lemmas, and citations.

**Curation** -- See the forest from the trees. Connected data allows aggregation and analysis in new ways. Automated and custom curation methods across tablets, signs, lemmas, and meanings.

**Scholarly Contribution** *(future)* -- Catalyze your impact. Glintstone aims to unlock a new scale of scholarly achievement, with proper recognition for expertise and hard work. This requires significant input from working scholars to build right.

### Pipeline

Every artifact tracked through five stages -- from raw image to translated text. The interface shows what's complete, what's missing, and where scholarly effort has the highest impact.

```
01 Captured      The artifact exists as a digital photograph
02 Recognized    ML-assisted sign detection on the tablet surface
03 Transcribed   The text read into structured notation (ATF)
04 Lemmatized    Every word linked to its dictionary lemma
05 Translated    Meaning rendered in modern language
```

Each artifact also surfaces academic and historical context -- era, genre, place of origin -- drawn dynamically from trusted open sources.

### Data Model

The [v2 schema](data-model/v2/glintstone-v2-schema.yaml) is organized into five layers:

- **Physical** -- Surfaces, bounding boxes, damage states. Sources: CompVis, eBL OCR, ML models.
- **Graphemic** -- Sign inventory with cross-system concordance (OGSL, MZL, ABZ via Unicode).
- **Reading** -- ATF transliteration decomposed into lines, tokens, and competing readings.
- **Linguistic** -- Lemmatization, morphology, translations. Multiple competing analyses per token with provenance.
- **Semantic** -- Named entities, knowledge graph, cross-text parallels, authority reconciliation (Wikidata, Pleiades).

All layers converge on the **P-number** (CDLI artifact identifier) as the universal join key. Every record carries an `annotation_run_id` linking it to its source.

---

## Data Sources

### Artifacts & Objects

| Source | Provides | License |
|--------|----------|---------|
| **CDLI** | Artifact catalog (353k records), excavation contexts, provenance, photographs, physical measurements | CC0 |
| **Pleiades** | Geographic coordinates for ancient places; provenience resolution via ORACC GeoJSON | CC BY 3.0 |

### Texts & Corpora

| Source | Provides | License |
|--------|----------|---------|
| **CDLI** | ATF transliterations (135k texts, ~4M tokens), translations (43.7k), composite text links, fragment joins | CC0 |
| **ORACC** (12 projects) | Lemmatization (~309k tokens), glossaries (~21k entries), project-specific catalog enrichment | CC BY-SA 3.0 |

ORACC projects: DCCLT, RINAP, SAAo, RIAo, RIBo, RIME, ETCSRI, ETCSL, BLMS, CAMS, AMGG, HBTIN.

### Signs & Lexica

| Source | Provides | License |
|--------|----------|---------|
| **OGSL** | Cuneiform sign inventory (3,367 signs, ~15k reading values, Unicode/MZL/ABZ concordance) | CC BY-SA 3.0 |
| **ePSD2** | Sumerian lexicon (~21k entries), sign-level glossary data, lemma forms | CC BY-SA 3.0 |
| **DCCLT** | Cuneiform lexical tradition -- sign lists, vocabularies, scribal training texts | CC BY-SA 3.0 |

### Machine Learning

| Source | Provides | License |
|--------|----------|---------|
| **CompVis** | Sign bounding-box annotations (81 tablets, 8.1k annotations) | CC BY 4.0 |
| **eBL annotations** | Sign detection training data, MZL sign concordance | CC BY 4.0 |
| **DeepScribe** | Computer vision pipeline for cuneiform sign detection (Persepolis Fortification Archive) | MIT |
| **BabyLemmatizer** | Neural POS tagger and lemmatizer for Akkadian | Apache 2.0 |

### Bibliography & Citation

| Source | Provides | License |
|--------|----------|---------|
| **CDLI** | Publications bibliography (16.7k pubs), artifact-publication links, edition histories | CC0 |
| **eBL bibliography** | Fragment-level citation data via live API | Research use |
| **OpenAlex** | Publication DOI enrichment, scholar ORCID identifiers | CC0 |
| **Semantic Scholar** | Citation and reference graph data keyed to DOIs | Free API |
| **KeiBi** | Comprehensive Assyriology bibliography (~90k entries) | Research use |

### Scholars & Identity

| Source | Provides | License |
|--------|----------|---------|
| **CDLI** | Scholar name registry, ATF editor and author attribution | CC BY-SA |
| **Wikipedia / Wikidata** | Assyriologist name resolution, Wikidata QIDs for disambiguation | CC BY-SA 4.0 / CC0 |

For detailed field mappings, update frequencies, and access methods per source, see [data-sources.md](data-model/v2/data-sources.md).

---

## Tech Stack

- **Backend**: Python 3.9+ / FastAPI / Uvicorn
- **Database**: PostgreSQL (psycopg3)
- **Web**: FastAPI + Jinja2 (server-rendered)
- **Proxy**: nginx (local dev: `*.glintstone.test` domains)
- **Import pipeline**: Python scripts (`source-data/import-tools/`)
- **Marketing site**: Static HTML + Tailwind

---

## Project Structure

```
api/                    FastAPI app (api.glintstone.org)
app/                    Server-rendered web app (app.glintstone.org)
core/                   Shared Python package (config, database, repository)
data-model/
  migrate.py            Migration runner
  migrations/           Numbered SQL migrations
  seeds/                Seed data
  v2/                   v2 schema, docs, mappings
  v1/                   v1 reference
  source-schemas/       Raw source format documentation
source-data/
  import-tools/         Numbered import scripts (01-15)
  sources/              Raw source data (not in repo)
marketing/              Static marketing site (glintstone.org)
ml/models/              ML model sub-repos
ops/
  local/                Local dev setup, nginx, start/stop scripts
  deploy/               VPS provisioning and deployment
```

---

## Getting Started

### Prerequisites

- macOS with Homebrew
- Python 3.9+
- PostgreSQL 15+
- nginx

### Setup

```bash
# One-time setup
./ops/local/setup.sh

# Start all services
./ops/local/start.sh
```

Opens at http://app.glintstone.test (web) and http://api.glintstone.test (API). See `ops/deploy/DEPLOY.md` for production deployment.

### Data

Source data is not included in the repository. To populate:

1. Download source data into `source-data/sources/`
2. Copy `.env.example` to `.env` and configure database credentials
3. Run migrations: `python data-model/migrate.py`
4. Run import pipeline scripts in `source-data/import-tools/` (numbered order)

---

## Open Challenges

**Coverage gaps**
- Only ~2% of 389k artifacts have ORACC linguistic annotation.
- CDLI bulk catalog export frozen since August 2022.
- Sign concordance (MZL/OGSL/ABZ) ~90% auto-matched; ~200-400 signs need manual curation.

**Design trade-offs**
- GDL stored as JSON on tokens rather than normalized tables.
- Sumerian verbal morphology contested across frameworks -- schema supports competing annotations.
- CDLI/ORACC disagreements on period, genre, provenience handled via separate columns.

**Open questions**
- GDL normalization into queryable tables
- ORACC data versioning across releases

See [data-issues.md](data-model/v2/data-issues.md) for the full list.

---

## Beyond Cuneiform

The core infrastructure is language-agnostic. Trust tracking, provenance chains, and annotation ecosystems apply to any extinct or undeciphered writing system. Cuneiform is the proving ground -- but the same architecture could serve Linear A, Linear B, Egyptian, Mayan, Proto-Elamite, Ugaritic, Meroitic, Indus Valley, Etruscan, Luwian, Rongorongo, and Cypro-Minoan.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [v2 Schema](data-model/v2/glintstone-v2-schema.yaml) | Full schema specification (70+ tables) |
| [Data Sources](data-model/v2/data-sources.md) | Per-source field mappings, licenses, access methods |
| [Data Quality](data-model/v2/data-quality.md) | Trust architecture, competing interpretations, evidence chains |
| [ML Integration](data-model/v2/ml-integration.md) | BabyLemmatizer, DETR, Akkademia model integration |
| [Import Pipeline](data-model/v2/import-pipeline-guide.md) | 19-step ETL overview |
| [Data Issues](data-model/v2/data-issues.md) | Critical issues from pressure testing |
| [Citation Pipeline](data-model/v2/citation-pipeline-summary.md) | Citation sourcing from 9 external sources |
| [Source Mappings](data-model/v2/source-to-v2-mapping.yaml) | Field-level source-to-schema mappings |
| [Import Pipeline Spec](data-model/v2/import-pipeline.yaml) | Full technical ETL specification |
| [Deployment](ops/deploy/DEPLOY.md) | VPS provisioning and deployment |

---

## Collaboration

Glintstone is open source (CC BY-SA 4.0) and looking for collaborators:

- **Assyriologists & Philologists** -- Feedback on trust, workflows, and new tools
- **ML Experts & Computational Linguists** -- Data architecture and API for a rapidly changing field
- **Software Engineers** -- See open repo Issues.
- **Data Architects** -- Schema design for annotation at scale across projects, versions, and scholarly disagreement
- **Digital Humanities Scholars** -- Linked data, interoperability standards, modeling contested knowledge
- **Librarians & Metadata Specialists** -- Authority control, identifier alignment, cataloging standards

---

## Links

| Resource | URL |
|----------|-----|
| CDLI | https://cdli.earth |
| ORACC | https://oracc.museum.upenn.edu |
| eBL | https://www.ebl.lmu.de |
| ePSD2 | http://oracc.org/epsd2 |
| OGSL | http://oracc.org/ogsl |
| CompVis | https://github.com/CompVis/cuneiform-sign-detection-dataset |
| eBL OCR data | https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data |
| DeepScribe | https://github.com/DigitalPasts/DeepScribe |
| Akkademia | https://github.com/gaigutherz/Akkademia |
| BabyLemmatizer | https://github.com/asahala/BabyLemmatizer |
| OpenAlex | https://openalex.org |
| Pleiades | https://pleiades.stoa.org |
