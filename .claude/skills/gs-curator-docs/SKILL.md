---
name: gs-curator-docs
description: Owns Glintstone's YAML doc-header schema and the freshness contract. Use when committing, pushing, or whenever staged changes touch paths that have a corresponding skill/doc.
metadata:
  question: "How do I keep Glintstone's documentation honest and in sync with the code?"
  created: 2026-05-11
  modified: 2026-05-18
  context: "Created during the knowledge architecture overhaul to define the YAML header schema and the doc-freshness contract that every other skill and doc relies on."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: []
  related_skills: [gs-orient-project, gs-expert-integrations, gs-expert-data-model, gs-expert-ui, gs-expert-deployment, gs-curator-artifacts]
  supersedes: null
  superseded_by: null
  triggers: [commit, push, docs, documentation, freshness, header, YAML frontmatter, stale, "as-of"]
---

# gs-curator-docs

This skill is the source of truth for two things:

1. **The YAML header** that every Markdown doc in Glintstone carries.
2. **The freshness contract**: which code paths require which docs to be touched in the same commit.

It runs whenever Claude is about to commit or push, and whenever staged changes touch a path listed in the contract below.

## YAML header (canonical schema)

Every Markdown file **in the working tree** (skills, `data-model/`, `ops/`, READMEs, `CLAUDE.md`) starts with this block. Full schema in [header-schema.md](header-schema.md).

> **Wiki pages do NOT carry frontmatter.** Long-form documentation moved to the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki) on 2026-05-18; GitHub Wiki renders YAML frontmatter as raw text, so it must not be present. See "Editing the wiki" below.

```yaml
---
question: "One sentence: what question does this file answer?"
created: YYYY-MM-DD
modified: YYYY-MM-DD
context: "Why this file exists — the decision or conversation that produced it."
status: active           # active | draft | archived | deprecated
audience: [engineers]    # any subset of: engineers, claude, scholars, ops, designers
owners: [eric]
related_issues: []       # GitHub issue numbers as strings like "#60"
related_skills: []       # skill names this file feeds or is fed by
supersedes: null         # path to previous doc, or null
superseded_by: null      # path to replacement doc, or null
---
```

For SKILL files, also include `triggers: [...]` and `description: ...` (Claude reads these to decide when to load the skill).

## Freshness contract

When staged changes include any of these paths, the matching doc must also be touched in the same commit range, OR the pre-push hook prints a warning.

| Code path | Doc that must update |
|---|---|
| `ingestion/connectors/*.py` | `.claude/skills/gs-expert-integrations/framework.md` (port table) |
| `ingestion/base.py` | `.claude/skills/gs-expert-integrations/SKILL.md` |
| `source-data/migrations/*.sql` | `.claude/skills/gs-expert-data-model/migrations.md` + `data-model/glintstone-schema.yaml` |
| `app/static/css/core/tokens.css` | `.claude/skills/gs-expert-ui/css-tokens.md` |
| `README.md` row-count tables | `.claude/skills/gs-orient-project/SKILL.md` row counts |
| any migration adding new tables | `.claude/skills/gs-curator-artifacts/catalog.yaml` (scenarios that need fixtures) |
| `.github/workflows/*.yml`, `ops/deploy/*.sh` | `.claude/skills/gs-expert-deployment/pipeline.md` |
| `ops/deploy/supervisor/*.ini`, `ops/deploy/provision*.sh` | `.claude/skills/gs-expert-deployment/SKILL.md` — process-supervision section (services list, log paths, sudoers entries) |
| `ops/deploy/cron/*.cron` | `.claude/skills/gs-expert-deployment/SKILL.md` — scheduled-jobs table |
| new HuggingFace/dataset/model reference | `.claude/skills/gs-scout-integrations/worked-examples.md` |

The hook is **warn-only**. It never blocks a push. Deployment-safety checks (e.g. red CI) DO block, but those live in `gs-expert-deployment`.

### Wiki freshness (narrative docs)

The long-form narrative docs live in the [GitHub Wiki](https://github.com/wittkensis/glintstone/wiki) and are NOT enforced by the in-tree pre-push hook (wiki is a separate git repo). Instead:

- When a commit touches a code surface documented on the wiki, **add a one-line note in the commit body** naming the wiki page that may need an update. Example: `Wiki follow-up: Reference-API-Artifacts may need refresh.`
- Code surface → wiki page map:
  | Code path | Wiki page |
  |---|---|
  | `api/routes/artifacts*.py`, `api/schemas/artifact*.py` | [Reference-API-Artifacts](https://github.com/wittkensis/glintstone/wiki/Reference-API-Artifacts) |
  | `api/routes/search*.py`, `gs_mcp/`, `core/agent/` | [Reference-API-Search-Agentic](https://github.com/wittkensis/glintstone/wiki/Reference-API-Search-Agentic), [Reference-MCP](https://github.com/wittkensis/glintstone/wiki/Reference-MCP) |
  | `api/routes/dictionary*.py`, `core/lexical.py` | [Reference-API-Dictionary](https://github.com/wittkensis/glintstone/wiki/Reference-API-Dictionary) |
  | `api/routes/collections*.py` | [Reference-API-Collections](https://github.com/wittkensis/glintstone/wiki/Reference-API-Collections) |
  | `api/routes/composites*.py` | [Reference-API-Composites](https://github.com/wittkensis/glintstone/wiki/Reference-API-Composites) |
  | `data-model/glintstone-schema.yaml` (layer changes) | [Reference-Data-Model](https://github.com/wittkensis/glintstone/wiki/Reference-Data-Model) and the per-layer pages |
  | `ingestion/connectors/*.py` (new source) | [Data-Model-Data-Sources](https://github.com/wittkensis/glintstone/wiki/Data-Model-Data-Sources) |
  | ingestion pipeline structural changes | [Data-Model-Import-Pipeline-Guide](https://github.com/wittkensis/glintstone/wiki/Data-Model-Import-Pipeline-Guide) |
  | `gs_mcp/server_stdio.py`, MCP tool signatures | corresponding [Reference-MCP-*](https://github.com/wittkensis/glintstone/wiki/Reference-MCP) page |

Leaving the note in the commit body lets the user batch wiki updates without blocking deploys.

## Editing the wiki

The GitHub Wiki is a separate git repository (`https://github.com/wittkensis/glintstone.wiki.git`). To edit:

```bash
git clone https://github.com/wittkensis/glintstone.wiki.git /tmp/glintstone-wiki
cd /tmp/glintstone-wiki
# edit Foo-Page.md
git add -A && git commit -m "update Foo-Page" && git push origin master
```

Rules of the road:

- **No YAML frontmatter.** Wiki pages must start with a markdown `# Heading`.
- **Page names are flat with hyphens.** `Reference-API-Artifacts.md` not `reference/api/artifacts.md`.
- **Cross-links are bare page names.** Use `[Artifacts](Reference-API-Artifacts)` — no `.md`, no `/wiki/` prefix.
- **Default branch is `master`** (not `main`).
- `Home.md`, `_Sidebar.md`, `_Footer.md` are special — they render on every wiki page. Keep the sidebar in sync when you add a new page.

## Staleness rule

Any doc whose `modified:` stamp is older than **60 days** AND that lives in one of these categories surfaces in the freshness check:

- Skill files in `.claude/skills/`
- Anything in `data-model/`
- `README.md`, `CLAUDE.md`

(Wiki pages are not in scope for the in-tree staleness check. Treat the wiki as living documentation that contributors update opportunistically; the research-report pages there are explicitly point-in-time and don't need refreshing.)

When you see a stale stamp, either:
1. Re-confirm the content is still accurate, bump `modified:`, commit.
2. Move it to `status: archived` and link `superseded_by:`.

## When this skill runs

1. Before any `git commit` or `git push` (proactive).
2. When the user says "commit", "push", "ship", "PR", "release", "deploy".
3. When staged changes include any path in the contract.
4. When Claude adds a new Markdown file (verify the header is present and correct).

## What to do

1. Run `git diff --name-only --cached` (staged) or `--diff HEAD~1` to see touched paths.
2. For each touched path, check the contract above. If a matching doc was not also touched, propose the diff.
3. For every Markdown file being added or edited, confirm the YAML header is present and `modified:` is today's date.
4. If the user is pushing, run [check-docs-freshness.sh](../../../ops/hooks/check-docs-freshness.sh) and surface its warnings.

## Tools

- [header-schema.md](header-schema.md) — full schema reference with field-by-field guidance
- [add-headers.py](add-headers.py) — idempotent retro-fit script. `--check` mode lists files missing headers; default mode adds a stub header that the author fills in
- [`ops/hooks/check-docs-freshness.sh`](../../../ops/hooks/check-docs-freshness.sh) — the pre-push hook
