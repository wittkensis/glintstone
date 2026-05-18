# Glintstone — durable rules

This is a **production academic application** for cuneiform / Assyriology scholars. Their careers depend on the data being accurate and properly attributed.

## Non-negotiables

- **Source attribution is structural.** Every row in every annotation table carries `annotation_run_id`. Never silently overwrite a previous annotation; always create a new run.
- **Competing interpretations are a feature, not a bug.** Two scholars disagreeing on a lemma both get stored. Don't dedupe based on agreement.
- **Two-tier rule.** The web app (`app/`) never touches the database directly — it calls the API (`api/`) over HTTP via httpx.
- **Migrations run as `wittkensis`.** Tables are owned by `wittkensis`; the app connects as `glintstone`. After creating any new table or sequence, `GRANT` permissions to `glintstone`.
- **psycopg rollback trap.** `conn.rollback()` undoes ALL uncommitted changes in the transaction. Use `ON CONFLICT` or `NOT EXISTS`, not try/except `UniqueViolation`.
- **macOS SSL workaround.** Python `urllib`/`requests` can fail on some HTTPS endpoints. Shell out to `curl` via `subprocess.run(...)`.
- **Deployment is routed through `gs-expert-deployment`.** Never push to `main` with red CI, never modify the production Neon branch directly, never use `--no-verify`.

## How to respond

- **Explain things in plain English.** Avoid jargon, acronyms, and code-level shorthand when explaining what something is, why it matters, or what to do about it. If a technical term is unavoidable, define it inline the first time. Save the precise terminology for the code itself.
- **When you've made an assumption, say what you assumed and what could go wrong.** Don't bury caveats inside short bracketed asides — spell out the situation, why it might bite, and what to do if it does.
- **Recommend a path, don't just list options.** When several approaches work, name the one Eric should try first and why. Other options come after.

## Where to look first

Open `gs-orient-project/SKILL.md` for the routing map. That skill auto-loads at session start. Other skills are triggered by keywords:

| Skill | Loads for |
|---|---|
| `gs-expert-assyriology` | Anything ATF, lemma, sign, glossary, ancient-language morphology |
| `gs-expert-data-model` | Schema, migrations, repository / query code, lexical API |
| `gs-expert-ui` | CSS, BEM, semantic HTML, accessibility, `app/static/` |
| `gs-expert-integrations` | `ingestion/`, new connectors, source-specific quirks |
| `gs-expert-deployment` | Deploy, staging, rollback, Hostinger, Neon, GitHub Actions, R2 |
| `gs-scout-integrations` | "Should we use this new HuggingFace model / dataset / API?" |
| `gs-curator-artifacts` | "Find me a test tablet / scholar / lemma / sign / search term…" |
| `gs-curator-docs` | Before any `git commit` or `git push` (freshness check) |

## Tech stack (quick)

- **Backend**: Python 3.13, FastAPI, uvicorn, psycopg 3
- **Database**: PostgreSQL 17 (Neon prod, local for dev)
- **Web**: server-rendered Jinja2 + vanilla JS + token-driven CSS
- **Ingestion**: `python -m ingestion.cli list|run|status|dead-letters`
- **Deploy**: GitHub Actions → Hostinger VPS with symlink rotation

## Doc and folder structure

```
README.md                       Public-facing project intro
CLAUDE.md                       This file
docs/                           Reference docs (onboarding, research, opportunities, personas, ideas, prototypes)
data-model/                     Schema YAMLs + migrate.py + migrations/ (NNN_*.sql)
docs/data-model/                Narrative docs about the schema + pipeline
ingestion/                      ETL framework
ops/                            Deployment, local dev, hooks
.claude/skills/gs-*/            Project-local knowledge skills
```

Time-bound exploration goes in `docs/ideas.md` (not GitHub issues until actionable).

## YAML header on every doc

Every Markdown file under the repo carries the schema defined in `gs-curator-docs/header-schema.md`. `gs-curator-docs/add-headers.py --check` validates the contract.

## A note about `_archive/`

Earlier prototypes, the v1 schema tools, the v1 ATF viewer, and the original linguistics-schema agent outputs were committed to git history on `2026-05-11` and then removed from the working tree. To inspect:

```bash
git log --diff-filter=D --name-only -- '_archive/*'
git show <hash>:_archive/<path>
```

Don't recreate `_archive/` in the working tree.

## Deeper onboarding

[`docs/engineer-onboarding.md`](docs/engineer-onboarding.md) is the Day 1–5 ramp-up. [`docs/assyriology-101.md`](docs/assyriology-101.md) is the 5-minute domain primer.
