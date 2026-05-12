---
name: gs-orient-project
description: Always-on orientation. Loads at session start to ground Claude in Glintstone's identity, two-tier architecture, current row counts, and the routing map to other gs-* skills.
metadata:
  question: "What is Glintstone, where does its code live, and which skill should I use for X?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Created during the knowledge architecture overhaul as the always-on orientation skill. Replaces the stale SessionStart hook that referenced retired v1 paths."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#60"]
  related_skills: [gs-expert-integrations, gs-expert-data-model, gs-expert-ui, gs-expert-deployment, gs-expert-assyriology, gs-scout-integrations, gs-curator-artifacts, gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: [glintstone, cuneiform, tablet, p-number, P-number, ATF, scholar, "what is", "where is", "where does", "how does", project overview]
---

# Glintstone — project orientation

**Production academic platform** unifying open cuneiform research data (CDLI, ORACC, eBL, ePSD2, OGSL, +) for working Assyriologists. Scholars' careers depend on proper attribution; data integrity is non-negotiable.

## In 60 seconds

```
Browser
  │
nginx (.test in dev, Hostinger VPS in prod)
  │
  ├── Web app (port 8002, FastAPI + Jinja2) ───► API (port 8001, FastAPI + JSON) ───► PostgreSQL 17 (Neon)
  └── Marketing site (static)
```

**Two-tier rule**: the web app NEVER touches the database directly. It calls the API over HTTP. This exists so the API can serve future consumers (ML pipelines, other tools, public access).

**P-number** is the universal join key. Every artifact, every annotation, every record traces back to a P-number (CDLI artifact ID, e.g. `P227657`). Composites use Q-numbers.

**Five-stage pipeline** per artifact: Captured → Recognized → Transcribed → Lemmatized → Translated.

## Where things live

```
api/                  REST API
app/                  Web app (Jinja2 templates, vanilla JS)
core/                 Shared: config, database pool, BaseRepository, lexical helpers
ingestion/            ETL framework — SEE gs-expert-integrations
  base.py             SourceConnector / ModelConnector contracts
  cli.py              `python -m ingestion.cli list|run|status|dead-letters`
  connectors/         One file per source (cdli_catalog.py, oracc_lemmatizations.py, …)
data-model/           Schema YAMLs + migrate.py + source-schemas/
docs/data-model/      Narrative docs about the schema + pipeline
source-data/
  migrations/         NNN_*.sql — SEE gs-expert-data-model
  sources/            Raw data (gitignored, ~16 GB)
ml/                   ML model integrations (BabyLemmatizer, DETR, Akkademia)
ops/
  local/              setup/start/stop, nginx config
  deploy/             deploy.sh + rollback.sh — SEE gs-expert-deployment
  hooks/              git hooks (warn-only freshness checks)
tests/                pytest suite
docs/                 Long-form reference (onboarding, research, opportunities, personas)
.claude/skills/gs-*/  This knowledge base
```

## Current scale (as-of 2026-05-11)

| Table | Rows |
|---|---|
| artifacts | 353,283 |
| text_lines | 1,395,668 |
| tokens | 3,957,240 |
| translations | 43,777 |
| lexical_lemmas | 61,435 |
| lexical_senses | 155,491 |
| scholars | 20,490 |
| publications | 16,725 |

Coverage gap: only ~2% of artifacts are lemmatized, ~35% have ATF, ~12% have translations. **Expect NULLs everywhere.**

## Routing map — which skill for what

| User says or task touches | Load skill |
|---|---|
| "add a new connector / source", `ingestion/connectors/*.py`, `ingestion/base.py` | **gs-expert-integrations** |
| ATF, lemma, sign, glossary, Sumerian/Akkadian morphology, ORACC | **gs-expert-assyriology** |
| schema, migration, query, repository, `source-data/migrations/`, `core/lexical.py` | **gs-expert-data-model** |
| CSS, tokens, BEM, markup, accessibility, semantic HTML, `app/static/` | **gs-expert-ui** |
| deploy, staging, rollback, VPS, GitHub Actions, Neon branch, Cloudflare R2, env, secret | **gs-expert-deployment** |
| HuggingFace URL, new model, new dataset, "should we integrate X" | **gs-scout-integrations** |
| "find a tablet with…", "give me a test scholar / lemma / sign", "scenario for…", "interesting Q-number" | **gs-curator-artifacts** |
| commit, push, ship, PR, release | **gs-curator-docs** |

## Non-negotiables

- **Source attribution is structural.** Every row carries `annotation_run_id` → who/when/version. Never silently overwrite.
- **Competing interpretations are a feature.** Two scholars disagreeing on a lemma both get stored.
- **Tables owned by `wittkensis`, app user is `glintstone`.** New tables need explicit `GRANT`.
- **Two-tier boundary**: web layer calls API via httpx; no direct DB access from `app/`.
- **macOS Python SSL**: `urllib` fails for some endpoints; shell out to `curl` via `subprocess.run(...)`.
- **psycopg rollback trap**: `conn.rollback()` undoes ALL uncommitted changes. Use `NOT EXISTS` or `ON CONFLICT` instead of try/except `UniqueViolation`.

## Deeper reading

- [docs/engineer-onboarding.md](../../../docs/engineer-onboarding.md) — Day 1–5 ramp-up
- [docs/assyriology-101.md](../../../docs/assyriology-101.md) — 5-minute domain primer
- [data-model/](../../../data-model/) — canonical schema + per-source docs
- [`README.md`](../../../README.md) — public-facing project intro
- [`CLAUDE.md`](../../../CLAUDE.md) — durable rules every Claude session loads
