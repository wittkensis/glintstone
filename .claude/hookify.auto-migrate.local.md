---
event: PostToolUse
action: warn
---

# Auto-Migration Reminder

When migration files are edited, remind to apply them.

## Pattern

`data-model/migrations/.*\.sql`

## Action

After editing migration files in `data-model/migrations/`, always run:

```bash
python ops/migrate.py --apply
```

Or if using the manual migration script:

```bash
# Review migration
cat data-model/migrations/[filename].sql

# Apply to database
psql -d glintstone -f data-model/migrations/[filename].sql
```

**Important:** Never forget to apply migrations after editing schema files!
