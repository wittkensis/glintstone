---
name: gs-expert-integrations
description: Glintstone connector framework — porting v1 import scripts, connector anatomy, ETL patterns, and gotchas. Use when writing or porting any Glintstone ingestion connector.
metadata:
  question: "How do I write or port an ingestion connector against Glintstone's connector framework?"
  created: 2026-02-21
  modified: 2026-05-11
  context: "Began life as the glintstone-connector skill during the ingestion migration (issue #60). Renamed to gs-expert-integrations during the 2026-05-11 knowledge architecture overhaul to match the new naming convention and to pair with gs-scout-integrations (the outside-view sibling)."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#60"]
  related_skills: [gs-expert-data-model, gs-scout-integrations, gs-curator-docs, gs-curator-artifacts]
  supersedes: ".claude/skills/glintstone-connector/SKILL.md"
  superseded_by: null
  triggers: [glintstone, connector, port, ingestion, SourceConnector, ModelConnector, ingestion.cli, "new data source", "dead letter"]
---

# Glintstone Connector Framework

Full patterns in [framework.md](framework.md).

## Quick Reference

- All connectors live in `ingestion/connectors/`
- Subclass `SourceConnector` (or `ModelConnector` for ML runs)
- Implement `extract()` and `load()`; override `discover()`, `transform()`, `verify()` as needed
- `id` must match what other connectors declare in `runs_after`
- `discover()` returns a checksum → unchanged sources short-circuit to `no_op`
- Use `upsert_batch()` from `ingestion/loader.py` — handles conflict policies + stats
- Dead-letter bad rows via `ctx.dead_letter(...)`, never raise
- Tests: write a `_Synthetic*` connector in the test file, hit real Neon DB

## Port checklist

1. Read the v1 script in `source-data/import-tools/`
2. Identify target tables and unique keys
3. Write connector, run `python -m ingestion.cli list` to confirm registry picks it up
4. Smoke-test `extract()` with a FakeCtx before touching the DB
5. Mark retired in `source-data/import-tools/README.md`
