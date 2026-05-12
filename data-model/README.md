---
question: "What's the canonical data-model directory layout, and where does each schema artifact live?"
created: 2026-02-22
modified: 2026-05-11
context: "Flattened during the 2026-05-11 overhaul: the v2/ subdir was collapsed into data-model/, the v2-naming was dropped, and the narrative .md documentation moved into docs/data-model/. This directory now holds only schema definitions, mappings, and the migration runner."
status: active
audience: [engineers, claude]
owners: [eric]
related_issues: []
related_skills: [gs-expert-data-model, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# data-model/

Schema is owned by [`glintstone-schema.yaml`](glintstone-schema.yaml). Migrations live in [`../source-data/migrations/`](../source-data/migrations/) and are tracked by `_migrations` in Postgres.

## Files in this directory

| File | Purpose |
|---|---|
| [`glintstone-schema.yaml`](glintstone-schema.yaml) | Full schema definition (70+ tables) |
| [`glintstone-schema-api.yaml`](glintstone-schema-api.yaml) | API-surface view |
| [`import-pipeline.yaml`](import-pipeline.yaml) | Full ETL specification |
| [`source-mapping.yaml`](source-mapping.yaml) | Per-source field mappings |
| [`source-schemas/`](source-schemas/) | Reference schemas for external data (CDLI, ORACC, OGSL, eBL, ePSD2) |
| [`migrate.py`](migrate.py) | SQL migration runner |

## Narrative documentation (lives in `docs/data-model/`)

| Doc | What it covers |
|---|---|
| [docs/data-model/data-sources.md](../docs/data-model/data-sources.md) | Per-source licenses, access methods, field mappings |
| [docs/data-model/data-quality.md](../docs/data-model/data-quality.md) | Trust architecture, competing interpretations, evidence chains |
| [docs/data-model/ml-integration.md](../docs/data-model/ml-integration.md) | BabyLemmatizer, DETR, Akkademia model integration |
| [docs/data-model/data-issues.md](../docs/data-model/data-issues.md) | Known data-quality issues from pressure testing |
| [docs/data-model/citation-pipeline-summary.md](../docs/data-model/citation-pipeline-summary.md) | Citation pipeline approach |
| [docs/data-model/import-pipeline-guide.md](../docs/data-model/import-pipeline-guide.md) | ETL pipeline overview |

## Migrations

Migrations live in [`../source-data/migrations/`](../source-data/migrations/) as `NNN_description.sql`.

```bash
python data-model/migrate.py status
python data-model/migrate.py up
```

Tables are owned by `wittkensis`; the app connects as `glintstone`. New tables and sequences need explicit `GRANT` — see `.claude/skills/gs-expert-data-model/migrations.md` for the workflow.

## When to load the skill

For any question about the schema, the lexical API (`core/lexical.py`), or query patterns, load `.claude/skills/gs-expert-data-model/`. It is the operational companion to this directory.
