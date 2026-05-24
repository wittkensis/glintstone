---
question: "How are scheduled jobs (cron entries) versioned and installed on the VPS?"
created: 2026-05-18
modified: 2026-05-18
context: "Cron entries on the VPS were previously edited in-place with `crontab -e` and not tracked in the repo. This folder is the source of truth for any scheduled job the deploy user runs; install snippet below."
status: active
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Glintstone cron entries

Each `*.cron` file in this directory is a versioned fragment of the `deploy`
user's crontab. The fragments are tracked here so the schedule survives
reviews, rollbacks, and a fresh VPS provision.

| File | Schedule | Purpose |
|---|---|---|
| `glintstone-backfill.cron` | Sun 03:00 UTC | Backfill artifact images the main crawler missed; 60-min budget; shares CDLI lock |
| `glintstone-embeddings.cron` | Daily 02:00 UTC | Voyage embedding backfill for all entity types; skips unchanged rows via source_hash; after initial run (~hours) subsequent runs are seconds unless ingestion ran |

## Install a fragment on the VPS

The Alpine VPS uses standard user-crontab (`crontab -e`). To append a fragment
idempotently:

```bash
# From the project root
scp ops/deploy/cron/glintstone-backfill.cron glintstone:/tmp/

# As the deploy user, append the fragment only if its first non-comment line
# is not already present (idempotent re-runs).
ssh glintstone '
    line=$(grep -v "^#\|^$" /tmp/glintstone-backfill.cron | head -1)
    if crontab -l 2>/dev/null | grep -Fq "$line"; then
        echo "Already installed."
    else
        ( crontab -l 2>/dev/null; cat /tmp/glintstone-backfill.cron ) | crontab -
        echo "Installed."
    fi
'

# Log files need deploy ownership the first time
ssh glintstone-root '
    touch /var/log/glintstone-backfill.out.log /var/log/glintstone-backfill.err.log
    chown deploy:deploy /var/log/glintstone-backfill.{out,err}.log
'
```

## Verify

```bash
ssh glintstone "crontab -l | grep glintstone-backfill || echo NOT INSTALLED"
```

## Removing an entry

Open `crontab -e` as `deploy` on the VPS and delete the matching lines. There
is no automated `uninstall` snippet — schedule removals are rare enough that
a manual edit is the safer interface.

## Why not /etc/periodic/?

Alpine's `run-parts`-based `/etc/periodic/{daily,weekly,monthly}/` is
attractive but runs scripts as **root** at fixed times that aren't easy to
override. The deploy user's crontab gives us per-job control over time, env,
and run-as identity (the script needs to write to the prod R2 bucket using
the same `.env` the crawler reads, which lives in `deploy`'s context).
