# Claude Code Hooks for Glintstone

Agentic automation hooks that protect critical data, ensure pipeline integrity, and load ANE research context automatically.

## Overview

Claude Code hooks run at specific lifecycle events during Claude sessions. These hooks provide:
- **Data protection** - Prevent accidental deletion of schema/migration files
- **Pipeline integrity** - Validate import scripts before ending sessions
- **Context loading** - Auto-load ANE research context at session start
- **Migration reminders** - Prompt to apply schema changes
- **Import context** - Inject pipeline info when discussing data imports

## Installed Hooks

### PreToolUse - Protect Critical Data (Tier 1)

**Type:** Prompt-based (LLM-driven)
**When:** Before any tool executes
**Purpose:** Block dangerous operations on production data

**Protects:**
- Schema files: `*.sql`, `*.yaml` in `data-model/`
- Migration files: `data-model/migrations/`
- Source data: `source-data/sources/` (read-only)

**Actions:**
- Asks for confirmation before:
  - Deleting schema/migration files
  - Running DROP TABLE, TRUNCATE, destructive SQL
  - Writing to `source-data/sources/`

**Example:**
```
User: "Delete data-model/migrations/001_initial.sql"
Hook: "⚠️ Confirm: This operation modifies critical data files.
       Deleting migration file: 001_initial.sql"
```

---

### Stop - Verify Data Pipeline Integrity (Tier 1)

**Type:** Command (Bash script)
**When:** Before Claude session ends
**Purpose:** Ensure import pipeline didn't break

**Checks:**
- All 15 import scripts parse as valid Python
- Schema YAML validates
- No uncommitted changes in `source-data/import-tools/`

**Script:** `ops/hooks/verify-import-pipeline.sh`

**Example:**
```
→ Validating Python syntax for all import scripts...
✓ All 15 import scripts have valid Python syntax
✓ Schema YAML is valid
✓ Import pipeline integrity verified!
```

---

### SessionStart - Load ANE Research Context (Tier 2)

**Type:** Prompt-based (LLM-driven)
**When:** Session begins
**Purpose:** Preload project-specific context

**Loads:**
- Data model schema overview (`glintstone-v2-schema.yaml`)
- Import script sequence (00-15)
- Recent migrations
- Assyriology skill availability

**Output:** 3-4 sentence summary preserved in context

**Example:**
```
Glintstone v2 schema loaded with 42 tables.
15 import scripts available (00_setup_database through 15_final_enrichment).
No pending migrations.
Use the 'assyriology' skill for ANE linguistics work.
```

---

### PreCompact - Preserve Schema Context (Tier 3)

**Type:** Prompt-based (LLM-driven)
**When:** Before context compaction
**Purpose:** Ensure data model context survives compaction

**Preserves:**
- Current schema version (v2)
- Active migration files
- Import pipeline state
- Key architectural decisions

**Output:** Compact 3-5 sentence summary

---

## Hookify Rules (PostToolUse)

Hookify provides simple markdown-based hooks without JSON editing.

### Auto-Migration Reminder

**File:** `.claude/hookify.auto-migrate.local.md`
**Event:** PostToolUse
**Pattern:** `data-model/migrations/.*\.sql`

**Action:** After editing migration files, reminds to run:
```bash
python ops/migrate.py --apply
```

---

### Import Pipeline Context Injection

**File:** `.claude/hookify.import-context.local.md`
**Event:** UserPromptSubmit
**Patterns:** `\b(import|ETL|pipeline|source data)\b`

**Action:** Injects context about:
- Import script sequence (00-15)
- Data sources (CDLI, ORACC, eBL, ePSD2)
- Pipeline location

---

## Hook Lifecycle

```
Session Starts
    ↓
[SessionStart] → Load ANE context
    ↓
User works...
    ↓
[UserPromptSubmit] → Inject import context if relevant
    ↓
[PreToolUse] → Check if tool modifies critical data
    ↓
Tool executes
    ↓
[PostToolUse] → Remind about migrations if needed
    ↓
Context approaching limit?
    ↓
[PreCompact] → Preserve schema state
    ↓
Session ending...
    ↓
[Stop] → Verify pipeline integrity
    ↓
Session Ends
```

## Configuration

### Main Config: `hooks.json`

```json
{
  "hooks": {
    "PreToolUse": [...],
    "Stop": [...],
    "SessionStart": [...],
    "PreCompact": [...]
  }
}
```

### Hookify Rules

Located in project root:
- `.claude/hookify.auto-migrate.local.md`
- `.claude/hookify.import-context.local.md`

## Testing

### Test PreToolUse Protection

Try to delete a schema file (will ask for confirmation):
```
"Delete data-model/glintstone-v2-schema.yaml"
```

### Test Stop Hook

Modify an import script with syntax error:
```
echo "def broken(" >> source-data/import-tools/00_setup_database.py
```
Then try to end session - hook will catch the error.

### Test SessionStart

Start a new Claude session - should see ANE context summary loaded automatically.

### Test Migration Reminder

Edit a migration file:
```
echo "-- test" >> data-model/migrations/001_initial.sql
```
Hook will remind to run migration.

## Troubleshooting

### Hooks not running

**Issue:** Hooks don't seem to execute
**Fix:** Hooks load at session start. Restart Claude session to activate changes.

### Hook fails with timeout

**Issue:** `Hook exceeded timeout`
**Fix:** Increase timeout in hooks.json (default: 15-30s)

### Permission denied on script

**Issue:** `verify-import-pipeline.sh: Permission denied`
**Fix:** `chmod +x ops/hooks/verify-import-pipeline.sh`

### JSON syntax error

**Issue:** `Failed to parse hooks.json`
**Fix:** Validate JSON:
```bash
python3 -c "import json; json.load(open('.claude/hooks/hooks.json'))"
```

### Hook blocks legitimate operation

**Issue:** PreToolUse asks confirmation for safe operations
**Fix:** Refine prompt in hooks.json to better distinguish safe/unsafe operations

## Disabling Hooks

### Temporarily disable all hooks

Rename hooks.json:
```bash
mv .claude/hooks/hooks.json .claude/hooks/hooks.json.disabled
```

Restart session.

### Disable specific hook

Edit `.claude/hooks/hooks.json` and remove the hook entry, or comment out (JSON doesn't support comments, so remove entirely).

### Disable hookify rule

Rename the hookify file:
```bash
mv .claude/hookify.auto-migrate.local.md .claude/hookify.auto-migrate.local.md.disabled
```

## Performance

- **PreToolUse:** ~1-2 seconds (LLM evaluation)
- **Stop:** ~3-5 seconds (validates 15 Python files + YAML)
- **SessionStart:** ~2-4 seconds (reads schema + lists files)
- **PreCompact:** ~1-2 seconds (summarizes state)

Total overhead: <10 seconds per session (SessionStart + Stop).

## Advanced: Writing Custom Hooks

See Claude Code documentation for hook development:
- [Hook Development Guide](https://docs.anthropic.com/claude-code/hooks)
- [Hook Reference](https://docs.anthropic.com/claude-code/hooks/reference)

### Example: Custom PostToolUse Hook

```json
{
  "PostToolUse": [
    {
      "type": "command",
      "command": "bash ops/hooks/custom-hook.sh",
      "timeout": 10
    }
  ]
}
```

## Security Considerations

**Hooks have access to:**
- Session transcript
- File paths
- Tool inputs/outputs
- Current working directory

**Best practices:**
- Quote all bash variables in command hooks
- Validate all inputs in scripts
- Use short timeouts (10-30s)
- Test hooks before deploying to production

## Next Steps

- Monitor hook effectiveness over next few sessions
- Refine PreToolUse patterns based on false positives
- Add more hookify rules as workflows stabilize
- Consider adding pre-commit hook for testing (Phase 3)

## Files Reference

```
.claude/hooks/
  ├── hooks.json                              # Main hook configuration
  └── README.md                               # This file

ops/hooks/
  └── verify-import-pipeline.sh               # Stop hook script

.claude/
  ├── hookify.auto-migrate.local.md           # Migration reminder
  └── hookify.import-context.local.md         # Import context injection
```
