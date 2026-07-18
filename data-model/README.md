---
question: "What's the canonical data-model directory layout, and where does each schema artifact live?"
created: 2026-02-22
modified: 2026-07-17
context: "Flattened during the 2026-05-11 overhaul: the v2/ subdir was collapsed into data-model/, the v2-naming was dropped, and the narrative .md documentation moved out. As of 2026-07-17 (#872) the narrative docs live on the GitHub Wiki (they briefly lived in docs/data-model/ but that folder was removed on 2026-05-11), and the migrations path was corrected to data-model/migrations/. This directory holds schema definitions, mappings, and the migration runner."
status: active
audience: [engineers, claude]
owners: [eric]
related_issues: []
related_skills: [gs-expert-data-model, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# data-model/

Schema is owned by [`glintstone-schema.yaml`](glintstone-schema.yaml). Migrations live in [`migrations/`](migrations/) (`NNN_description.sql`) and are tracked by `_migrations` in Postgres.

## Files in this directory

| File | Purpose |
|---|---|
| [`glintstone-schema.yaml`](glintstone-schema.yaml) | Full schema definition (70+ tables) |
| [`glintstone-schema-api.yaml`](glintstone-schema-api.yaml) | API-surface view |
| [`import-pipeline.yaml`](import-pipeline.yaml) | Full ETL specification |
| [`source-mapping.yaml`](source-mapping.yaml) | Per-source field mappings |
| [`source-schemas/`](source-schemas/) | Reference schemas for external data (CDLI, ORACC, OGSL, eBL, ePSD2) |
| [`migrate.py`](migrate.py) | SQL migration runner |

## Narrative documentation (GitHub Wiki)

The long-form data-model narrative moved to the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki) on 2026-05-11. See the wiki's Data Model section for:

| Topic | What it covers |
|---|---|
| Data sources | Per-source licenses, access methods, field mappings |
| Data quality | Trust architecture, competing interpretations, evidence chains |
| ML integration | BabyLemmatizer, DETR, Akkademia model integration |
| Data issues | Known data-quality issues from pressure testing |
| Citation pipeline | Citation pipeline approach |
| Import-pipeline guide | ETL pipeline overview |

## Migrations

Migrations live in [`migrations/`](migrations/) as `NNN_description.sql`.

```bash
python data-model/migrate.py status
python data-model/migrate.py up
```

Tables are owned by `wittkensis`; the app connects as `glintstone`. New tables and sequences need explicit `GRANT` — see `.claude/skills/gs-expert-data-model/migrations.md` for the workflow.

## When to load the skill

For any question about the schema, the lexical API (`core/lexical.py`), or query patterns, load `.claude/skills/gs-expert-data-model/`. It is the operational companion to this directory.
