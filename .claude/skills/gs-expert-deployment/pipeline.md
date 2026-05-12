---
question: "What do test.yml and deploy.yml actually do, and how do I debug a failing run?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Tracks the GitHub Actions → Hostinger flow."
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

1. Build a tarball of the working tree (excluding `_archive/`, `source-data/sources/`, `venv/`, etc.)
2. SCP to `/opt/glintstone/releases/<git-sha>/` on the Hostinger VPS
3. SSH to the VPS and:
   - `python data-model/migrate.py up` against production Neon
   - Update symlink `/opt/glintstone/current` → `releases/<git-sha>`
   - `systemctl restart glintstone-api glintstone-app`
   - `nginx -t && nginx -s reload`
4. Smoke-test `https://app.glintstone.org/healthz`
5. On failure: leave the previous symlink in place; surface the error

## Where logs live

| Surface | Logs |
|---|---|
| GitHub Actions run | `gh run view <run-id> --log` |
| Hostinger uvicorn | `/var/log/glintstone/{api,app}.log` |
| Hostinger nginx | `/var/log/nginx/{access,error}.log` |
| Migration output | captured into the Actions run; also `/var/log/glintstone/migrate.log` |

## Debugging a failed run

1. `gh run list --branch main --limit 5` — find the failed run
2. `gh run view <run-id> --log-failed` — get just the failed step
3. If migration failed: was the migration tested against a Neon branch first? (see [staging.md](staging.md))
4. If smoke test failed: SSH in (`ssh glintstone@<vps>`), `journalctl -u glintstone-api -n 100`
5. If the run never started: check GitHub Actions secrets are still set (`gh secret list`)

## Secrets the workflows need

| Secret | Used in | Purpose |
|---|---|---|
| `DATABASE_URL` | deploy.yml | Production Neon connection |
| `TEST_DATABASE_URL` | test.yml | Test-branch Neon connection |
| `SSH_PRIVATE_KEY` | deploy.yml | SSH to Hostinger |
| `SSH_HOST` | deploy.yml | VPS hostname |
| `SSH_USER` | deploy.yml | `glintstone` |

If a secret is missing or rotated, `gh secret set <name>` updates it.

## Pre-push hook (local)

`ops/hooks/pre-push.sh` runs `check-docs-freshness.sh` (warn-only). It never blocks; the deployment-safety rules in this skill's `SKILL.md` are what gate risky actions.

## When this file's content might be wrong

- Workflow files were renamed/changed → update the workflow column in the table above
- New secrets added → update the secrets table
- New step in `deploy.yml` → update the flow diagram

`gs-curator-docs` flags pushes that touch `.github/workflows/*.yml` or `ops/deploy/*.sh` without updating this file.
