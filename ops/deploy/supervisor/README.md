---
question: "How do new supervisord program units get onto the VPS?"
created: 2026-05-18
modified: 2026-05-18
context: "supervisord units for api/app are baked into provision.sh as one-time heredocs. New units added after the initial bring-up (e.g. the CDLI crawler) need a way to get to /etc/supervisor.d/ without re-running provision."
status: active
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Glintstone supervisord units

Holds `.ini` files that supervisord reads from `/etc/supervisor.d/`. Each one
defines a long-running program supervised with auto-restart.

| Unit | Process | Port | Notes |
|---|---|---|---|
| glintstone-api.ini | `uvicorn api.main:app` | 8001 | in `provision.sh` |
| glintstone-web.ini | `uvicorn app.main:app` | 8002 | in `provision.sh` |
| glintstone-staging-api.ini | `uvicorn api.main:app` | 8003 | in `provision-staging.sh` |
| glintstone-staging-web.ini | `uvicorn app.main:app` | 8004 | in `provision-staging.sh` |
| **glintstone-crawler.ini** | `python -m ops.scripts.cdli_image_crawler` | — | new (this dir) |

## Install a new unit on the VPS

```bash
# From the project root
scp ops/deploy/supervisor/<unit>.ini glintstone:/tmp/
ssh glintstone-root "install -m 0644 /tmp/<unit>.ini /etc/supervisor.d/<unit>.ini && supervisorctl update"
```

`supervisorctl update` reads new/changed `.ini` files and starts any
program with `autostart=true` that isn't already running. Existing programs
are unaffected unless their config changed.

## Why this folder instead of editing provision.sh

`provision.sh` runs once on bring-up. New units added later — like the
crawler — need to ship via the repo (versioned, reviewable) without
re-running the provisioner against a populated VPS. Eventually `deploy.sh`
should sync this directory on every deploy; until then, install manually
with the snippet above.
