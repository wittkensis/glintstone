---
question: "How do supervisord program units get onto the VPS?"
created: 2026-05-18
modified: 2026-06-25
context: "supervisord units for api/app were baked into provision.sh as one-time heredocs and manually edited on the VPS. As of #472 deploy.sh rsyncs THIS directory into /etc/supervisor.d/ on every production deploy + runs supervisorctl update, so the repo — not a manual VPS edit — is authoritative for worker counts/env. All units now live here as the source of truth."
status: active
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Glintstone supervisord units

Holds the `.ini` files supervisord reads from `/etc/supervisor.d/`. Each defines
a long-running program supervised with auto-restart. **This directory is the
source of truth**: a production `deploy.sh` run copies every `*.ini` here into
`/etc/supervisor.d/` and runs `supervisorctl update` (#472), so worker counts and
env are owned by version control, not by manual edits on the VPS.

| Unit | Process | Port | Notes |
|---|---|---|---|
| glintstone-api.ini | `uvicorn api.main:app --workers 2` | 8001 | `DB_POOL_MAX=10` (#444) |
| glintstone-web.ini | `uvicorn app.main:app --workers 2` | 8002 | `DB_POOL_MAX=10` (#444) |
| glintstone-mcp.ini | `python -m mcp.server_http` | 8005 | `autostart=false` (not built yet) |
| glintstone-crawler.ini | `python -m ops.scripts.cdli_image_crawler` | — | CDLI image backfill |
| glintstone-staging-api.ini | `uvicorn api.main:app` | 8003 | `autostart=false` |
| glintstone-staging-web.ini | `uvicorn app.main:app` | 8004 | `autostart=false` |

## Changing a unit (worker count, env, a new program)

Edit the `.ini` here and deploy. `deploy.sh` syncs the file and runs
`supervisorctl update`, which re-reads only changed configs and (re)starts the
affected program — unchanged programs are untouched.

`provision.sh` still writes the same units as one-time heredocs for a bare-box
bring-up; **keep the two in sync** (the api/web env/worker lines especially). The
deploy-time sync needs two narrow sudoers grants (`cp * /etc/supervisor.d/*` and
`supervisorctl update`), installed by `provision.sh`.

To install a unit out-of-band (before the next deploy):

```bash
scp ops/deploy/supervisor/<unit>.ini glintstone:/tmp/
ssh glintstone-root "install -m 0644 /tmp/<unit>.ini /etc/supervisor.d/<unit>.ini && supervisorctl update"
```
