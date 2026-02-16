# Glintstone

A federated cuneiform research platform. Glintstone aggregates open data from across the field into a single interface organized around a five-stage pipeline: **Image > OCR > ATF > Lemmas > Translation**. Every artifact shows its pipeline status so researchers can see what exists, what's missing, and where human expertise or new tools could make the most difference.

This project would not exist without the decades of scholarship behind [CDLI](https://cdli.earth), [ORACC](https://oracc.museum.upenn.edu), [eBL](https://www.ebl.lmu.de), [ePSD2](http://oracc.org/epsd2), [OGSL](http://oracc.org/ogsl), and the [CompVis](https://github.com/CompVis/cuneiform-sign-detection-dataset) and [eBL OCR](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data) annotation teams. The researchers and institutions behind these projects built the foundation this platform stands on -- cataloging hundreds of thousands of artifacts, producing transliterations and linguistic annotations, training sign detection models, and making all of it openly available. Glintstone's role is to bring these resources together and make them more accessible. Credit and source attribution are structural requirements, not afterthoughts.

We are early in this process. There is a great deal to learn about the domain, and it will take sustained iteration -- with input from working Assyriologists -- to get this right.

---

## What Glintstone Does

Cuneiform research data is fragmented. Tablet photographs live in one system, transliterations in another, linguistic annotations in a third, dictionaries in a fourth. No single platform shows the complete picture for a given tablet, or tells you what's missing.

Glintstone federates these sources around a **pipeline-first** view:

```
Image  >  OCR  >  ATF  >  Lemmas  >  Translation
```

For each of the ~389,000 artifacts in the database, the interface shows which stages are complete and where gaps remain. This makes it easy to find tablets that have transliterations but no lemmatization, or lemmatization but no translation -- the places where scholarly effort has the highest marginal value.

Beyond pipeline visibility, the data model supports:

- **Competing interpretations** -- multiple readings or lemmatizations of the same token, each with provenance and confidence
- **Full provenance tracking** -- every annotation traces to the scholar, tool, or import process that produced it
- **Sign concordance** -- unified lookup across OGSL, MZL, ABZ, and Unicode sign identification systems
- **Citation resolution** -- a three-tier system linking artifacts to their publication history

For the full data model, see the [v2 schema](schema-architecture/glintstone-schema-v2/glintstone-v2-schema.yaml).

---

## Data Sources

### Integrated

| Source | Provides | License |
|--------|----------|---------|
| **CDLI** (cdli.earth) | Artifact catalog (353k), ATF transliterations (135k texts), translations (5.6k), tablet images (on-demand), publications API | CC0 |
| **ORACC** (12+ projects) | Lemmatization (~309k tokens), glossaries (~21k entries), project-specific catalog enrichment, geographic coordinates | CC BY-SA 3.0 |
| **OGSL** | Cuneiform sign inventory (3,367 signs, ~15k reading values, Unicode mappings) | CC BY-SA 3.0 |
| **CompVis** | Sign bounding-box annotations (81 tablets, 8.1k annotations) | MIT |
| **eBL** | OCR training data, sign concordance data, fragment-level citations | Research use |

ORACC projects currently downloaded: dcclt, epsd2, saao, rinap, riao, etcsri, blms, hbtin, dccmt, ribo, amgg, ogsl. Several additional projects (rime, etcsl, cams, ctij) are known to exist but return server errors when fetched.

CDLI and OGSL data are imported from bulk downloads. ORACC project data is fetched via zip API. CDLI images are fetched on demand and cached locally. The CDLI publications endpoint provides structured bibliographic data via REST API.

For detailed field mappings, update frequencies, and access methods per source, see [data-sources.md](schema-architecture/glintstone-schema-v2/data-sources.md).

### Not Yet Integrated

| Source | Status |
|--------|--------|
| **CAD** (Chicago Assyrian Dictionary) | PDF digitization tools built, extraction not yet run |
| **BabyLemmatizer** output | Model available, import pathway designed, not yet executed |
| **KeiBi** (Keilschriftbibliographie) | ~90k entries, manual acquisition required |

---

## Data Model

The schema is organized into five layers, reflecting the stages of cuneiform research:

**Physical** -- Where are signs on the artifact? Surfaces, bounding boxes, damage states. Sources: CompVis annotations, eBL OCR, ML models.

**Graphemic** -- What signs are present? The cuneiform sign inventory with cross-system concordance (OGSL canonical, with MZL and ABZ numbers mapped via Unicode). Source: OGSL.

**Reading** -- How are signs read in context? ATF transliteration decomposed into lines, tokens, and competing readings. A single token position can have multiple readings from different scholars or models. Sources: CDLI ATF, ORACC corpus.

**Linguistic** -- What do the words mean? Lemmatization (dictionary headword mapping), morphological analysis, and translations. Supports multiple competing analyses per token with provenance. Sources: ORACC corpus and glossaries, BabyLemmatizer (future).

**Semantic** -- Higher-level meaning. Named entity registry (persons, deities, places), entity relationships (knowledge graph), cross-text parallels, and authority reconciliation (links to Wikidata, Pleiades, etc.). Derived from linguistic layer.

All layers converge on the **P-number** (CDLI artifact identifier) as the universal join key. Every record carries an `annotation_run_id` linking it to its source -- see [data-quality.md](schema-architecture/glintstone-schema-v2/data-quality.md) for how this provenance system works.

For the full schema specification, see the [v2 schema YAML](schema-architecture/glintstone-schema-v2/glintstone-v2-schema.yaml). For import details, see the [import pipeline guide](schema-architecture/glintstone-schema-v2/import-pipeline-guide.md).

---

## Formats

Glintstone works with several identification, annotation, and interchange formats used across the field:

**Artifact identification**
- **P-numbers** (CDLI artifact identifiers) as the universal join key, with museum numbers, excavation numbers, and publication designations mapped via an identifier concordance table
- **Q-numbers** for composite (reconstructed) texts assembled from multiple exemplars

**Transliteration and annotation**
- **ATF** (ASCII Transliteration Format) -- the standard line-oriented notation for cuneiform transliteration, parsed into surfaces, lines, and tokens
- **CoNLL-U** -- token-level linguistic annotation format used by BabyLemmatizer for import/export interchange. Maps to the schema's lemmatization and morphology tables. See [ml-integration.md](schema-architecture/glintstone-schema-v2/ml-integration.md).

**Sign identification**
- **OGSL** -- canonical sign names (e.g., "KA", "LUGAL", "|A.AN|"), used as primary identifiers
- **MZL** -- Borger's Mesopotamisches Zeichenlexikon integer codes (used by CompVis annotations)
- **ABZ** -- Borger's ABZ integer codes (used by eBL)
- **Unicode** -- cuneiform block codepoints (U+12000-U+1254F), serving as the bridge for cross-system concordance

**Citation and interoperability**
- **W3C Web Annotation** -- scholarly annotations exportable to W3C Web Annotation Data Model format for federation with external tools
- **IIIF** -- planned for image interoperability, not yet implemented

---

## Open Challenges

These are the significant gaps, assumptions, and trade-offs in the current design. We document them here because transparency about limitations is essential for a research tool.

**Coverage gaps**
- Only ~2% of the 389k artifacts have ORACC linguistic annotation. The remaining 98% exist at the identity or text layer only.
- The CDLI bulk catalog export has not been updated since August 2022. Artifacts added after this date are not reflected.
- Sign concordance between MZL, OGSL, and ABZ is incomplete. Auto-matching via Unicode resolves ~90%, but ~200-400 signs require manual curation.
- Several ORACC projects (rime, etcsl, cams, ctij) are unavailable due to server-side errors.

**Design trade-offs**
- GDL (sign-level structure) stored as JSON on tokens rather than in normalized tables. Simpler to import, but limits sign-level queries.
- Sumerian verbal morphology is contested across scholarly frameworks (Jagersma, Zolyomi, Edzard). The schema supports multiple analyses as competing annotations rather than picking one framework.
- CDLI and ORACC sometimes disagree on period, genre, or provenience. CDLI is treated as authoritative for identity fields; ORACC enrichment stored in separate columns.
- Translations link to text lines, not individual tokens. No source currently provides token-level translation alignment.

**Open questions**
- How to handle IIIF image integration properly
- Whether to normalize GDL JSON into queryable tables in a future version
- How to version ORACC data across releases (currently tracked via annotation_runs timestamps)

For the full list of 12 data quality issues found during pressure testing, see [data-issues.md](schema-architecture/glintstone-schema-v2/data-issues.md).

---

## Getting Started

### Prerequisites

- macOS with Homebrew
- PHP 8.4+, Python 3.9+
- Composer (installed by setup script)

### Setup

```bash
# One-time setup (~15 min)
./ops/setup.sh

# Start all services
./ops/start.sh
```

Opens at http://glintstone.test. See `ops/SERVER-SETUP.md` for manual setup and troubleshooting.

### Data

Source data is not included in the repository. To populate:

1. Download source data: see `data/sources/SETUP.md`
2. Clone ML model sub-repos: see `ml/models/SETUP.md`
3. Run import pipeline: `data/v2-schema-tools/run_full_import.sh`

---

## Documentation

| Document | Purpose |
|----------|---------|
| [v2 Schema](schema-architecture/glintstone-schema-v2/glintstone-v2-schema.yaml) | Full schema specification (70+ tables, annotated) |
| [Data Sources](schema-architecture/glintstone-schema-v2/data-sources.md) | Per-source field mappings, licenses, access methods |
| [Data Quality](schema-architecture/glintstone-schema-v2/data-quality.md) | Trust architecture, competing interpretations, evidence chains |
| [ML Integration](schema-architecture/glintstone-schema-v2/ml-integration.md) | BabyLemmatizer, DETR, Akkademia model integration |
| [Import Pipeline](schema-architecture/glintstone-schema-v2/import-pipeline-guide.md) | 19-step ETL overview |
| [Data Issues](schema-architecture/glintstone-schema-v2/data-issues.md) | 12 critical issues from pressure testing |
| [Citation Pipeline](schema-architecture/glintstone-schema-v2/citation-pipeline-summary.md) | Citation sourcing from 9 external sources (built) |
| [Source Mappings](schema-architecture/glintstone-schema-v2/source-to-v2-mapping.yaml) | Field-level source-to-schema mappings with null rates |
| [Import Pipeline Spec](schema-architecture/glintstone-schema-v2/import-pipeline.yaml) | Full technical ETL specification |

---

## Links

| Resource | URL |
|----------|-----|
| CDLI | https://cdli.earth |
| ORACC | https://oracc.museum.upenn.edu |
| eBL | https://www.ebl.lmu.de |
| ePSD2 | http://oracc.org/epsd2 |
| OGSL | http://oracc.org/ogsl |
| CompVis annotations | https://github.com/CompVis/cuneiform-sign-detection-dataset |
| eBL OCR data | https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data |
| Akkademia | https://github.com/gaigutherz/Akkademia |
| BabyLemmatizer | https://github.com/asahala/BabyLemmatizer |
