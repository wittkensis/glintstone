---
question: "Production is broken. How do I roll back, and what's the blast radius for each surface?"
created: 2026-05-11
modified: 2026-05-18
context: "Created during the 2026-05-11 overhaul. Rollback is a symlink swap on Hostinger; this file documents the safe procedure for a non-technical operator. 2026-05-18: corrected paths (/opt/ → /var/www/), replaced systemctl with supervisorctl, and rewrote DB-recovery to use the VPS pg_dump snapshots since Neon was decommissioned 2026-05-12."
status: active
audience: [claude, ops]
owners: [eric]
related_issues: ["#14"]
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Rollback procedures

## App rollback (Hostinger)

The deploy keeps the last N release directories on disk:

```
/var/www/glintstone/
├── releases/
│   ├── prod-20260518-185831-9b7d53a/   ← current
│   ├── prod-20260517-...               ← previous
│   └── prod-20260516-...               ← 2 releases back
├── shared/                              ← .env, backups, www, bin (persist across releases)
└── current → releases/prod-20260518-185831-9b7d53a
```

Run rollback from your laptop (it ssh's in):

```bash
./ops/deploy/rollback.sh <release-tag>     # e.g. prod-20260517-130412-abcd123
```

**Safe-default rule (from SKILL.md)**: never run rollback without naming the release tag. The skill must restate:

> I'm about to roll back from `<current-release>` to `<target-release>`. This swaps the `current` symlink and restarts the supervised uvicorns. Database state is NOT reverted (recovery path: `/var/www/glintstone/shared/backups/`). Confirm?

After rollback, the script handles steps 1–2; step 3 is on you:

1. `sudo supervisorctl restart glintstone-api glintstone-web` (NOT `systemctl` — there's no systemd on this host)
2. `sudo nginx -t && sudo nginx -s reload` (only if nginx configs changed)
3. Smoke-test `curl http://127.0.0.1:8001/health` and `http://127.0.0.1:8002/healthz`

## Blast radius by surface

| Surface | Reversible? | How |
|---|---|---|
| App code | Yes | `rollback.sh` — symlink swap + `supervisorctl restart`, ~10 seconds |
| Migration (additive: add column, add table) | Mostly | Roll forward with a reversing migration; rarely a true revert |
| Migration (destructive: drop column, drop table) | NO | Restore from pre-deploy `pg_dump` snapshot under `/var/www/glintstone/shared/backups/` (Neon was decommissioned 2026-05-12) |
| `.env` change on VPS | Yes | Revert the file at `/var/www/glintstone/shared/.env`, `supervisorctl restart glintstone-api glintstone-web` |
| Nginx config | Yes | Restore previous config, `sudo nginx -t && sudo nginx -s reload` |
| Cloudflare R2 deletion | Sometimes | R2 has versioning if enabled — verify before assuming recovery |
| DNS change | Slow | Wait for TTL (up to 24h) |
| Secret rotation in GitHub Actions | Yes | `gh secret set <name>` to old value |

## When the database is the problem

Production Postgres lives on the VPS (Neon decommissioned 2026-05-12). Two snapshot sources to recover from:

- **Pre-deploy snapshots** — `deploy.sh` runs `pg_dump -Fc` before every prod migration into `/var/www/glintstone/shared/backups/pre-deploy-<release-tag>.dump.gz` (last 3 retained).
- **Daily cron backups** — `/var/www/glintstone/shared/bin/pg_backup.sh` runs at 04:15 UTC into the same backups dir (separate retention).

Recovery procedure:

1. **Stop the bleeding**: roll back the app to a release that doesn't write the bad column (`rollback.sh <prev-tag>`).
2. **Identify the right snapshot**: `ssh glintstone "ls -lt /var/www/glintstone/shared/backups/"` — pick the most recent one taken *before* the bad migration.
3. **Restore into a new DB first, not production**:
   ```bash
   ssh glintstone "createdb glintstone_recovery && \
     gunzip -c /var/www/glintstone/shared/backups/<snapshot>.dump.gz | pg_restore -d glintstone_recovery"
   ```
4. **Verify** the recovery DB has correct data (spot-check the affected tables).
5. **Cut over**: either rename databases (downtime) or update `DATABASE_URL` in `/var/www/glintstone/shared/.env` to point at `glintstone_recovery`, then `supervisorctl restart glintstone-api glintstone-web`.
6. **Write a forward migration** that prevents recurrence.

If no recent snapshot exists, contact Hostinger support about VM-level disk snapshots — last-resort recovery.

## When the deploy itself failed

If `deploy.yml` failed mid-deploy:

- Symlink is still pointing at the previous release (the workflow updates the symlink LAST)
- Migrations may have run already — check `migrate.py status` against production
- If migrations ran but the new code is bad: roll back the symlink, leave the migration applied if it's additive

## What NOT to do

- ❌ `git push --force` to `main` — does not roll back the deployed code, only the git history
- ❌ Edit code on the VPS directly — gets clobbered on next deploy
- ❌ Delete the bad release directory — useful for forensics
- ❌ Manually run SQL on production to "undo" a migration — write a proper reversing migration

## After every rollback

- File a GitHub issue: what broke, how it was rolled back, what to fix forward
- Add a regression test for the broken scenario
- Update `gs-curator-artifacts/catalog.yaml` if the bug was caught by a specific record
