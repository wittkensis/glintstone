# Glintstone

Five thousand years of writing. Less than 2% translated.

Glintstone unifies the open cuneiform record -- [CDLI](https://cdli.earth), [ORACC](https://oracc.museum.upenn.edu), [eBL](https://www.ebl.lmu.de), and a dozen more sources -- into one platform where scholars can see exactly what's understood, what isn't, and where effort matters most. Every artifact is tracked through a five-stage pipeline: **Captured > Recognized > Transcribed > Lemmatized > Translated**.

This project would not exist without the decades of scholarship behind CDLI, ORACC, eBL, [ePSD2](http://oracc.org/epsd2), [OGSL](http://oracc.org/ogsl), and the [CompVis](https://github.com/CompVis/cuneiform-sign-detection-dataset) and [eBL OCR](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data) teams. Credit and source attribution are structural requirements, not afterthoughts.

We are early. There is a great deal to learn about the domain, and it will take sustained iteration -- with input from working Assyriologists -- to get this right.

## What it does

Cuneiform research data is fragmented across incompatible systems. Glintstone compounds what CDLI, ORACC, and the broader scholarly ecosystem have built -- making each resource more queryable, more connected, and more meaningful.

- **Exploration** -- New views across existing data. Search and use the API across artifacts, composites, signs, readings, lemmas, and citations.
- **Curation** -- Connected data enables aggregation and analysis in new ways, across tablets, signs, lemmas, and meanings.
- **Scholarly contribution** *(future)* -- Unlock a new scale of scholarly achievement, with proper recognition for expertise. This requires significant input from working scholars to build right.

Every artifact moves through five stages -- raw image to translated text -- and the interface shows what's complete, what's missing, and where scholarly effort has the highest impact:

```
01 Captured      The artifact exists as a digital photograph
02 Recognized    ML-assisted sign detection on the tablet surface
03 Transcribed   The text read into structured notation (ATF)
04 Lemmatized    Every word linked to its dictionary lemma
05 Translated    Meaning rendered in modern language
```

## Quickstart

**Prerequisites:** Python 3.13+ and a PostgreSQL `DATABASE_URL`.

```bash
cp .env.example .env                 # set DATABASE_URL=postgresql://...
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python data-model/migrate.py up      # apply schema
./ops/local/start.sh                 # optional nginx-routed local domains
```

Opens at http://app.glintstone.test (web) and http://api.glintstone.test (API).

Ingest data with the connector CLI (`python -m ingestion.cli list|run|status|dead-letters`), or use the `/admin/ingestion` dashboard. See [ingestion/CONTRIBUTING.md](ingestion/CONTRIBUTING.md) to write a connector and [ops/deploy/DEPLOY.md](ops/deploy/DEPLOY.md) to deploy.

## Architecture in brief

A two-tier system: a server-rendered Jinja2 web app (`app/`) that never touches the database directly -- it calls a FastAPI service (`api/`) over HTTP, which owns all Postgres access. Data arrives through the `ingestion/` connector framework with DB-backed run tracking, and everything converges on the **P-number** (CDLI artifact identifier) as the universal join key, with each record carrying an `annotation_run_id` linking it to its source.

The [schema](data-model/glintstone-schema.yaml) spans 70+ tables across five layers -- Physical, Graphemic, Reading, Linguistic, Semantic. See [data-model/README.md](data-model/README.md) for the directory layout and the [Data Model wiki](https://github.com/wittkensis/glintstone/wiki) for the full narrative. Backend is Python 3.13 / FastAPI / psycopg 3 on PostgreSQL 17, deployed via GitHub Actions to a Hostinger VPS with symlink rollback.

The core infrastructure is language-agnostic. Trust tracking, provenance chains, and annotation ecosystems apply to any undeciphered or extinct writing system -- cuneiform is just the proving ground.

## Documentation

| Topic | Where |
|-------|-------|
| Engineering rules & conventions | [CLAUDE.md](CLAUDE.md) |
| Directory & data-model layout | [data-model/README.md](data-model/README.md) |
| Full schema (70+ tables) | [glintstone-schema.yaml](data-model/glintstone-schema.yaml) · [source mappings](data-model/source-mapping.yaml) · [ETL spec](data-model/import-pipeline.yaml) |
| Writing an ingestion connector | [ingestion/CONTRIBUTING.md](ingestion/CONTRIBUTING.md) |
| Deployment | [ops/deploy/DEPLOY.md](ops/deploy/DEPLOY.md) |
| Implementation learnings | [LEARNINGS.md](LEARNINGS.md) |
| Data sources, quality, ML integration, open issues | [Project Wiki](https://github.com/wittkensis/glintstone/wiki) |
| Day 1–5 onboarding · domain primer | [Engineer Onboarding](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) · [Assyriology 101](https://github.com/wittkensis/glintstone/wiki/Assyriology-101) |

## Collaboration

Glintstone is open source ([CC BY-SA 4.0](LICENSE)) and looking for collaborators -- Assyriologists and philologists, ML and computational-linguistics experts, software engineers, data architects, digital-humanities scholars, and metadata specialists. See the open repo [Issues](https://github.com/wittkensis/glintstone/issues), or the [wiki](https://github.com/wittkensis/glintstone/wiki) for where the work is heading.
