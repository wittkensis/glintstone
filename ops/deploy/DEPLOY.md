---
question: "How does Glintstone get from a git commit to a running release on the VPS?"
created: 2026-05-11
modified: 2026-06-23
context: "Rewritten 2026-05-12 to reflect post-VPS-cutover reality: production Postgres lives on the VPS itself (Neon decommissioned), migrations run server-side, and the branch model is `staging` → `main` with an approval gate on production. 2026-06-23 (#219/#272): pre-deploy pg_dump now skipped on code-only deploys and parallelised (-Fd -j4) when it runs. 2026-06-23 (#275): added the long-running ingestion / DLQ-replay section — run multi-minute ops under nohup/setsid so SIGHUP on SSH disconnect can't kill them mid-stream."
status: active
audience: [engineers, ops, claude]
owners: [eric]
related_issues: ["#14", "#52", "#61", "#219", "#272", "#273", "#275"]
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
  │       └── pre-deploy-prod-*.dumpdir/      (migration deploys only; -Fd parallel; last 2 kept)
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
        │                                        ├── pending-migration check
        │                                        │     ├─ none  → SKIP pg_dump (code-only)
        │                                        │     └─ found → pg_dump -Fd -j4 snapshot
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
For destructive recovery, restore from the matching pre-deploy snapshot.

> **Restore a pre-deploy snapshot.** Since #272 the pre-deploy snapshot is a
> PostgreSQL **directory-format** dump (`pre-deploy-<tag>.dumpdir`, produced by
> `pg_dump -Fd -j4`), not a single `.dump.gz` file. Restore it with `pg_restore`
> (also parallel), **not** `psql`:
>
> ```bash
> # on the VPS, as a role that owns the tables (DATABASE_URL_MIGRATIONS)
> set -a && . /var/www/glintstone/shared/.env && set +a
> pg_restore -j4 --clean --if-exists \
>     -d "${DATABASE_URL_MIGRATIONS:-$DATABASE_URL}" \
>     /var/www/glintstone/shared/backups/pre-deploy-<tag>.dumpdir
> ```
>
> Drop `--clean --if-exists` to load into a fresh/empty database instead.
> Note: a pre-deploy snapshot is only taken on deploys that **ship a migration**
> — code-only deploys skip the dump (#219), so the relevant snapshot is the one
> from the last migration-bearing deploy. Nightly cron backups
> (`glintstone-YYYYMMDD-*.dump.gz`) remain the every-day recovery point.

### Laptop fallback deploy (when CI can't ship)

CI is the normal path. If a deploy must go out and CI is unavailable — a
GitHub Actions outage, or an `ssh-keyscan` flake that survives the in-workflow
retries — deploy from the laptop with the wrapper script:

```bash
ops/deploy/deploy-from-laptop.sh                 # api app www (default)
ops/deploy/deploy-from-laptop.sh api app         # a subset
```

The wrapper exists so the fallback is repeatable and can't drift. It:

- **Exports `DEPLOY_HOST` / `APP_ENV=production` / `SSH_KEY_PATH`** so `deploy.sh`
  skips sourcing the laptop `.env` (whose `APP_ENV=local` would otherwise
  override the inline `APP_ENV` and trip the pre-deploy snapshot gate — the
  failure that aborted a fallback on 2026-06-21).
- **Fast-forwards local `main` to `origin/main` before deploying** (you ship
  what origin has) and **re-confirms the sync after** — so the next engineer
  branches from a fresh HEAD and the fallback never leaves local `main` stale
  (issue #266). It refuses to deploy if local `main` is *ahead of* or *diverged
  from* origin (push or reconcile first; override with `SKIP_GIT_SYNC=1`).

> If you ever run the raw command by hand, remember both halves:
> `export DEPLOY_HOST=76.13.208.149 APP_ENV=production SSH_KEY_PATH=~/.ssh/glintstone_deploy`
> **and** `git fetch origin && git branch -f main origin/main` afterward. The
> wrapper does both for you.

### About the "Deploy to Hostinger hangs" symptom

Since #219/#272 most deploys **skip the pre-deploy `pg_dump` entirely**: it now
runs only when the deploy actually ships a database migration. When it does run,
it is a parallel `pg_dump -Fd -j4` of the ~22 GB prod DB — roughly **~5 min**,
down from the old ~18–20 min single-stream dump. It is **not** a hang —
`deploy.sh` prints a timestamped progress line with the dump size every ~60s. Do
not cancel a deploy that is still printing growing dump sizes. Every long remote
step (pip install, import
verify, migrations) is now wrapped in its own remote `timeout`, and the SSH
sessions use keepalive + `ConnectTimeout` + `BatchMode`, so a *genuine* stall
fails fast with a clear error instead of pinning the job. The workflow's
`timeout-minutes` is 40 to give the dump real headroom.

> **Verify breadcrumb (#219/#272).** To confirm the skip logic is behaving:
> - In the deploy log of a **code-only** deploy, look for
>   `No pending migrations (N/N applied) … SKIPPING the pre-deploy pg_dump`. The
>   `Snapshotting production DB` lines should be absent and total deploy time
>   should be ~4–5 min.
> - In the deploy log of a **migration-bearing** deploy, look for
>   `K pending migration(s) … will snapshot the DB first` followed by the
>   `Snapshotting production DB → …dumpdir (-Fd -j4)` lines, and a
>   `pre-deploy-<tag>.dumpdir` directory in `shared/backups/`.
> - If you ever see `Could not parse migrate.py status output — defaulting to
>   TAKING a backup`, the detection hit an error and **fell back to dumping** (the
>   safe default); investigate the `migrate.py status` line that printed below it.

### Hotfix prod (skip staging)

```bash
git checkout -b hotfix-something main
# … edit, commit, push, PR direct to main …
```

The production approval gate still fires. Cost: you've bypassed the staging
soak. Reserve for genuine emergencies.

### Long-running ingestion / DLQ replay

Ingestion runs, dead-letter (DLQ) replays, and bulk backfills can take many
minutes — sometimes hours (a GeoNames load or a multi-million-row DLQ replay).
If you start one in a plain SSH session and the connection drops — laptop
sleeps, Wi-Fi blips, you close the lid — the shell receives **SIGHUP** and
kills the process *and its whole pipeline* mid-stream. We learned this the hard
way (#273): a `ssh … | tail` DLQ replay got SIGHUP'd at ~70K of 4.87M rows when
the pipe stalled, and had to be re-run.

**Rule: any op expected to outlive an SSH session runs detached.** Use `nohup`
(or `setsid`) so SIGHUP can't reach it, redirect output to a log file, and tail
the log instead of holding the process open through the pipe.

#### Pattern A — `nohup … &` (the default, simplest)

```bash
# On the VPS, from the app root (/var/www/glintstone/current):
nohup python -m ingestion.cli dead-letters replay --source geonames \
  > /var/www/glintstone/shared/logs/dlq-replay-$(date +%F).log 2>&1 &
echo "started PID $!"          # note the PID so you can check on it later

# Now it's safe to disconnect. To watch progress, re-attach and tail the log:
tail -f /var/www/glintstone/shared/logs/dlq-replay-*.log

# Check it's still alive / see it finish:
ps -p <PID>                     # empty output = it exited
```

Why it works: `nohup` makes the process ignore SIGHUP, the `> … 2>&1`
redirect detaches stdout/stderr from the terminal (so a closed pipe can't stall
or kill it), and trailing `&` backgrounds it so your shell returns immediately.

#### Pattern B — `setsid` (fully detached, survives even `kill -HUP` of the shell)

```bash
setsid python -m ingestion.cli run --source geonames \
  > /var/www/glintstone/shared/logs/geonames-ingest-$(date +%F).log 2>&1 < /dev/null
# returns immediately; the process is in its own session with no controlling
# terminal, so nothing the SSH session does can signal it. tail the log as above.
```

Use **B** when you want the job in its own session (no chance of inheriting a
signal from the parent shell at all); **A** is fine for everything routine.

**Do / don't**
- **Do** redirect to a log under `shared/logs/` and `tail -f` it — never pipe a
  long run straight into `tail`/`grep` over SSH (a stalled pipe is exactly what
  bit us in #273).
- **Do** record the PID (`echo $!`) and the log path before you walk away.
- **Don't** run a multi-minute ingestion/replay in a bare foreground SSH shell.
- **Don't** assume `tmux`/`screen` is installed on the VPS — `nohup`/`setsid`
  are always present and need no session to stay attached to.

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
| Migration corrupted data | (not auto-detected) | `pg_restore -j4` from `shared/backups/pre-deploy-<tag>.dumpdir` (see Roll back) |
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
