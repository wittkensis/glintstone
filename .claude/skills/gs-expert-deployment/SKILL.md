---
name: gs-expert-deployment
description: Proactive infra concierge — Hostinger VPS, GitHub Actions, Neon, Cloudflare R2. Restates risky actions before executing, surfaces drift before it bites, routes to the right MCP. Use for anything deploy / staging / rollback / env-related.
metadata:
  question: "How do I safely deploy, stage, roll back, and manage Glintstone's infrastructure (Hostinger, GitHub Actions, Neon, soon Cloudflare R2)?"
  created: 2026-05-11
  modified: 2026-05-18
  context: "Created during the 2026-05-11 overhaul to absorb the infra-juggling burden from a non-technical operator. Designed to be proactive — surfaces problems before they bite, restates risky actions before executing, and routes to the right MCP server for the job. Process-supervision section added 2026-05-18 after a near-miss where the operator was told 'services have no reboot survival' (false — supervisord was already running them; the audit missed it by looking for systemd/OpenRC instead of asking 'who's the parent PID?')."
  status: active
  audience: [claude, ops, engineers]
  owners: [eric]
  related_issues: ["#7", "#14", "#52"]
  related_skills: [gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: [deploy, deployment, staging, production, rollback, vps, hostinger, "github actions", "GitHub Actions", neon, "Neon branch", cloudflare, "Cloudflare R2", R2, env, secret, dns, nginx, "image hosting", "CI failed", "build broke", ssh, release, ship, hooks, "pre-commit", "git hooks", "hooks.json", "pre-push", "post-merge"]
---

# Glintstone deployment & staging

The infra surface is wide and the operator is non-technical. This skill is **proactive**: it surfaces problems before they bite and never executes a risky action without restating it first.

## Surfaces

| Surface | What it is | MCP / tool |
|---|---|---|
| **Hostinger VPS** | Alpine 3.22, production + staging app server. nginx + supervisord-managed uvicorns + static marketing + Postgres 17. | Hostinger MCP (when available); `ssh glintstone` / `ssh glintstone-root` fallback |
| **GitHub Actions** | CI (test.yml) + deploy (deploy.yml) → Hostinger | `gh` CLI |
| **Cloudflare R2** | Image hosting (`glintstone-assets`, live since 2026-05-12) | Cloudflare MCP (when added) |
| **`.env`** | DATABASE_URL + secrets per env, stored under each env's `shared/` on the VPS | server-side files; no DB secrets in GitHub |
| ~~Neon~~ | Decommissioned 2026-05-12 — production moved to VPS-local Postgres | (no longer used) |

## When to load which file

| Question | File |
|---|---|
| Walk me through a release / CI failed / how does deploy.yml work? | [pipeline.md](pipeline.md) |
| Spin up a Neon branch / swap DATABASE_URL / preview a migration safely | [staging.md](staging.md) |
| Production is broken, how do I roll back? | [rollback.md](rollback.md) |
| Asset hosting today vs. the R2 migration plan | [storage.md](storage.md) |
| Which MCP tool should I reach for? | [mcp-cheat-sheet.md](mcp-cheat-sheet.md) |
| Hook scripts, hooks.json, .pre-commit-config.yaml — what does each do, how to keep them in sync? | [hooks.md](hooks.md) |

## Safe-default rules (these BLOCK — they don't just warn)

When the user asks for one of these, I MUST restate the action and wait for confirmation before executing. No exceptions.

1. **Never push to `main` without CI green** — check `gh pr checks` or `gh run list` first.
2. **Never run `ops/deploy/rollback.sh` without naming the release tag** we're rolling back to.
3. **Never modify the production Neon branch directly** — always create a branch first.
4. **Never delete a deployment release directory** under `/var/www/glintstone/releases/` — let `deploy.sh` rotate.
5. **Never commit secrets** — `.env` is gitignored; if a `.env*` file is staged, abort and surface it.
6. **Never use `--no-verify` on git push** — pre-push hooks are warnings, not annoyances.
7. **Never restart production nginx** without confirming the config validates (`nginx -t`).

When the user says **"deploy"**, my response template is:

> I'm about to deploy `<branch>` to `<target>` against `<DATABASE_URL>`. CI is `<status>`. Confirm?

Then wait.

## Proactive checks — run these without being asked

When this skill loads, opportunistically check:

1. **CI status** on the current branch (`gh run list --branch <branch> --limit 1`).
2. **Open PRs** awaiting review (`gh pr list --state open`).
3. **Stale Neon branches** older than 14 days (potential cost / drift).
4. **`.env` drift** — does the local `.env` have keys missing from `.env.example`?
5. **Image hosting overflow** — Hostinger filesystem usage trending toward limit.

Surface anything that needs attention before the user asks.

## Glintstone deployment overview

```
GitHub commit on main
  │
  ├─ .github/workflows/test.yml  (pytest, ruff, mypy)
  │      │
  │      ▼ on success
  │
  └─ .github/workflows/deploy.yml
         │
         ├─ Build release tarball
         ├─ rsync to Hostinger VPS /var/www/glintstone/releases/<tag>/
         ├─ pip install into release's per-release venv
         ├─ Symlink shared/.env into the release
         ├─ Run migrations on the VPS (Postgres at 127.0.0.1, not reachable from CI)
         ├─ Atomic symlink swap: /var/www/glintstone/current → releases/<tag>
         ├─ supervisorctl restart glintstone-{api,web}  ← supervisord, NOT systemd
         ├─ nginx reload if marketing/nginx target included
         └─ Smoke-test http://127.0.0.1:{8001,8002}/health
```

Rollback is a symlink swap; see [rollback.md](rollback.md).

## Process supervision — read this BEFORE concluding services are unmanaged

The VPS runs **Alpine Linux** (OpenRC-based, not systemd). The pattern is:

```
OpenRC default runlevel
  └─ supervisord (one OpenRC service)        ← /etc/init.d/supervisord
       ├─ glintstone-api          uvicorn :8001  ← /etc/supervisor.d/glintstone-api.ini
       ├─ glintstone-web          uvicorn :8002  ← /etc/supervisor.d/glintstone-web.ini
       ├─ glintstone-staging-api  uvicorn :8003  ← /etc/supervisor.d/glintstone-staging-api.ini
       ├─ glintstone-staging-web  uvicorn :8004  ← /etc/supervisor.d/glintstone-staging-web.ini
       └─ glintstone-crawler      python -m ops.scripts.cdli_image_crawler
                                                 ← /etc/supervisor.d/glintstone-crawler.ini
```

**Reboot survival** is already correct: OpenRC starts supervisord, supervisord starts each program with `autostart=true autorestart=true`. Do NOT create `/etc/init.d/glintstone-*` units — they'll fight supervisord for the same ports.

### When auditing process state, check in this order

1. `ssh glintstone "sudo supervisorctl status"` — authoritative list of managed programs and their PIDs
2. `ssh glintstone "ps aux | grep supervisord | grep -v grep"` — confirms supervisord itself is running
3. `ssh glintstone "rc-update show default | grep supervisor"` — confirms supervisord auto-starts on boot
4. `ssh glintstone "ls /etc/supervisor.d/"` — program unit files
5. **Only then** ask "what would happen on reboot?" — by this point the answer is in front of you

Do NOT conclude "services are unmanaged" because `/etc/init.d/glintstone-*` is empty or `systemctl` isn't installed. Both are expected on this stack.

### Adding a new supervised service

Versioned units live in `ops/deploy/supervisor/<name>.ini` in the repo. To install on the VPS:

```bash
scp ops/deploy/supervisor/<name>.ini glintstone:/tmp/
ssh glintstone-root "install -m 0644 /tmp/<name>.ini /etc/supervisor.d/<name>.ini && supervisorctl update"
```

`supervisorctl update` (not `reload`) reads new/changed `.ini` files and starts any program with `autostart=true` that isn't already running. Existing programs are not touched unless their config changed.

The api/web/staging units were baked into `provision.sh` (one-shot bring-up); the crawler and any future units ship from `ops/deploy/supervisor/` (versioned, reviewable). `deploy.sh` does not yet rsync this directory — install manually until that gap is closed.

### Reading service logs

| Program | stdout | stderr |
|---|---|---|
| glintstone-api | `/var/log/glintstone-api.out.log` | `/var/log/glintstone-api.err.log` |
| glintstone-web | `/var/log/glintstone-web.out.log` | `/var/log/glintstone-web.err.log` |
| glintstone-staging-api | `/var/log/glintstone-staging-api.out.log` | `/var/log/glintstone-staging-api.err.log` |
| glintstone-staging-web | `/var/log/glintstone-staging-web.out.log` | `/var/log/glintstone-staging-web.err.log` |
| glintstone-crawler | `/var/log/glintstone-crawler.out.log` | `/var/log/glintstone-crawler.err.log` |

Or use `supervisorctl tail -f glintstone-<name> stderr` for live streaming. Never `journalctl` — there's no systemd journal on this host.

### What `deploy` can do without sudo password

Sudoers grants `deploy`:

- `/usr/bin/supervisorctl restart glintstone-*`
- `/usr/bin/supervisorctl status glintstone-*`
- `/sbin/rc-service nginx reload`
- `/usr/sbin/nginx -t` and `nginx -s reload`

For anything else (writing to `/etc/supervisor.d/`, `rc-update`, package installs), `ssh glintstone-root` is the right tool.

## Open issues this skill tracks

- #7 — Server configuration & security (Hostinger, Alpine, bot protection)
- #14 — Deployment & versioning system
- #52 — Infrastructure: images, caching & security (R2 migration lives here)
