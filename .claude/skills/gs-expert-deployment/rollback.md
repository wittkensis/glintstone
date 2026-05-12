---
question: "Production is broken. How do I roll back, and what's the blast radius for each surface?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Rollback is a symlink swap on Hostinger; this file documents the safe procedure for a non-technical operator."
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
/opt/glintstone/
├── releases/
│   ├── 47cf69a/   ← previous
│   ├── 9335764/   ← 2 releases back
│   └── fb0baa0/
└── current → releases/47cf69a   ← symlink, current production
```

`ops/deploy/rollback.sh` does the swap:

```bash
ssh glintstone@<vps> "cd /opt/glintstone && ./rollback.sh <git-sha>"
```

**Safe-default rule (from SKILL.md)**: never run rollback without naming the release tag. The skill must restate:

> I'm about to roll back from `<current-sha>` to `<target-sha>`. This swaps the symlink and reloads systemd. Database state is NOT reverted. Confirm?

After rollback:

1. `systemctl restart glintstone-api glintstone-app`
2. `nginx -t && nginx -s reload`
3. Smoke-test `/healthz`

## Blast radius by surface

| Surface | Reversible? | How |
|---|---|---|
| App code | Yes | `rollback.sh` — symlink swap, ~10 seconds |
| Migration (additive: add column, add table) | Mostly | Roll forward with a reversing migration; rarely a true revert |
| Migration (destructive: drop column, drop table) | NO | Restore from Neon point-in-time snapshot |
| `.env` change on VPS | Yes | Revert the file, restart services |
| Nginx config | Yes | Restore previous config, `nginx -s reload` |
| Cloudflare R2 deletion (future) | Sometimes | R2 has versioning if enabled — verify |
| DNS change | Slow | Wait for TTL (up to 24h) |
| Secret rotation in GitHub Actions | Yes | `gh secret set <name>` to old value |

## When the database is the problem

If a migration corrupted production data:

1. **Stop the bleeding**: roll back the app to a version that doesn't write the bad column.
2. **Open Neon dashboard** → Branches → Restore.
3. **Create a recovery branch** from the point-in-time snapshot before the bad migration.
4. **Verify** the recovery branch has correct data.
5. **Promote** the recovery branch to `main` (or update production `DATABASE_URL` to point at the recovery branch).
6. **Write a forward migration** that fixes the schema mistake.

Neon retains 7 days of point-in-time history on the free tier; longer on paid plans. Check the plan before assuming you have a snapshot to restore.

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
