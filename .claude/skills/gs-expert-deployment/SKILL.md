---
name: gs-expert-deployment
description: Proactive infra concierge — Hostinger VPS, GitHub Actions, Neon, Cloudflare R2. Restates risky actions before executing, surfaces drift before it bites, routes to the right MCP. Use for anything deploy / staging / rollback / env-related.
metadata:
  question: "How do I safely deploy, stage, roll back, and manage Glintstone's infrastructure (Hostinger, GitHub Actions, Neon, soon Cloudflare R2)?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Created during the 2026-05-11 overhaul to absorb the infra-juggling burden from a non-technical operator. Designed to be proactive — surfaces problems before they bite, restates risky actions before executing, and routes to the right MCP server for the job."
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
| **Hostinger VPS** | Production + staging app server (nginx + uvicorn + static marketing + Postgres 17) | Hostinger MCP (when available); `ssh` fallback |
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
4. **Never delete a deployment release directory** under `/opt/glintstone/releases/` — let `deploy.sh` rotate.
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
         ├─ scp to Hostinger VPS /opt/glintstone/releases/<sha>/
         ├─ Run migrations against production Neon
         ├─ Update symlink /opt/glintstone/current → releases/<sha>
         ├─ Reload uvicorn (systemd) + nginx (reload, not restart)
         └─ Smoke-test https://app.glintstone.org
```

Rollback is a symlink swap; see [rollback.md](rollback.md).

## Open issues this skill tracks

- #7 — Server configuration & security (Hostinger, Alpine, bot protection)
- #14 — Deployment & versioning system
- #52 — Infrastructure: images, caching & security (R2 migration lives here)
