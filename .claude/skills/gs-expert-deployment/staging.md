---
question: "How do I preview a change safely — Neon branches, DATABASE_URL swaps, local parity with production?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Neon branching is the safe-preview pattern; this file codifies the workflow so a non-technical operator can spin up and tear down branches confidently."
status: active
audience: [claude, ops, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-deployment, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Staging via Neon branches

Neon's branching is the project's preview mechanism. Every risky DB change should run against a branch first.

## Pattern

```
production branch (main)
       │
       ├── staging-branch-MIGRATION-021   (test the new migration)
       ├── staging-branch-2026-05-11      (general staging snapshot)
       └── staging-branch-rinap-reimport  (named after the operation)
```

Branches are cheap. Make one per risky operation. Delete when done.

## Operations

Via Neon MCP (preferred when available):

- **List branches**: `Neon list_branches`
- **Create branch**: `Neon create_branch --name <name> --parent main`
- **Get connection string**: `Neon get_connection_string --branch <name>`
- **Delete branch**: `Neon delete_branch --name <name>`

Via the Neon web UI: same operations under "Branches".

## Swapping DATABASE_URL

The app reads `DATABASE_URL` from `.env`. One line change, no other code touched:

```bash
# Production
DATABASE_URL=postgresql://user:pass@ep-prod.neon.tech/glintstone?sslmode=require

# Staging branch
DATABASE_URL=postgresql://user:pass@ep-staging-2026-05-11.neon.tech/glintstone?sslmode=require

# Local dev (Postgres on laptop)
DATABASE_URL=postgresql://wittkensis@127.0.0.1:5432/glintstone
```

Then `./ops/local/stop.sh && ./ops/local/start.sh` to pick up the new connection.

## Preview workflow

1. **Create a Neon branch** off `main` named for the operation.
2. **Update local `.env`** to point at the branch.
3. **Run the operation** (migration, large import, schema change, etc.).
4. **Smoke-test locally** with the branch's data.
5. **Optionally deploy a preview**: push to a feature branch, GitHub Actions runs tests against this Neon branch (set `TEST_DATABASE_URL` on the workflow run).
6. **When confident**: merge to `main`, run the same operation against the production branch.
7. **Delete the staging branch** to keep the list tidy.

## Reset-to-production for a Neon branch

If a staging branch has drifted and you want a fresh copy of prod:

- Delete the branch (`Neon delete_branch`)
- Create a new one off `main`

Don't try to "rebase" — Neon branches aren't git.

## When to ask before acting

The safe-default rule from `SKILL.md`: **never modify the production Neon branch directly**. If a user says "run this migration on prod", confirm:

> This will run against the production Neon branch. Should I create a staging branch first and verify, or do you have a specific reason to skip that?

## Local dev parity

For tightest parity with production:

- Use the same Postgres version (17)
- Same psycopg version
- Same `search_path` setting (empty — see `gs-expert-data-model/migrations.md`)
- Local user `wittkensis` owns tables; app connects as `glintstone`

Differences that don't matter: cluster-level settings (autovacuum tuning, etc.) — these are Neon-specific.
