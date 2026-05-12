---
question: "How do I preview a change safely against staging, and how does the staging↔production promotion work?"
created: 2026-05-11
modified: 2026-05-12
context: "Rewritten 2026-05-12 after Neon decommissioning. Staging is now a separate Postgres database on the same VPS, populated by a nightly restore from the production backup. Preview workflow is branch-based, not Neon-branch-based."
status: active
audience: [claude, ops, engineers]
owners: [eric]
related_issues: ["#52", "#61"]
related_skills: [gs-expert-deployment, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Staging (post-Neon)

Staging is a **second deployment surface on the same VPS**: separate
`/var/www/glintstone-staging/`, separate supervisor services, separate Postgres
database `glintstone_staging`, separate subdomains. It mirrors production's
data via a nightly `pg_restore` from the latest prod backup.

## What changed (was: Neon branches)

| Before (≤2026-05-11) | Now (≥2026-05-12) |
|---|---|
| Staging = a Neon branch of the prod DB | Staging = `glintstone_staging` Postgres DB on the VPS |
| Spin up per-operation via `Neon create_branch` | Always-on; refreshes nightly |
| `DATABASE_URL_STAGING` GitHub secret swapped per-test | No GitHub DB secret — staging reads its own `.env` on the VPS |
| One-off ad-hoc staging | Stable subdomain `staging.glintstone.org` |

Treat any older docs that reference "Neon staging branch" or
`DATABASE_URL_STAGING` as obsolete.

## Promotion model

```
feature branch  →  staging branch  →  main
                   ↓ auto-deploy     ↓ approval-gated deploy
                staging.glintstone   app.glintstone
                staging-api.glintst  api.glintstone
```

A change is "ready to promote" when:

1. It's merged into `staging` and the `deploy.yml` run on that branch is green
2. You've poked the change on `https://staging.glintstone.org` (and/or its API)
3. `curl https://staging.glintstone.org/version` returns the expected release

Then `ops/deploy/promote.sh` opens a `staging → main` PR. Merging it triggers
production deploy with the approval-gate prompt.

## When staging diverges from production

Staging gets **rewritten nightly from the latest production backup**, so:

- Don't manually edit staging data and expect it to persist past 05:15 UTC
- A migration applied to staging will be re-applied to staging the next night
  on top of the freshly-restored production schema; if you run the migration
  on production first, you'll see staging skip it on the next deploy
  (already-applied per `_migrations`)
- If you need a "frozen" staging snapshot for longer testing, manually
  `pg_dump glintstone_staging` and restore it under a different name; don't
  fight the cron

## Risky migrations — preview pattern

Before merging a migration to `main`:

1. Open PR to `staging` branch
2. Deploy fires; `migrate.py up` runs on `glintstone_staging`
3. Exercise the affected pages on `https://staging.glintstone.org`
4. If migration is reversible-via-restore (the usual case), confirm the
   `pre-deploy-*.dump.gz` snapshot is created on prod-side anyway (only
   prod deploys snapshot; staging skips it since the nightly restore is the
   recovery path)
5. Promote to main

## Hard rules (these BLOCK, not warn)

1. **Never run migrations directly against `glintstone` production from your
   laptop.** Use the deploy pipeline. The exception is read-only diagnostics
   (`psql -c 'SELECT …'`).
2. **Never apply destructive migrations** (`DROP TABLE`, `DROP COLUMN`)
   without first restoring the most recent `pre-deploy-*.dump.gz` to a
   scratch DB and verifying rollback works there.
3. **Never delete `pre-deploy-*.dump.gz` for a release that's still the
   current symlink** — that's the rollback escape hatch.

## Diagnostics

```bash
# Compare what's deployed where
curl -s https://staging.glintstone.org/version | jq
curl -s https://app.glintstone.org/version | jq

# Both should have a `schema_version` field; if they diverge, a migration is
# pending on production.
```
