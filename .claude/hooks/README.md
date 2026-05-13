---
question: "Which Claude Code hooks does Glintstone install, and what does each do?"
created: 2026-02-21
modified: 2026-05-11
context: "Rewritten during the 2026-05-11 knowledge architecture overhaul. The previous version referenced retired v1 paths (data-model/migrations, 00-15 numbered scripts) and SessionStart context that's now handled by the gs-orient-project skill auto-loading. This version is intentionally minimal — most context-loading is delegated to skills."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-orient-project, gs-curator-docs, gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Claude Code hooks — Glintstone

Two hooks. Most context-loading and routing has moved out of hooks into the `gs-*` skills (which load on triggers rather than indiscriminately at SessionStart).

## Installed hooks

### `PreToolUse` — safety validator

Type: prompt-based (LLM-driven).

Catches risky modifications to:

- `data-model/*.yaml` (schema files)
- `data-model/migrations/*.sql` (migrations)
- `ops/deploy/`, `.github/workflows/deploy.yml` (production deploy machinery)
- Force-push to `main`

If the tool use matches, the hook asks for confirmation via `systemMessage`. The `gs-expert-deployment` skill's safe-default rules layer on top of this.

### `Stop` — pipeline integrity

Type: shell command — runs `ops/hooks/verify-import-pipeline.sh`.

Validates that the ingestion framework is still healthy: discovers connectors, parses the registry, sanity-checks imports.

## What's gone (and where it went)

- **`SessionStart` context prompt** — used to read the schema YAML and list import scripts. Replaced by the `gs-orient-project` skill, which auto-loads on Glintstone triggers and carries a current-as-of row-count snapshot.
- **`PreCompact` schema preserver** — same logic, same replacement. The `gs-orient-project` summary survives compaction.
- **`hookify.auto-migrate.local.md`** — referenced `data-model/migrations` (wrong path) and assumed v1 numbered scripts. Removed; the `gs-curator-docs` freshness contract covers the same ground.
- **`hookify.import-context.local.md`** — referenced the 15 numbered scripts. Removed; `gs-expert-integrations` is loaded on import-related keywords instead.

## How the freshness mechanism works

`gs-curator-docs` defines a contract: when staged changes touch certain paths, specific docs / skills must also be touched (warn-only). The freshness check runs on push via `ops/hooks/check-docs-freshness.sh`.

See [`gs-curator-docs/SKILL.md`](../skills/gs-curator-docs/SKILL.md) for the path-to-doc contract.

## Testing the hooks

```bash
# PreToolUse — attempt a risky operation, verify the prompt fires
echo "test" > data-model/test.yaml  # should ask for confirmation

# Stop — manually run the verifier
bash ops/hooks/verify-import-pipeline.sh
```

## Disabling

Temporarily disable all hooks:
```bash
mv .claude/hooks/hooks.json .claude/hooks/hooks.json.disabled
```
Restart the Claude session to take effect.

## Performance

- `PreToolUse`: ~1–2 s LLM evaluation per risky tool call
- `Stop`: ~3–5 s for the verifier

Total overhead: well under 10 s per session.
