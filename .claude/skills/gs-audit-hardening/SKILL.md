---
name: gs-audit-hardening
description: Hardening & optimization audit — systematic review of the server, deploy pipeline, GitHub Actions, nginx, MCP, and app performance. Produces a structured report and a single GitHub issue. Use when asked to "harden", "audit", "review the deployment", or "run the audit".
metadata:
  question: "How do I conduct a thorough, consistent hardening and optimization audit of Glintstone's server, pipeline, and app?"
  created: 2026-05-18
  modified: 2026-05-18
  context: "Created after the 2026-05-18 audit session that found critical gaps: missing DB indexes, broken docs-build path, stale supervisor configs, nginx TLS overwrite, and MCP service misconfiguration. Codifies the methodology so future audits produce comparable findings."
  status: active
  audience: [claude, ops, engineers]
  owners: [eric]
  related_issues: ["#83"]
  related_skills: [gs-expert-deployment, gs-expert-data-model, gs-expert-ui, gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: [audit, harden, hardening, "security review", "deployment review", "performance audit", "pipeline audit", "run the audit", "review everything"]
---

# Glintstone hardening & optimization audit

This skill governs how audits are scoped, conducted, and reported. Run it when asked to do a hardening pass, after a major infrastructure change, or when something feels brittle. It produces a structured report and a GitHub issue with actionable sub-items.

**Previous audit:** 2026-05-18 → [GitHub issue #83](https://github.com/wittkensis/glintstone/issues/83)

---

## When to run

- After any major infrastructure change (VPS migration, new service, major deploy refactor)
- When the codebase hasn't been audited in >90 days
- When a production incident reveals a gap in the pipeline
- On request ("harden this", "audit the deploy", "what are we missing")

---

## How to conduct the audit

### Step 1 — Load context (do not skip)

Before reading any files, load these to understand current state:

```bash
git log --oneline -10                          # recent changes
git status                                     # uncommitted drift
git diff HEAD~1 HEAD -- ops/ .github/ mcp/    # recent infra changes
```

Then read in this order:
1. `ops/deploy/deploy.sh` — the full deploy flow
2. `.github/workflows/deploy.yml` and `test.yml` — CI contract
3. `ops/deploy/nginx/*.conf` — all four nginx configs
4. `ops/deploy/provision.sh` and `provision-staging.sh` — server setup
5. `ops/deploy/rollback.sh` — rollback assumptions
6. `mcp/__init__.py`, `mcp/server_stdio.py` — MCP state
7. `CLAUDE.md` and `ops/deploy/DEPLOY.md` — durable rules and docs
8. `api/repositories/artifact_repo.py` — query patterns
9. `core/database.py` — connection pool
10. All migrations for index coverage: `grep -h "CREATE INDEX" data-model/migrations/*.sql`

### Step 2 — Work through the scope checklist

See [scope-checklist.md](scope-checklist.md) for the full per-area question list. Go through every section. Do not skip sections because they seem fine — the point is to verify.

### Step 3 — Write the report

Use the structure in [report-template.md](report-template.md). Every finding needs:
- A severity (Critical / High / Medium / Low)
- The specific file(s) and line(s) involved
- The root cause in plain English
- A concrete fix (code or config snippet when useful)

Do not include vague findings like "could be improved." Every finding must have a specific, verifiable problem and a specific, implementable fix.

### Step 4 — Cross-check against previous audit

Load GitHub issue #83 via `gh issue view 83`. For each item that was previously open:
- Is it now fixed? Mark it explicitly in the report.
- Was a fix attempted that introduced a regression? Flag that too.
- Is it still open? Carry it forward with a note on current status.

### Step 5 — Create the GitHub issue

After presenting the report to Eric and incorporating any feedback:

```bash
gh issue create \
  --title "Hardening & Optimization Audit — <YYYY-MM-DD>" \
  --label "bug,enhancement,documentation" \
  --body "$(cat report.md)"
```

Use the exact section structure from the report template. Phase labels (Phase 1, Phase 2, etc.) map to severity × effort and make triage obvious.

---

## Severity definitions

| Severity | Meaning | Examples |
|---|---|---|
| **Critical** | Broken right now or will break on next deploy | Missing DB index causing full table scans, deploy step that overwrites TLS config |
| **High** | Will cause a problem under foreseeable load or operation | Stale provision script that fails on re-provision, rollback that doesn't handle staging |
| **Medium** | Causes meaningful friction, drift, or confusion | Stale docs, wrong env vars, non-deterministic cron timing |
| **Low** | Minor quality / hygiene | Unused files, cosmetic inconsistencies, redundant deps |

---

## Phasing convention

Issues are grouped into phases by severity × effort so Eric can triage:

| Phase | Criteria |
|---|---|
| **Phase 1** | Critical or High severity, XS–S effort. Fix before next deploy. |
| **Phase 2** | Documentation and configuration drift. Medium severity, XS–S effort. |
| **Phase 3** | Pipeline quality gaps. Medium severity, M effort. |
| **Phase 4** | Performance. High impact, S–M effort. Ordered by ROI. |
| **Phase 5** | Security and infrastructure. Low–Medium risk, S–M effort. |

---

## Domain areas to audit

Full question list per area: [scope-checklist.md](scope-checklist.md)

| Area | Primary files |
|---|---|
| Deploy pipeline | `ops/deploy/deploy.sh`, `.github/workflows/deploy.yml` |
| Server provisioning | `ops/deploy/provision.sh`, `provision-staging.sh` |
| nginx | `ops/deploy/nginx/*.conf`, `ops/local/nginx.conf` |
| Rollback | `ops/deploy/rollback.sh` |
| CI/CD | `.github/workflows/test.yml`, `.github/workflows/deploy.yml` |
| MCP | `mcp/__init__.py`, `mcp/server_stdio.py`, `mcp/client.py` |
| Docs freshness | `CLAUDE.md`, `ops/deploy/DEPLOY.md`, [Engineer-Onboarding wiki](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) |
| Database indexes | `data-model/migrations/*.sql`, `api/repositories/artifact_repo.py` |
| Query performance | `api/repositories/artifact_repo.py`, `core/database.py` |
| Web layer latency | `app/routes/tablets.py`, `api/routes/artifacts.py` |
| Static assets | nginx configs + `app/static/` + deploy rsync exclusions |
| Environment config | `.env.example`, `core/config.py` |
| Git hygiene | `.gitignore`, hooks in `ops/hooks/` |

---

## Known recurring failure modes

Patterns that have appeared in past audits — check these first:

1. **Supervisor configs pointing outside `current/`** — any `command=` in supervisor `.ini` files that uses an absolute path instead of `…/current/venv/bin/…` will break on re-provision.
2. **nginx static alias not following symlink** — `alias /var/www/glintstone/app/static/` should be `alias /var/www/glintstone/current/app/static/`.
3. **Phantom services** — supervisor or nginx configs referencing a module that doesn't exist in the codebase (e.g. `mcp.server_http`).
4. **TLS overwrite** — deploy copies HTTP-only nginx configs over certbot-managed HTTPS configs.
5. **docs/build path drift** — build scripts that output to a renamed directory (the `marketing/` → `www/` incident).
6. **Stale database references in CLAUDE.md** — Neon was decommissioned 2026-05-12; any future hosted-DB migration should update CLAUDE.md immediately.
7. **Missing junction-table indexes** — `artifact_genres(p_number)` and `artifact_languages(p_number)` were missing as of the 2026-05-18 audit.
8. **Sequential HTTP calls in the web layer** — `tablet_list` makes two blocking API calls sequentially; parallelism not yet implemented.
9. **COUNT(\*) double-query pagination** — search runs a separate COUNT query; window function not yet applied.
