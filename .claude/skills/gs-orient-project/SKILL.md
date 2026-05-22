---
name: gs-orient-project
description: Always-on orientation. Loads at session start to ground Claude in Glintstone's identity, two-tier architecture, current row counts, and the routing map to other gs-* skills.
metadata:
  question: "What is Glintstone, where does its code live, and which skill should I use for X?"
  created: 2026-05-11
  modified: 2026-05-18
  context: "Created during the knowledge architecture overhaul as the always-on orientation skill. Replaces the stale SessionStart hook that referenced retired v1 paths."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#60"]
  related_skills: [gs-expert-integrations, gs-expert-data-model, gs-expert-ui, gs-expert-deployment, gs-expert-assyriology, gs-scout-integrations, gs-curator-artifacts, gs-curator-docs, gs-audit-hardening]
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
source-data/
  migrations/         NNN_*.sql — SEE gs-expert-data-model
  sources/            Raw data (gitignored, ~16 GB)
ml/                   ML model integrations (BabyLemmatizer, DETR, Akkademia)
ops/
  local/              setup/start/stop, nginx config
  deploy/             deploy.sh + rollback.sh — SEE gs-expert-deployment
  hooks/              git hooks (warn-only freshness checks)
tests/                pytest suite
.claude/skills/gs-*/  This knowledge base
```

Long-form narrative documentation (onboarding, data-model docs, research, opportunities, personas) lives in the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki).

## Current scale (as-of 2026-05-19)

| Table | Rows |
|---|---|
| artifacts | 353,283 |
| text_lines | 1,728,706 |
| tokens | 4,905,814 |
| lemmatizations | 416,911 |
| translations | 43,777 |
| lexical_lemmas | 346,480 |
| lexical_norms | 834,235 |
| lexical_senses | 860,940 |
| glossary_entries | 220,349 |
| scholars | 20,490 |
| publications | 16,725 |

Coverage gap: ~2% of artifacts lemmatized, ~35% have ATF, ~12% have translations. ORACC expanded to ~115 projects (2026-05-19); ~2.4M lemma tokens in dead-letter backlog (texts not yet ATF-parsed). **Expect NULLs everywhere.**

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
| audit, harden, "security review", "deployment review", "performance audit", "run the audit" | **gs-audit-hardening** |
| "frontend audit", "design audit", "css audit", "design system", "frontend entropy", "clean up the css" | **gs-audit-frontend** |

## Non-negotiables

- **Source attribution is structural.** Every row carries `annotation_run_id` → who/when/version. Never silently overwrite.
- **Competing interpretations are a feature.** Two scholars disagreeing on a lemma both get stored.
- **Tables owned by `wittkensis`, app user is `glintstone`.** New tables need explicit `GRANT`.
- **Two-tier boundary**: web layer calls API via httpx; no direct DB access from `app/`.
- **macOS Python SSL**: `urllib` fails for some endpoints; shell out to `curl` via `subprocess.run(...)`.
- **psycopg rollback trap**: `conn.rollback()` undoes ALL uncommitted changes. Use `NOT EXISTS` or `ON CONFLICT` instead of try/except `UniqueViolation`.

## Deeper reading

- [Engineer Onboarding (wiki)](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) — Day 1–5 ramp-up
- [Assyriology 101 (wiki)](https://github.com/wittkensis/glintstone/wiki/Assyriology-101) — 5-minute domain primer
- [Wiki home](https://github.com/wittkensis/glintstone/wiki) — full long-form documentation tree
- [data-model/](../../../data-model/) — canonical schema + per-source docs
- [`README.md`](../../../README.md) — public-facing project intro
- [`CLAUDE.md`](../../../CLAUDE.md) — durable rules every Claude session loads
