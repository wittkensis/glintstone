---
question: "What is the current health of the server, deploy pipeline, and app as of 2026-06-07?"
created: 2026-06-07
modified: 2026-06-07
context: "Audit conducted after PRD-017 UI overhaul (7-worker swarm, 15+ template/CSS files), AI feature assessment (PRD-018/019/020 written), and Neon→VPS Postgres migration. Previous audit: 2026-05-18 (issue #83)."
status: active
audience: [eric, engineers]
owners: [eric]
related_issues: ["#83"]
related_skills: [gs-audit-hardening, gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Hardening & Optimization Audit — 2026-06-07

**Scope:** Server, deploy pipeline, CI/CD, nginx, security headers, connection pool, AI endpoint timeouts, cron jobs, supervisor configs, index coverage, known performance gaps.

**Previous audit:** 2026-05-18 → [GitHub issue #83](https://github.com/wittkensis/glintstone/issues/83)

---

## Previous audit cross-check (issue #83)

| Item | Status |
|------|--------|
| 1a — `artifact_genres(p_number)` + `artifact_languages(p_number)` indexes | ✅ Fixed (`idx_ag_p_number`, `idx_al_p_number` in migrations) |
| 1b — `nginx -t` validation before reload | ✅ Fixed (`deploy.sh:296` validates first) |
| 1c — nginx static alias follows `current/` symlink | ✅ Fixed (`/var/www/glintstone/current/app/static/`) |
| 2a–2d — Supervisor paths, phantom MCP service, stale Neon references | ✅ Fixed |
| 3a–3b — CI pipeline: ssh-keyscan error, no `2>/dev/null` swallow | ✅ Fixed |
| 4g — Pool size upgraded to 15 via `DB_POOL_MAX` env | ✅ Fixed (`core/database.py:52`) |
| 5b — Staging nginx installs on `deploy_api` OR `deploy_app` | ✅ Fixed (`deploy.sh:261`) |
| 5c — Auto-rollback restarts MCP | ✅ Fixed (`deploy.sh:335`) |
| 5a — VPS IP hardcoded in committed files | ⚠️ Partially fixed — `DEPLOY.md`/`STAGING.md` cleaned up, but `cron-ingest.yml` still hardcodes the IP (see Finding 1a below) |

All Phase 1 items from the prior audit are resolved. One Phase 5 item regressed / was never fully addressed.

---

## Phase 1 — Fix Before Beta Invite (Critical / XS–S effort)

### 1a — VPS IP hardcoded in `cron-ingest.yml` + wrong secret name (Critical)

**Files:** `.github/workflows/cron-ingest.yml`, lines 41, 47, 62, 68, 83, 86

`cron-ingest.yml` hardcodes `76.13.208.149` on six lines instead of referencing `secrets.HOSTINGER_HOST`. Worse: it uses `secrets.DEPLOY_SSH_KEY` for the SSH key, while `deploy.yml` uses `secrets.HOSTINGER_SSH_KEY`. These are almost certainly the same physical key but registered under different names.

**Concrete impact:** If `DEPLOY_SSH_KEY` is not set as a GitHub secret (separate from `HOSTINGER_SSH_KEY`), every scheduled ingest run — weekly ORACC, monthly CDLI — silently fails. Data drift accumulates for weeks with no CI notification.

**Verify first:**
```bash
gh secret list --repo wittkensis/glintstone
```

**Fix:**
```yaml
# cron-ingest.yml — add env blocks to all three jobs (oracc, cdli, manual):
env:
  DEPLOY_SSH_KEY: ${{ secrets.HOSTINGER_SSH_KEY }}  # same secret as deploy.yml
  DEPLOY_HOST: ${{ secrets.HOSTINGER_HOST }}         # stop hardcoding 76.13.208.149

# Replace hardcoded IP references:
ssh-keyscan -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts
ssh deploy@"$DEPLOY_HOST" "cd /var/www/glintstone/current && ..."
```

---

### 1b — `HttpxTransport` 10s timeout will time out AI endpoints from server-side routes (High)

**File:** `app/transports.py:29–30`

```python
def __init__(self, base_url: str, timeout: float = 10.0) -> None:
    self._client = httpx.Client(base_url=base_url, timeout=timeout)
```

The 10-second default is fine for most routes. But the AI summary endpoint (`GET /artifacts/{p}/summary`) calls Claude — on a cold cache, synthesis takes 10–30 seconds. Any future server-side route that pre-fetches a summary (e.g., for OpenGraph tags) will time out and surface a 500.

The current AI summary is fetched client-side (browser JS → API directly), so immediate impact is low. But the `tablet_list` route makes sequential httpx calls on this 10s timeout with no retry — and any AI endpoint added to server-side rendering inherits the problem.

**Fix:** Expose a per-route timeout override or use `httpx.Timeout` with split connect/read values:
```python
httpx.Client(base_url=base_url, timeout=httpx.Timeout(connect=5.0, read=60.0))
```

---

## Phase 2 — Configuration & Documentation Drift (Medium / XS effort)

### 2a — `glintstone-crawler.ini` not installed by `provision.sh` (Medium)

**Files:** `ops/deploy/supervisor/glintstone-crawler.ini`, `ops/deploy/provision.sh`

`provision.sh` installs supervisor configs for `glintstone-api`, `glintstone-web`, `glintstone-mcp`, and both staging services. It does not install `glintstone-crawler.ini`. After a VPS reprovision, the image crawler — which runs for ~245 days and must not be interrupted — silently won't autostart.

**Fix:** Add to `provision.sh` after the other supervisor stanza installs:
```bash
cp ops/deploy/supervisor/glintstone-crawler.ini /etc/supervisor.d/
supervisorctl reread && supervisorctl update
```

Or document it explicitly in `provision.sh` as a post-provision manual step. Currently it's not mentioned at all.

---

### 2b — CSP header missing from `security-headers.conf` (Medium, security)

**File:** `ops/deploy/nginx/snippets/security-headers.conf`

The snippet sets X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS, and X-Permitted-Cross-Domain-Policies — but no `Content-Security-Policy`. CSP is the primary browser-side defense against XSS. For an app where scholars log in with credentials and view cuneiform content imported from external sources, this matters.

**Suggested starting policy:**
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' assets.glintstone.org https://cdli.ucla.edu data:; connect-src 'self' api.glintstone.org; frame-ancestors 'none';" always;
```

Note: audit `app/static/` for inline styles/scripts before tightening `'unsafe-inline'` on `script-src`.

---

### 2c — Untracked `.claude/worktrees/` directories polluting `git status` (Low)

Seven worktree directories from the PRD-017 swarm show up on every `git status`. Add to `.gitignore` or delete:

```bash
# Add to .gitignore:
.claude/worktrees/

# Or clean manually:
rm -rf .claude/worktrees/agent-*/
```

---

### 2d — New PRDs not committed (Low)

`PRD-018-ai-summaries-mvp.md`, `PRD-019-semantic-search-activation.md`, `PRD-020-token-interpretation-wiring.md`, and this file are untracked. Stage alongside `PRD-agentic-translation.md`.

---

## Phase 3 — CI Quality Gates (Medium / M effort)

### 3a — `mypy` and `pip-audit` still non-blocking in CI (Medium)

**File:** `.github/workflows/test.yml`, lines 43 and 51

Both steps have `continue-on-error: true`. Issue #83 flagged these as technical debt. The PRD-017 swarm added 15+ new Python routes and JS files — new type errors won't gate the deploy.

**Action:** Run `mypy api/ app/ core/ mcp/ --ignore-missing-imports` locally. If fewer than 20 errors remain, fix them and flip both steps to blocking.

---

### 3b — Integration tests don't run in CI (Medium)

**File:** `.github/workflows/test.yml:56–60`

Tests requiring a real database are skipped in CI (VPS-local Postgres, not reachable from GitHub Actions). Before beta, verify the `tests/` suite covers the routes modified by PRD-017 (compositions, scholars, dictionary, dashboard) at minimum with unit tests.

---

## Phase 4 — Performance (High impact / S–M effort)

### 4a — Sequential httpx calls in `tablet_list` (known, unresolved)

**File:** `app/routes/tablets.py:34` (commented as known)

The tablet list route makes multiple blocking API calls sequentially. Under concurrent beta-user load, each page render holds a thread for N × round-trip time. With API and web on the same VPS, individual calls are fast (~2ms), so tolerable for now — but the first thing to parallelize as usage grows.

**Fix approach when prioritized:** Convert to `async def` routes + `httpx.AsyncClient` + `asyncio.gather`.

---

### 4b — `agent_outputs` lazy-persist TTL not verified (Medium)

`agent_outputs.find_fresh` has an unknown TTL. Too short = every AI summary regenerates on next visit (Claude cost). Too long = staleness when underlying facts change after ingestion.

**Action:** `grep -n "TTL\|days\|hours\|fresh" core/agent/agent_outputs.py` — read and confirm the value is sensible for MVP (30 days is a reasonable default).

---

## Phase 5 — Carry-forwards & Status

### 5a — Embedding backfill cron is installed but initial run may not have occurred (Medium)

`ops/deploy/cron/glintstone-embeddings.cron` defines a nightly job at 02:00 UTC. The script `scripts/backfill_embeddings.py` exists. But the initial full backfill (353k artifacts, ~hours) may never have run — the cron only handles incremental nightly runs after the first pass.

**Action:** SSH to VPS:
```sql
SELECT entity_type, COUNT(*) FROM entity_embeddings GROUP BY entity_type;
```
If empty or low count, trigger the initial backfill manually. See PRD-019 for the full sequence.

---

### 5b — mcp.glintstone.org returns 502 (by design, documented) (No action)

The nginx config proxies to port 8005; supervisor has `autostart=false`. Every HTTPS request returns 502. The config comment documents this is intentional until `mcp.server_http` is implemented.

---

## Summary scorecard

| Phase | Finding | Severity | Action |
|-------|---------|----------|--------|
| 1a | cron-ingest.yml hardcoded IP + wrong secret name | **Critical** | `gh secret list` + fix cron-ingest.yml |
| 1b | HttpxTransport 10s timeout vs. 30s Claude synthesis | High | Raise read timeout or expose per-route override |
| 2a | Crawler supervisor config not in provision.sh | Medium | Add stanza or document as post-provision step |
| 2b | CSP header missing from security-headers.conf | Medium | Add CSP policy to nginx snippet |
| 2c | Worktree dirs in git status | Low | Add `.claude/worktrees/` to `.gitignore` |
| 2d | New PRDs untracked | Low | `git add PRD-018*.md PRD-019*.md PRD-020*.md AUDIT-*.md` |
| 3a | mypy + pip-audit non-blocking | Medium | Count errors; flip to blocking when <20 |
| 3b | Integration tests skip in CI | Medium | Unit tests for PRD-017 routes |
| 4a | Sequential httpx calls in tablet_list | Medium | Parallelize when usage grows |
| 4b | agent_outputs TTL unverified | Medium | Read `agent_outputs.py`, document value |
| 5a | Embedding backfill may not have run | Medium | Check `entity_embeddings` count on VPS |
| 5b | mcp.glintstone.org → 502 | N/A | By design |

**Highest-priority action (30 seconds):**
```bash
gh secret list --repo wittkensis/glintstone
```
Confirm `DEPLOY_SSH_KEY` is set. If it isn't, all scheduled ingest jobs have been silently failing.
