# Glintstone — durable rules

This is a **production academic application** for cuneiform / Assyriology scholars. Their careers depend on the data being accurate and properly attributed.

## Non-negotiables

- **Source attribution is structural.** Every row in every annotation table carries `annotation_run_id`. Never silently overwrite a previous annotation; always create a new run.
- **Competing interpretations are a feature, not a bug.** Two scholars disagreeing on a lemma both get stored. Don't dedupe based on agreement.
- **Two-tier rule.** The web app (`app/`) never touches the database directly — it calls the API (`api/`) over HTTP via httpx.
- **Migrations run as `wittkensis`.** Tables are owned by `wittkensis`; the app connects as `glintstone`. After creating any new table or sequence, `GRANT` permissions to `glintstone`.
- **psycopg rollback trap.** `conn.rollback()` undoes ALL uncommitted changes in the transaction. Use `ON CONFLICT` or `NOT EXISTS`, not try/except `UniqueViolation`.
- **macOS SSL workaround.** Python `urllib`/`requests` can fail on some HTTPS endpoints. Shell out to `curl` via `subprocess.run(...)`.
- **Deployment is routed through `gs-expert-deployment`.** Never push to `main` with red CI, never run destructive operations against the production VPS Postgres directly, never use `--no-verify`.

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
| `gs-expert-deployment` | Deploy, staging, rollback, Hostinger, VPS Postgres, GitHub Actions, R2 |
| `gs-scout-integrations` | "Should we use this new HuggingFace model / dataset / API?" |
| `gs-curator-artifacts` | "Find me a test tablet / scholar / lemma / sign / search term…" |
| `gs-curator-docs` | Before any `git commit` or `git push` (freshness check) |
| `gs-audit-hardening` | Hardening pass, audit, "review the deployment", "run the audit" |
| `gs-audit-frontend` | Frontend/design audit, "design system", "css audit", "clean up the frontend", "frontend entropy" |
| `gs-swarm` | Parallel multi-part build/feature/audit — "swarm", "fan out", "build feature", "run audit" (Glintstone-tuned: two-tier decompose, serialized deploy) |
| `gs-canary` | Blast-radius triage for a bug/change — "which tier", "api or app", "blast radius", "this smells systemic" (read-only recon) |
| `giddyup` | Backlog triage — "what's next?", "what should I work on?", "prioritize", "sequence the backlog" |

## Tech stack (quick)

- **Backend**: Python 3.13, FastAPI, uvicorn, psycopg 3
- **Database**: PostgreSQL 17 (VPS-local for prod, local for dev — Neon decommissioned 2026-05-12)
- **Web**: server-rendered Jinja2 + vanilla JS + token-driven CSS
- **Ingestion**: `python -m ingestion.cli list|run|status|dead-letters`
- **Deploy**: GitHub Actions → Hostinger VPS with symlink rotation

## Doc and folder structure

```
README.md                       Public-facing project intro
CLAUDE.md                       This file
data-model/                     Schema YAMLs + migrate.py + migrations/ (NNN_*.sql)
ingestion/                      ETL framework
ops/                            Deployment, local dev, hooks
.claude/skills/                 Project-local knowledge skills (gs-*, giddyup)
docs/                           Persona HTML pages + interactive prototypes (no markdown — see wiki)
```

Long-form narrative documentation (onboarding, data-model docs, API/MCP reference, research, opportunities, project) lives in the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki). Time-bound exploration lives on the [Ideas wiki page](https://github.com/wittkensis/glintstone/wiki/Ideas).

## YAML header on every doc

Every Markdown file **in the working tree** carries the schema defined in `gs-curator-docs/header-schema.md`. `gs-curator-docs/add-headers.py --check` validates the contract. Wiki pages do NOT carry frontmatter — GitHub Wiki renders YAML as raw text.

## A note about `_archive/`

Earlier prototypes, the v1 schema tools, the v1 ATF viewer, and the original linguistics-schema agent outputs were committed to git history on `2026-05-11` and then removed from the working tree. To inspect:

```bash
git log --diff-filter=D --name-only -- '_archive/*'
git show <hash>:_archive/<path>
```

Don't recreate `_archive/` in the working tree.

## Deeper onboarding

[Engineer Onboarding](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) (wiki) is the Day 1–5 ramp-up. [Assyriology 101](https://github.com/wittkensis/glintstone/wiki/Assyriology-101) (wiki) is the 5-minute domain primer.
