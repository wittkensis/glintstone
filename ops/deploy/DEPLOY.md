---
question: "How does Glintstone get from a git commit to a running release on the VPS?"
created: 2026-05-11
modified: 2026-05-12
context: "Rewritten 2026-05-12 to reflect post-VPS-cutover reality: production Postgres lives on the VPS itself (Neon decommissioned), migrations run server-side, and the branch model is `staging` → `main` with an approval gate on production."
status: active
audience: [engineers, ops, claude]
owners: [eric]
related_issues: ["#14", "#52", "#61"]
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Glintstone deploy

## Mental model

> Push to `staging` branch → auto-deploys to **staging.glintstone.org**. Merge
> `staging` → `main` → waits for your approval click → auto-deploys to
> **app.glintstone.org**.

Both environments stay live independently. Same code, same versioning scheme,
different `/var/www/` directory and different supervisor services.

## Layout on the VPS

```
/var/www/glintstone/                  ← production
  ├── current → releases/prod-…       (atomic symlink)
  ├── shared/
  │   ├── .env                        (runtime secrets)
  │   └── backups/
  │       ├── glintstone-YYYYMMDD-*.dump.gz   (nightly cron @ 04:15 UTC)
  │       └── pre-deploy-prod-*.dump.gz       (every prod deploy; last 3 kept)
  └── releases/
      ├── prod-20260512-165148-7a7b585/       ← newest, KEEP_RELEASES=5
      └── …

/var/www/glintstone-staging/          ← staging (mirrors layout)
  ├── current → releases/staging-…
  ├── shared/.env
  └── releases/staging-…
```

## Versioning

One scheme, every component:

| Component | Carries the release tag |
|---|---|
| Release directory | `releases/<env>-<UTC>-<short-sha>/` |
| Each release writes | `version.txt` at the release root |
| API | `version=` in OpenAPI, `GET /version`, `X-Glintstone-Release` header |
| Web app | `GET /version`, `GET /healthz`, footer build chip, asset cache-bust, `X-Glintstone-Release` header |
| Marketing | Static — same release tag, ships in same tarball |
| DB schema | `public._migrations` table tracks applied versions (NNN_*.sql) |

Inspect the live release from anywhere:

```bash
curl -s https://app.glintstone.org/version           # web app
curl -s https://api.glintstone.org/version           # API + schema_version
curl -sI https://app.glintstone.org/ | grep -i x-glintstone-release
```

## CI/CD flow

```
git push origin staging                  git push origin main
        │                                        │
        ▼                                        ▼
 .github/workflows/deploy.yml         .github/workflows/deploy.yml
        │                                        │
        ├── test.yml  (pytest, ruff, mypy)       │  (same)
        │                                        │
        ▼                                        ▼
   environment: staging               environment: production
   no protection                      required reviewer: @wittkensis
        │                                        │
        ▼                                        ▼  (after approval click)
   ops/deploy/deploy.sh                  ops/deploy/deploy.sh
   APP_ENV=staging                       APP_ENV=production
        │                                        │
        ├── rsync release/                       ├── rsync release/
        ├── venv + pip install                   ├── venv + pip install
        ├── venv import check                    ├── venv import check
        │                                        ├── pg_dump → pre-deploy snapshot
        ├── migrate.py up (staging DB)           ├── migrate.py up (prod DB)
        ├── write version.txt                    ├── write version.txt
        ├── record PREV_RELEASE                  ├── record PREV_RELEASE
        ├── atomic symlink swap                  ├── atomic symlink swap
        ├── supervisorctl restart                ├── supervisorctl restart
        │       glintstone-staging-{api,web}     │       glintstone-{api,web}
        ├── smoke test (curl /health + /healthz) ├── smoke test (curl /health + /healthz)
        │   ON FAIL → auto-rollback symlink      │   ON FAIL → auto-rollback symlink
        └── trim to KEEP_RELEASES=5              └── trim to KEEP_RELEASES=5
```

## Hands-on workflows

### Ship a change

```bash
# 1) feature branch
git checkout -b my-feature
# … edit, commit …

# 2) merge to staging (PR is fine, direct push is fine for solo dev)
git checkout staging && git merge --ff-only my-feature && git push

# 3) watch staging deploy
gh run watch
# verify on https://staging.glintstone.org

# 4) promote — opens PR staging → main, the approval gate handles the rest
ops/deploy/promote.sh
```

Or do step 4 manually: `gh pr create --base main --head staging` then merge.

### Roll back

```bash
ops/deploy/rollback.sh                                  # list available releases
ops/deploy/rollback.sh prod-20260512-130149-dc1ea08     # roll back to that tag
```

Rollback swaps **code only**. The database schema is forward. Migrations must
be additive — never destructive — so old code can talk to a newer schema.
For destructive recovery, restore from the matching `pre-deploy-*.dump.gz`.

### Hotfix prod (skip staging)

```bash
git checkout -b hotfix-something main
# … edit, commit, push, PR direct to main …
```

The production approval gate still fires. Cost: you've bypassed the staging
soak. Reserve for genuine emergencies.

## Required GitHub configuration

| Secret | Used by | Value |
|---|---|---|
| `HOSTINGER_HOST` | deploy.yml | VPS IP (mirrors `DEPLOY_HOST` in `.env`) |
| `HOSTINGER_SSH_KEY` | deploy.yml | Private deploy key |

Old `DATABASE_URL_PROD` / `DATABASE_URL_STAGING` are unused — production reads
its URL from `/var/www/glintstone/shared/.env` at runtime; staging from
`/var/www/glintstone-staging/shared/.env`.

| Environment | Branch policy | Protection |
|---|---|---|
| `production` | `main` only | Required reviewer (@wittkensis) |
| `staging` | `staging` only | None |

## Failure modes & how the pipeline handles them

| What goes wrong | Caught by | Recovery |
|---|---|---|
| Import error / syntax bug in new code | venv import check (pre-swap) | Deploy aborts before symlink swap; previous release stays live |
| Failed migration | `migrate.py up` non-zero exit | Deploy aborts pre-swap; pre-deploy snapshot is on disk |
| New code runtime error after restart | Smoke test (curl /health, /healthz) | Auto-rollback to `PREV_RELEASE` |
| Migration corrupted data | (not auto-detected) | Restore from `shared/backups/pre-deploy-<tag>.dump.gz` |
| Concurrent staging + prod deploy | GH Actions `concurrency: deploy-${{ github.ref }}` | Different refs, different VPS directories — they don't race |
| Disk fills | `KEEP_RELEASES=5` + snapshot cap (3) | Trim is automatic; older nightly backups need a manual prune |
| SSH key rotated | First deploy fails at `ssh-keyscan` / auth | `gh secret set HOSTINGER_SSH_KEY` |
| VPS unreachable | `ssh-keyscan -T 8` non-zero | Deploy fails fast with the exact error (no `2>/dev/null` swallow) |

## One-time VPS prerequisites

If staging hasn't been provisioned (gap as of 2026-05-12), root SSH is needed
once to: create `/var/www/glintstone-staging/`, install supervisor configs
(`/etc/supervisor.d/glintstone-staging-{api,web}.ini`), install nginx vhost
(`/etc/nginx/http.d/staging.glintstone.org.conf`), create the
`glintstone_staging` Postgres database, drop `/var/www/glintstone-staging/shared/.env`.
Also a DNS A record for `staging.glintstone.org` and `staging-api.glintstone.org`
→ the VPS IP (see `DEPLOY_HOST` in `.env`). See [STAGING.md](STAGING.md) for the bootstrap script.

## When this file is wrong

- `deploy.sh` flow changed → update the CI/CD flow diagram
- New secret or environment → update the GH config table
- New failure mode that should be auto-handled → add a row to the failure modes table

`gs-curator-docs` flags pushes that touch `ops/deploy/*` or `.github/workflows/*`
without updating this file.
