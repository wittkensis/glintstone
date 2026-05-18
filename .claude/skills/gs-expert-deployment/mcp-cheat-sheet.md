---
question: "Which MCP tool do I reach for — Hostinger, Neon, Cloudflare, or fallback CLI?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul as a quick-reference card so a non-technical operator never has to remember which surface owns which operation."
status: active
audience: [claude, ops]
owners: [eric]
related_issues: []
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# MCP cheat sheet

## By operation

| I want to… | Reach for | If MCP unavailable |
|---|---|---|
| Check production app status | Hostinger MCP — VPS status | `ssh glintstone "sudo supervisorctl status"` |
| Tail production logs | Hostinger MCP — log tail | `ssh glintstone "sudo supervisorctl tail -f glintstone-api stderr"` |
| ~~List Neon branches~~ | — | Neon decommissioned 2026-05-12; staging is a separate VPS-local DB |
| ~~Create a Neon staging branch~~ | — | Decommissioned. Staging uses its own DB at `/var/www/glintstone-staging/shared/.env` |
| Run a migration on staging | `APP_ENV=staging ./ops/deploy/deploy.sh` | — |
| Trigger / re-run a GitHub Actions workflow | `gh workflow run`, `gh run rerun` | GitHub web UI |
| View a failed CI run | `gh run view <id> --log-failed` | GitHub web UI |
| Set / rotate a GitHub secret | `gh secret set <name>` | GitHub web UI |
| Upload to Cloudflare R2 (future) | Cloudflare MCP — R2 put | `wrangler r2 object put` |
| Check R2 bucket usage (future) | Cloudflare MCP — R2 stats | Cloudflare dashboard |
| Update DNS | Cloudflare MCP (future) | Cloudflare dashboard |

## By trigger keyword

When the user says these, this is the routing:

- **"production is slow / down"** → Hostinger MCP for app + Neon MCP for DB
- **"my migration broke prod"** → Neon MCP point-in-time restore
- **"CI is red"** → `gh run view --log-failed`
- **"upload these images"** → Cloudflare R2 (when ready), otherwise `scp` to Hostinger
- **"swap to staging"** → Neon MCP create_branch + local `.env` edit

## What each MCP provides (capability scope)

### Hostinger MCP

(When available — current status TBD with provider)

- VPS lifecycle (start/stop, status)
- Log streaming
- Service control (supervisord wrappers via `supervisorctl`)
- File transfer (scp wrapper)

### Neon MCP

- Branch management (`list_branches`, `create_branch`, `delete_branch`)
- Connection strings (`get_connection_string`)
- Point-in-time restore
- Compute settings (rare — usually leave alone)

Do NOT use Neon MCP to run arbitrary SQL — use psql or the app for that. The MCP is for branch / connection / lifecycle operations.

### Cloudflare MCP (when added)

- R2 bucket operations (put/get/list/delete objects)
- DNS record management
- Cache purge
- Worker deployment (if we ever go that route)

## Fallback discipline

If an MCP is unavailable, use the CLI equivalent (`ssh`, `gh`, `wrangler`, `psql`, web UI). Don't invent MCP tools that don't exist — the SKILL.md safety rules apply equally to MCP and CLI paths.

## Routing rules (when this skill loads)

When a user mentions an operation in the table above, immediately check whether the MCP is available (the tool will be present in the available-tools list). If yes, use it. If no, fall back to the CLI equivalent and tell the user which fallback is being used.
