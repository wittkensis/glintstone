---
question: "Where does every piece of Glintstone documentation live, and which doc do I open for the task I'm doing?"
created: 2026-07-17
modified: 2026-07-17
context: "Created 2026-07-17 (#872) as the single entry point for Glintstone's in-tree docs. The durable docs had grown organically across six module folders (data-model/, ingestion/, ops/, ml/) with no map, and the long-form narrative had migrated to the GitHub Wiki. This index is the one place that tells a reader — human or agent — which doc answers their question and whether it's in-tree or on the wiki."
status: active
audience: [engineers, claude, ops, scholars]
owners: [eric]
related_issues: ["#872"]
related_skills: [gs-curator-docs, gs-orient-project]
supersedes: null
superseded_by: null
---

# Glintstone documentation index

Start here. This page maps every piece of documentation to the task it serves.
Glintstone keeps docs in two places:

- **In-tree** (`*.md` in the repo) — operational runbooks, contracts, and per-module
  references that must version alongside the code they describe.
- **[GitHub Wiki](https://github.com/wittkensis/glintstone/wiki)** — long-form narrative:
  onboarding, the full data-model story, API/MCP reference, research, and opportunities.
  Wiki pages have no YAML header (GitHub renders it as raw text).

If you only read one other file, read [CLAUDE.md](CLAUDE.md) — the durable, non-negotiable
engineering rules.

## By task — "I want to…"

| I want to… | Open |
|---|---|
| Understand what Glintstone is | [README.md](README.md) · [Assyriology 101](https://github.com/wittkensis/glintstone/wiki/Assyriology-101) (domain primer) |
| Know the durable engineering rules | [CLAUDE.md](CLAUDE.md) |
| Ramp up as a new engineer (Day 1–5) | [Engineer Onboarding](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) (wiki) |
| Run the app locally | [README.md → Quickstart](README.md#quickstart) |
| Understand the schema & data-model layout | [data-model/README.md](data-model/README.md) → [Data Model wiki](https://github.com/wittkensis/glintstone/wiki) |
| Add or port an ingestion connector | [ingestion/CONTRIBUTING.md](ingestion/CONTRIBUTING.md) |
| See what a source's raw records look like | [data-model/source-schemas/SAMPLES.md](data-model/source-schemas/SAMPLES.md) |
| Deploy to staging or production | [ops/deploy/DEPLOY.md](ops/deploy/DEPLOY.md) |
| Bootstrap a staging environment | [ops/deploy/STAGING.md](ops/deploy/STAGING.md) |
| Manage scheduled jobs / cron | [ops/deploy/cron/README.md](ops/deploy/cron/README.md) |
| Manage supervisord worker units | [ops/deploy/supervisor/README.md](ops/deploy/supervisor/README.md) |
| Understand the git hooks / quality gates | [ops/hooks/README.md](ops/hooks/README.md) |
| Archive & track large source snapshots | [ops/snapshots/README.md](ops/snapshots/README.md) |
| Run the ML sign-detection service | [ml/service/README.md](ml/service/README.md) |
| Set up ML model checkpoints | [ml/models/SETUP.md](ml/models/SETUP.md) · [ml/models/ebl_ocr/SETUP.md](ml/models/ebl_ocr/SETUP.md) |
| Deploy the ML service to Modal | [ml/service/deploy/MODAL_DEPLOYMENT.md](ml/service/deploy/MODAL_DEPLOYMENT.md) · [troubleshooting](ml/service/deploy/MODAL_TROUBLESHOOTING.md) |
| See non-obvious build learnings | [LEARNINGS.md](LEARNINGS.md) |

## By area

### Overview & rules
| Doc | Answers |
|---|---|
| [README.md](README.md) | What Glintstone is, quickstart, architecture in brief |
| [CLAUDE.md](CLAUDE.md) | Durable engineering rules, tech stack, skill routing |
| [LEARNINGS.md](LEARNINGS.md) | Non-obvious findings from the agentic-summarization build |

### Data model & ingestion
| Doc | Answers |
|---|---|
| [data-model/README.md](data-model/README.md) | Directory layout: schema YAMLs, mappings, migration runner |
| [data-model/source-schemas/SAMPLES.md](data-model/source-schemas/SAMPLES.md) | Most-complete sample records per source (field coverage) |
| [ingestion/CONTRIBUTING.md](ingestion/CONTRIBUTING.md) | Connector contract: lifecycle, LoadStats, dead letters |

### Operations & deployment
| Doc | Answers |
|---|---|
| [ops/deploy/DEPLOY.md](ops/deploy/DEPLOY.md) | Commit → running release on the VPS |
| [ops/deploy/STAGING.md](ops/deploy/STAGING.md) | One-time staging bootstrap runbook |
| [ops/deploy/cron/README.md](ops/deploy/cron/README.md) | Versioning & installing scheduled jobs |
| [ops/deploy/supervisor/README.md](ops/deploy/supervisor/README.md) | supervisord units as the source of truth |
| [ops/hooks/README.md](ops/hooks/README.md) | Git hooks / quality gates and how to enable them |
| [ops/snapshots/README.md](ops/snapshots/README.md) | Archiving large source files out of git |

### Machine learning
| Doc | Answers |
|---|---|
| [ml/service/README.md](ml/service/README.md) | Local FastAPI sign-detection service |
| [ml/models/SETUP.md](ml/models/SETUP.md) | Obtaining the three model repositories |
| [ml/models/ebl_ocr/SETUP.md](ml/models/ebl_ocr/SETUP.md) | eBL OCR DETR checkpoint setup |
| [ml/service/deploy/MODAL_DEPLOYMENT.md](ml/service/deploy/MODAL_DEPLOYMENT.md) | Deploying the ML service on Modal |
| [ml/service/deploy/MODAL_TROUBLESHOOTING.md](ml/service/deploy/MODAL_TROUBLESHOOTING.md) | Common Modal deployment issues |

## On the wiki (not in-tree)

Long-form narrative lives on the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki):

- **[Engineer Onboarding](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding)** — Day 1–5 ramp-up
- **[Assyriology 101](https://github.com/wittkensis/glintstone/wiki/Assyriology-101)** — 5-minute domain primer
- **Data Model** — the full narrative (per-source licenses & access, trust architecture,
  ML integration, known data-quality issues, citation pipeline, ETL guide). These pages
  used to live in-tree under `docs/data-model/`; they moved to the wiki on 2026-05-11.
- **API / MCP reference, Research, Opportunities, Project** — see the wiki sidebar.
- **[Ideas](https://github.com/wittkensis/glintstone/wiki/Ideas)** — time-bound exploration.

## Doc conventions

Every in-tree Markdown file (except repo-root `README.md` and `CLAUDE.md`) carries a YAML
header — the schema is in [`gs-curator-docs/header-schema.md`](.claude/skills/gs-curator-docs/header-schema.md).
Validate with `python3 .claude/skills/gs-curator-docs/add-headers.py --check`. The `modified:`
date drives the freshness hook, so bump it on any substantive edit.
