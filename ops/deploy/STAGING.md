---
question: "How do I stand up a working staging environment for Glintstone end-to-end?"
created: 2026-05-12
modified: 2026-05-12
context: "Phase A+C of the 2026-05-12 deploy hardening shipped code + GH config but the VPS-side staging surface (directory, supervisor configs, Postgres DB, nginx vhost, DNS) still needs a one-time root SSH bootstrap. This file is the runbook."
status: active
audience: [eric, ops, claude]
owners: [eric]
related_issues: ["#52", "#61"]
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Staging bootstrap — one-time setup

You're already past Phase A (versioning) and Phase C (pipeline tightening +
GitHub config). What's left is the actual provisioning of staging on the VPS.
Three independent pieces, can be done in any order:

1. DNS — you, in Hostinger/Cloudflare DNS admin
2. VPS provisioning — you, as `root` on the VPS, runs `provision-staging.sh`
3. Nightly prod→staging restore — installed by the same script

After all three, push a commit to the `staging` branch and watch
`https://staging.glintstone.org` come up.

## 1. DNS

Add two A records at your DNS provider pointing at the VPS (see `DEPLOY_HOST` in `.env` for the current IP):

```
staging.glintstone.org       A    <DEPLOY_HOST>
staging-api.glintstone.org   A    <DEPLOY_HOST>
```

TTL: whatever the rest of glintstone.org uses (5 min is fine for now).
Wait until `dig +short staging.glintstone.org` returns the IP before continuing.

## 2. VPS provisioning

SSH in as root and run the bootstrap script. Idempotent — safe to re-run.

```bash
# DEPLOY_HOST is sourced from .env. To inline: ssh root@$(grep ^DEPLOY_HOST .env | cut -d= -f2)
ssh "root@$DEPLOY_HOST" 'apk add --no-cache bash && bash -s' < ops/deploy/provision-staging.sh
```

> Hostinger's VPS is Alpine Linux, which doesn't ship `bash` by default; the
> `apk add` prefix installs it idempotently before piping the script in. If
> you already provisioned once, `bash` is already present and `apk add` is a
> no-op.

The script:

- Creates `/var/www/glintstone-staging/{releases,shared/backups}`
- `chown deploy:deploy` so the deploy user can write into it
- Creates Postgres role + DB: `glintstone_staging` owned by `wittkensis`,
  grants SELECT/INSERT/UPDATE/DELETE to the `glintstone` app role
- Writes `/var/www/glintstone-staging/shared/.env` cloned from production with
  the staging DB URL substituted in (you'll need to confirm the password is
  right — it copies from the prod .env)
- Installs supervisor configs `glintstone-staging-{api,web}.ini` listening
  on ports 8003/8004
- Installs nginx vhost from this repo's `ops/deploy/nginx/staging.glintstone.org.conf`
- Issues a Let's Encrypt certificate for staging.glintstone.org + staging-api.glintstone.org
- Installs a cron at 05:15 UTC that restores last night's prod backup into staging

The `provision.sh` already in the repo provisioned the *production* surface
back in February — the staging-specific subset is split out here so a re-run
on production-side wouldn't disturb anything.

## 3. After the script runs

A. **Verify supervisor sees the new services** (they autostart=false; the
   first deploy will start them):

   ```bash
   ssh "deploy@$DEPLOY_HOST" 'supervisorctl status | grep glintstone'
   ```

   You should see `glintstone-staging-api` and `glintstone-staging-web` in
   `STOPPED` state until the first deploy.

B. **Trigger the first staging deploy** by pushing the `staging` branch:

   ```bash
   git push origin main:staging   # only needed once if the branch was just created remotely
   git checkout staging && git push
   ```

C. **Watch the CI run**:

   ```bash
   gh run watch
   ```

   First-time deploy is slower (~3 min) because the venv has to install
   everything from scratch.

D. **Smoke the deployed staging**:

   ```bash
   curl -sf https://staging.glintstone.org/healthz
   curl -sf https://staging-api.glintstone.org/version
   curl -sI https://staging.glintstone.org/ | grep -i x-glintstone-release
   ```

## 4. Day-to-day: promote staging → production

```bash
ops/deploy/promote.sh
```

That opens a PR `staging → main`. Merge it from the GitHub UI; the production
environment's approval gate will prompt you for one click. After the click,
the same release tarball deploys to production.

## Rollback drill

Before you trust the pipeline, run a rollback drill on staging:

```bash
# 1. Note the current release tag
curl -s https://staging.glintstone.org/version | jq .release

# 2. Roll back to the previous one
ops/deploy/rollback.sh           # lists tags
ops/deploy/rollback.sh staging-<earlier-tag>

# 3. Verify the version flipped
curl -s https://staging.glintstone.org/version | jq .release
```

Production rollback is identical — the script targets `$DEPLOY_REMOTE_DIR`
based on `APP_ENV`. To roll back production: `APP_ENV=production ops/deploy/rollback.sh <tag>`.

## Nightly prod → staging restore

The cron runs as root at 05:15 UTC (the prod backup completes at ~04:20).
Steps it performs:

1. `dropdb glintstone_staging` (with FORCE in PG17 to kick connections)
2. `createdb glintstone_staging --owner=wittkensis`
3. `pg_restore --jobs=2 --no-owner --role=wittkensis` from
   `/var/www/glintstone/shared/backups/glintstone-YYYYMMDD-*.dump.gz` (latest)
4. Re-grants on the `glintstone` app role
5. Logs to `/var/log/glintstone-staging-restore.log`

**Implications:**
- Any data you write to staging gets blown away at 05:15 UTC daily. That's
  the point — staging is for testing migrations and code against real-shape
  data, not for accumulating its own state.
- A staging deploy in flight at 05:15 could collide with the restore. The
  cron grabs a file lock at `/var/run/glintstone-staging-restore.lock` and
  `deploy.sh` will start checking for it (see issue #61 follow-ups).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `staging.glintstone.org` returns 502 | Staging supervisor service down | `sudo supervisorctl status glintstone-staging-{api,web}`; check `/var/log/glintstone-staging-*.log` |
| `staging-api.glintstone.org` SSL error | Cert never issued | `sudo certbot certonly --nginx -d staging.glintstone.org -d staging-api.glintstone.org` |
| Deploy fails at migration step | Staging `.env` `DATABASE_URL_MIGRATIONS` wrong | Edit `/var/www/glintstone-staging/shared/.env` |
| Smoke test fails immediately | Probably a code regression — staging caught it | Check `/var/log/glintstone-staging-api.err.log`; rollback auto-fired |
| Nightly restore not running | cron disabled or backup file missing | `tail /var/log/glintstone-staging-restore.log`; verify `ls /var/www/glintstone/shared/backups/` |
