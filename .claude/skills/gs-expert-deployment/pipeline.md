---
question: "What do test.yml and deploy.yml actually do, and how do I debug a failing run?"
created: 2026-05-11
modified: 2026-05-18
context: "Created 2026-05-11. Updated 2026-05-12 when production Postgres moved from Neon to the VPS itself — migrations now run on the VPS, not in CI. 2026-05-18: corrected log paths and replaced journalctl references — VPS is Alpine/OpenRC/supervisord, not systemd."
status: active
audience: [claude, ops]
owners: [eric]
related_issues: ["#14", "#51"]
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# CI/CD pipeline

## Workflows

`.github/workflows/test.yml` — runs on every push and PR:

1. Checkout
2. Install Python 3.13 + cached deps
3. `ruff check .`
4. `mypy core/ ingestion/ api/`
5. `pytest tests/ -q` (hits a Neon test branch via `TEST_DATABASE_URL` secret)

`.github/workflows/deploy.yml` — runs on push to `main` after `test.yml` passes:

1. Configure the SSH deploy key from `HOSTINGER_SSH_KEY`
2. Invoke `ops/deploy/deploy.sh`, which:
   - rsyncs the working tree to `/var/www/glintstone/releases/<release-tag>/` on the VPS
   - creates a per-release `venv` and `pip install -r requirements.txt`
   - symlinks `shared/.env` into the release
   - runs `venv/bin/python data-model/migrate.py up` **on the VPS** (Postgres is on 127.0.0.1, not reachable from CI)
   - atomically swaps `/var/www/glintstone/current` → `releases/<release-tag>`
   - `sudo supervisorctl restart glintstone-{api,web}`
   - reloads nginx if marketing target included
3. On failure before the symlink swap: the previous release stays live.

## Where logs live

| Surface | Logs |
|---|---|
| GitHub Actions run | `gh run view <run-id> --log` |
| Hostinger uvicorn (prod api) | `/var/log/glintstone-api.{out,err}.log` |
| Hostinger uvicorn (prod web) | `/var/log/glintstone-web.{out,err}.log` |
| Hostinger uvicorn (staging) | `/var/log/glintstone-staging-{api,web}.{out,err}.log` |
| Hostinger crawler | `/var/log/glintstone-crawler.{out,err}.log` |
| Hostinger nginx | `/var/log/nginx/{access,error}.log` |
| Migration output | captured into the Actions run; tail on VPS via `supervisorctl tail -f <svc> stderr` for live view |

Live stream a service: `ssh glintstone "sudo supervisorctl tail -f glintstone-api stderr"` (works for any of the 5 services). Do not use `journalctl` — there is no systemd journal on this host.

## Debugging a failed run

1. `gh run list --branch main --limit 5` — find the failed run
2. `gh run view <run-id> --log-failed` — get just the failed step
3. If migration failed: was the migration tested against a Neon branch first? (see [staging.md](staging.md))
4. If smoke test failed: `ssh glintstone "sudo supervisorctl status glintstone-api && tail -n 100 /var/log/glintstone-api.err.log"`
5. If the run never started: check GitHub Actions secrets are still set (`gh secret list`)

## Secrets the workflows need

| Secret | Used in | Purpose |
|---|---|---|
| `HOSTINGER_HOST` | deploy.yml | VPS IP / hostname |
| `HOSTINGER_SSH_KEY` | deploy.yml | Private deploy key (matches `~/.ssh/authorized_keys` for `deploy`) |

Both production and staging DBs live on the VPS at `127.0.0.1:5432` and are not reachable from CI. Each environment reads its `DATABASE_URL` from its own `/var/www/glintstone{,-staging}/shared/.env` at runtime; migrations run on the VPS via the release's venv. The old `DATABASE_URL_PROD` / `DATABASE_URL_STAGING` GitHub secrets were retired with the Neon cutover (2026-05-12).

If a secret is missing or rotated, `gh secret set <name>` updates it.

## Pre-push hook (local)

`ops/hooks/pre-push.sh` runs `check-docs-freshness.sh` (warn-only). It never blocks; the deployment-safety rules in this skill's `SKILL.md` are what gate risky actions.

## When this file's content might be wrong

- Workflow files were renamed/changed → update the workflow column in the table above
- New secrets added → update the secrets table
- New step in `deploy.yml` → update the flow diagram

`gs-curator-docs` flags pushes that touch `.github/workflows/*.yml` or `ops/deploy/*.sh` without updating this file.
