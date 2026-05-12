---
question: "What every field in Glintstone's YAML doc header means, and what valid values are."
created: 2026-05-11
modified: 2026-05-11
context: "Field-by-field reference for the YAML frontmatter every Markdown doc carries. Loaded by gs-curator-docs when validating or adding headers."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-curator-docs]
supersedes: null
superseded_by: null
---

# YAML header schema

## Canonical template

```yaml
---
question: "One sentence: what question does this file answer?"
created: 2026-05-11
modified: 2026-05-11
context: "Why this file exists — the decision or conversation that produced it."
status: active
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: []
supersedes: null
superseded_by: null
---
```

For SKILL files only, add two extra fields **above the `---` close**:

```yaml
triggers: [keyword1, keyword2, "multi-word phrase"]
description: "One-sentence description Claude uses to decide when to load this skill."
```

## Field reference

### `question` (required)

A single sentence ending in `?` (or implicitly answerable). It frames the reader's intent.

Good: `"How do I add a new ingestion connector?"`
Bad: `"Connectors"` (not a question), `"This file explains how to add connectors and also covers related topics like..."` (too long)

### `created` (required)

ISO date `YYYY-MM-DD` of first commit. Never edited after the initial commit.

### `modified` (required)

ISO date `YYYY-MM-DD` of the last meaningful content change. **Update on every substantive edit.** Typo fixes don't count; reorganizing, adding sections, changing facts do.

The freshness hook compares this against the current date.

### `context` (required)

1–3 sentences. What conversation, incident, or decision produced this file. This is what survives when the author leaves — it tells future readers (and agents) whether the file is still load-bearing.

Good: `"Created during the ingestion migration to capture per-source quirks that bit us during the CDLI catalog port (lots of 302 redirects from cdli.earth)."`
Bad: `"Documentation file."`

### `status` (required)

One of:
- `active` — current canon, trust this file
- `draft` — work-in-progress, may be wrong
- `archived` — historically interesting, not authoritative
- `deprecated` — replaced; check `superseded_by`

### `audience` (required)

Array. Any subset of: `engineers`, `claude`, `scholars`, `ops`, `designers`.

If `claude` is in the list, write with progressive disclosure — short intro, then sections that can be referenced by anchor.

### `owners` (required)

Array of GitHub usernames or first names. Who to ask when this file is wrong.

### `related_issues` (optional, default `[]`)

Array of GitHub issue references as strings: `["#60", "#51"]`. These show up in the freshness check — if all linked issues are closed, the file may be ready to archive.

### `related_skills` (optional, default `[]`)

Array of skill directory names: `["gs-expert-integrations", "gs-expert-data-model"]`. Lets `gs-curator-docs` walk the dependency graph when something changes.

### `supersedes` (optional, default `null`)

Path to the doc this one replaces. Set when migrating content (e.g. from `PLAN/` to a skill).

### `superseded_by` (optional, default `null`)

Path to the doc that replaces this one. Set together with `status: deprecated`.

### `triggers` (skill-only)

Array of keywords or phrases. When the user's message contains any of them (case-insensitive), Claude should consider loading the skill.

### `description` (skill-only)

One sentence. Claude reads this from the skill listing to decide whether to load. Mirror the `question:` field, but rephrased as a capability statement.

## Validation rules

`add-headers.py --check` enforces:

1. The header is the first thing in the file (no blank lines or text before).
2. All required fields are present.
3. `created` and `modified` parse as `YYYY-MM-DD`.
4. `status` is one of the four allowed values.
5. `audience` is non-empty.
6. For files in `.claude/skills/`, `triggers` and `description` are present.

## Special cases

- **Repo-root `README.md`**: skip. GitHub renders YAML frontmatter awkwardly on the landing page.
- **Repo-root `CLAUDE.md`**: skip. Loaded verbatim by Claude every session — the header would be conversational noise.
- **README.md inside vendored source-data**: skip. Upstream-owned (e.g. `source-data/sources/eBL/metadata/ebl-api/README.md`).
- **PRIVATE-TODO.md**: user-owned, skip.
- **Generated files**: skip if the file says it's auto-generated.

## Migration story

When moving a doc:
1. Add `supersedes: <old-path>` to the new file.
2. In the old file, set `status: deprecated` and `superseded_by: <new-path>` BEFORE deleting it (so `git log` shows the link).
3. Bump `modified:` on the new file.
