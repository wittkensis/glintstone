---
name: giddyup
description: Full project status view + backlog triage. Loads all open issues, recent audits, untracked PRDs, and CI state, then produces a comprehensive work inventory (every known item, bucketed and sized) followed by a sequenced session plan. Run it when you want to see all remaining work and know what to do next.
metadata:
  question: "What is the complete remaining work, and how should it be sequenced?"
  created: 2026-06-08
  modified: 2026-06-09
  context: "Created after the 2026-06-07 audit session. Extended to produce a full work inventory (not just next 3 sessions) so Eric can see the whole picture and make sequencing decisions with full context."
  status: active
  audience: [eric]
  owners: [eric]
  related_issues: []
  related_skills: [gs-orient-project, gs-audit-hardening, gs-audit-frontend]
  supersedes: null
  superseded_by: null
  triggers: [giddyup, what's next, triage, backlog, what should I work on, what do I do next, prioritize, sequence, next steps, plan the work, where do we stand, show me all the work, full picture, project status]
---

# /giddyup — Full project status & work sequencing

Produces two things: (1) a **complete work inventory** — every known item across issues, audits, and untracked PRDs, bucketed and sized — and (2) a **sequenced session plan** showing how the work reasonably slices up. Run it at the start of any work session or when re-orienting after a gap.

---

## Item card format

**Every item in the inventory uses this exact template — no exceptions:**

```
SEVERITY_DOT **Title** `file:line` `Xm`
What's wrong or what the opportunity is — one sentence, plain English.
**Fix:** The exact action: file edit, command, or decision needed.
```

- **Line 1:** severity dot + bold title + backtick file/location (omit if not applicable) + backtick time estimate
- **Line 2:** problem or opportunity description — written for someone who hasn't seen the code
- **Line 3:** `**Fix:**` — concrete, specific, immediately actionable

Time estimate codes: `5m` `10m` `20m` `30m` `1h` `2h` `half-day` `1 session`

Severity dots:
- 🔴 Broken right now / silently failing / blocks deploy
- 🟠 Shippable gap — wrong or missing, would embarrass the project with real users
- 🟡 High-value improvement — meaningful, unblocked, clear scope
- 🔵 Roadmap — real, but sequentially dependent on something else shipping first
- 🟢 Deferred — real, but has an explicit "do it when X" condition

---

## Step 1 — Load all signal sources (do not skip any)

```bash
gh issue list --repo wittkensis/glintstone --state open --limit 50 --json number,title,labels,createdAt
gh run list --repo wittkensis/glintstone --limit 8
gh secret list --repo wittkensis/glintstone
git log --oneline -15
git status --short
ls PERSONAL/AUDIT-*.md PERSONAL/PRD-*.md 2>/dev/null | sort
```

Also read (if present): `PERSONAL/AUDIT-2026-06-07-hardening.md`, `PERSONAL/AUDIT-2026-06-07-frontend.md`.

Tie-breaker: `~/.claude/goals.md` — north star is "Ship Helpful Tools" for Assyriologists.

---

## Step 2 — Build the complete work inventory

**List every known work item.** Within each section, order by effort ascending (smallest first) so the reader can scan for quick wins. Use the item card format for every entry.

---

### Section A — 🔴 Blocking

Items that are broken right now, causing silent failure, or preventing deploys. These gate everything else. Always check:
- Is CI green? (`gh run list`) — get the failing test name and reason
- Is the deploy pipeline working? (issue #92 — GitHub Actions SSH timeout to Hostinger VPS)
- Is `DEPLOY_SSH_KEY` set as a GitHub secret? (It is not — this means `cron-ingest.yml` silently fails on every scheduled run)
- Are there tracked worktree directories in `.claude/worktrees/`? (Committed before `.gitignore` was updated — GitHub Actions treats them as orphaned submodules)

Surface every current blocking item as a card.

---

### Section B — 🟠 Pre-beta gate

Must close before beta scholars are invited. Not catastrophic but not shippable.

**Standing items from 2026-06-07 audits (update status when resolved):**

🟠 **cron-ingest.yml wrong secret + hardcoded IP** `.github/workflows/cron-ingest.yml` `20m`
`cron-ingest.yml` references `secrets.DEPLOY_SSH_KEY` (not set) instead of `secrets.HOSTINGER_SSH_KEY` (set), and hardcodes `76.13.208.149` on 6 lines instead of `${{ secrets.HOSTINGER_HOST }}`. Every scheduled ingest — weekly ORACC, monthly CDLI — has been silently failing since deployment.
**Fix:** Replace all `secrets.DEPLOY_SSH_KEY` → `secrets.HOSTINGER_SSH_KEY` and `76.13.208.149` → `${{ secrets.HOSTINGER_HOST }}` in the three jobs (oracc, cdli, manual).

🟠 **HttpxTransport 10s read timeout** `app/transports.py:29` `15m`
Default 10s timeout applies to all inter-service calls. AI summary endpoint takes 10–30s on cold cache — any server-side route that calls it will 500. Currently the summary is fetched client-side so impact is low, but the trap is set.
**Fix:** Change to `httpx.Timeout(connect=5.0, read=60.0)` in `HttpxTransport.__init__`.

🟠 **Crawler supervisor config missing from provision.sh** `ops/deploy/provision.sh` `10m`
`glintstone-crawler.ini` is never installed during VPS provisioning. After a reprovision, the image crawler (245-day job, must not be interrupted) silently won't autostart.
**Fix:** Add `cp ops/deploy/supervisor/glintstone-crawler.ini /etc/supervisor.d/ && supervisorctl reread && supervisorctl update` to `provision.sh` after the other supervisor stanza installs.

🟠 **CSP header missing from nginx security config** `ops/deploy/nginx/snippets/security-headers.conf` `20m`
X-Content-Type-Options, X-Frame-Options, HSTS are set — but no Content-Security-Policy. Primary browser-side XSS defense is absent for an app where scholars log in and view content imported from external sources.
**Fix:** Add `add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' assets.glintstone.org https://cdli.ucla.edu data:; connect-src 'self' api.glintstone.org; frame-ancestors 'none';" always;`

🟠 **`@import 'parallel.css'` is dead code** `app/static/css/components/atf-viewer/index.css:10` `5m`
PRD-017 removed parallel mode from `atf-viewer.js` (guarded at line 491 with a comment). The CSS import remains — loaded over the network and parsed on every page, but `atf-viewer--mode-parallel` is never applied.
**Fix:** Remove the `@import 'parallel.css';` line; delete `parallel.css` from the repo. Verify with `git grep 'mode-parallel'` = 0 results first.

🟠 **`btn-group { gap: -1px }` is invalid CSS** `app/static/css/components/buttons.css:203` `10m`
`gap` does not accept negative values — silently ignored by all browsers. Stage filter button groups have a 1px gap between buttons instead of merged borders, making them look like individual buttons.
**Fix:** Replace with `.btn-group .btn:not(:first-child) { margin-left: -1px; }` and add `position: relative` on `:focus` to bring focused button forward.

Include any additional pre-beta items surfaced from loaded issues.

---

### Section C — 🟡 Active PRDs

PRDs with a file written and a clear next action. For unwritten PRDs (issue exists, file doesn't), flag as "needs PRD authoring."

**Known PRDs as of 2026-06-07 (check if files exist, verify status):**

🟡 **PRD-018: AI Summaries MVP** `api/services/agent_service.py:268` `1 session`
Synthesis endpoint uses `synthesis.v1` prompt; `v2` adds dialect translation, scholarly disagreement qualification, mixed-language enforcement. 9 DOM IDs in `detail.html` need verification before this can ship.
**Fix:** (1) Verify 9 DOM IDs exist in `detail.html`; (2) Change `synthesis.v1` → `synthesis.v2` at line 268; (3) Add `agent_outputs.insert` caching to `do_suggest_line_translation`.

🟡 **PRD-019: Semantic Search Activation** `scripts/backfill_embeddings.py` `1 session + VPS time`
Search engine infrastructure is complete (hybrid lexical + semantic + RRF). `entity_embeddings` table is likely empty — semantic results return nothing. `VOYAGE_API_KEY` may not be set on VPS (falls back to Anthropic key, which fails silently against Voyage API).
**Fix:** (1) SSH to VPS; check `entity_embeddings` count; (2) Verify `VOYAGE_API_KEY` in `.env`; (3) Write `backfill_embeddings.py` with `--entity-type` and `--limit` flags; (4) Run initial backfill.

🟡 **PRD-020: Token Interpretation — decision gate** `PERSONAL/PRD-020-token-interpretation-wiring.md` `10m`
Backend complete; frontend disconnected (no `data-token-id` on `.atf-word` elements). Recommended: Option B (descope from MVP — popover already shows lexical data; AI layer adds 2-5s latency per click with no confirmed user demand).
**Fix:** Document Option B decision in the PRD, close the decision gate, file a backlog issue for post-beta revisit.

For the following, check whether a PRD file exists before listing as ready:
- 🟡 **PRD-002a** — Artifact Summary Sidebar Refactor (issue #55) — overlaps PRD-018
- 🟡 **PRD-002b** — Line Translation Suggestions: ATF Viewer Integration (issue #56)
- 🟡 **PRD-003** — Browse Tablets Page (issue #57)
- 🟡 **PRD-005** — Tablet Viewer (issue #58)
- 🟡 **PRD-001** — Translation Builder (issue #54)

---

### Section D — 🟡 High-value improvements

Improvements with clear scope, not yet filed as PRDs. **Include proactive recommendations — items worth doing that haven't been explicitly requested.** Within each sub-group, order by effort ascending.

**Infrastructure & CI:**

🟡 **Pin Python version in CI** `.github/workflows/test.yml` `5m`
`python-version: "3.13"` resolves to the latest 3.13.x patch, which could silently change behavior on point releases.
**Fix:** Change to `python-version: "3.13.4"` (or current stable patch) to lock behavior.

🟡 **Verify `agent_outputs` TTL** `core/agent/agent_outputs.py` `10m`
TTL for AI summary caching is unverified. Too short = Claude spend on every revisit; too long = stale results after ingestion updates. Expected value: 30 days.
**Fix:** `grep -n "TTL\|days\|hours\|fresh" core/agent/agent_outputs.py` — read and confirm; adjust if wrong.

🟡 **Add `ANTHROPIC_API_KEY` check to health route** `api/routes/health.py` `15m`
If the key expires, AI endpoints fail with a cryptic 500 rather than a clear signal. Scholars see a broken page with no explanation.
**Fix:** Add `"anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY"))` to the health check response.

🟡 **Upgrade GitHub Actions to Node.js 24** `.github/workflows/` `20m`
`actions/checkout@v4` and `actions/setup-python@v5` run on deprecated Node.js 20. GitHub forces the upgrade June 16th 2026 — this will break CI if not addressed first.
**Fix:** Bump to `actions/checkout@v4` → check latest tag; `actions/setup-python@v5` → check latest tag. Pin explicit versions.

🟡 **Add nginx rate limiting to AI endpoints** `ops/deploy/nginx/glintstone.conf` `30m`
`/artifacts/*/summary` triggers a Claude API call. No rate limiting means a single user (or bot) can exhaust API budget. Risk is low until beta but cost exposure is real.
**Fix:** Add `limit_req_zone $binary_remote_addr zone=ai:10m rate=5r/m;` to `nginx.conf` and `limit_req zone=ai burst=3 nodelay;` on the AI endpoint location block.

🟡 **Flip `mypy` and `pip-audit` to blocking in CI** `.github/workflows/test.yml` `1-2h`
Both steps have `continue-on-error: true`. PRD-017 added 15+ new Python files; new type errors won't gate deploys. Run `mypy api/ app/ core/ mcp/ --ignore-missing-imports` locally first — if <20 errors, fix them and flip.
**Fix:** Remove `continue-on-error: true` from both steps in `test.yml`. Fix any mypy errors surfaced.

🟡 **Parallelize sequential httpx calls in `tablet_list`** `app/routes/tablets.py:34` `2h`
Tablet list route makes multiple blocking API calls in sequence. Each page render holds a thread for N × round-trip time. Low-risk now (API and web on same VPS, ~2ms per call) but the first bottleneck as beta usage grows.
**Fix:** Convert route to `async def`, use `httpx.AsyncClient` with `asyncio.gather` for concurrent calls.

**Data & ingestion:**

🟡 **Triage ORACC dead-letter backlog** `ingestion/` `2h`
~2.4M lemma tokens never processed (issues #87, #63). Unknown split of fixable vs permanently malformed vs just-needs-retry. Currently growing silently.
**Fix:** Run `python -m ingestion.cli dead-letters` and categorize a sample (100 records). Decide: fix the connector, retry as-is, or archive.

🟡 **Compositions Phase 2: detail page + transmission history** issue #90 `1 session`
Detail page, transmission history timeline, and multi-composite rendering defined in the issue. Browse layer from PRD-017 is shipped; detail layer is missing.
**Fix:** Author a PRD file, then build. Issue has the scope.

🟡 **Dashboard Phase 2: Frontier section** issue #91 `1 session`
Compositions with large coverage gaps — useful for directing scholar attention to undertranslated tablets.
**Fix:** Author a PRD file, then build.

**Frontend / UX:**

🟡 **Fix stale breadcrumb test (or restore the breadcrumb)** `tests/web/test_tablet_detail.py` `15m`
PRD-017 removed `aria-label="breadcrumb"` from `detail.html` (replaced with a back-arrow pattern) but the test still asserts it exists. CI is failing because of this one test.
**Fix:** Either update the test to assert on the back-arrow pattern, or restore the breadcrumb nav with `aria-label="breadcrumb"` and `breadcrumb__current`.

🟡 **F-3: Replace raw font-size/gap values with tokens** `compositions.css` `dictionary.css` `20m`
PRD-017 introduced `font-size: 1rem`, `gap: 2px`, `gap: 3px`, `font-size: 3rem`, `font-size: 4rem` as raw values. The 3rem/4rem are intentional display sizes for cuneiform signs and need a named token.
**Fix:** Add `--text-display-lg: 4rem` to `tokens.css`; replace raw values with `var(--text-base)`, `var(--space-0-5)`, `var(--text-display-lg)`.

🟡 **F-4: Inline `style="font-style: normal"` in dictionary template** `app/templates/dictionary/index.html:273,292` `10m`
Two `<span>` elements override inherited italic styles inline rather than via a class. Minor hygiene.
**Fix:** Add `.dict-sign-name, .dict-guide-word { font-style: normal; }` to `dictionary.css`; replace inline style attributes with the new classes.

🟡 **Token popover: add skeleton/loading state** `app/static/js/token-popover.js` `30m`
Popover currently shows nothing while waiting for lexical API data. On slow connections or under load, the user sees an empty popover for 500ms+ with no feedback.
**Fix:** Show a skeleton or spinner immediately on click; replace with content on response. CSS can handle the transition with a `.is-loading` class.

🟡 **Extract inline auth IIFE from `base.html`** `app/templates/base.html` `30m`
Header avatar/login state is driven by an inline `<script>` IIFE that calls `/_me`. Correct behavior, but mixes presentation logic into the layout template and is untestable.
**Fix:** Move to `app/static/js/header-auth.js`; load with `<script src="...">` in `base.html`.

🟡 **Write unit tests for PRD-017 routes** `tests/web/` `1 session`
Compositions, scholars, dictionary, and dashboard pages were added by the swarm but have zero test coverage. The 276-passing suite hasn't grown with the surface area.
**Fix:** Add `test_compositions.py`, `test_scholars.py`, `test_dictionary.py`, `test_dashboard.py` — at minimum: happy-path route test (200 status, key DOM elements present) and a no-data graceful-empty test for each.

---

### Section E — 🔵 Auth roadmap (post-MVP, sequential)

Do not session-plan these until MVP beta is shipped. Surface only if asked.

🔵 **Auth & User System PRD** issue #75 — prereq: MVP beta invite
🔵 **Phase 2: Personal Workspace** issue #77 — prereq: Phase 1 auth
🔵 **Phase 3: Scholar Identity** issue #78 — prereq: Phase 2
🔵 **Phase 4: User Settings** issue #79 — prereq: Phase 3
🔵 **Phase 5: Contributed Translations** issue #80 — prereq: Phase 4
🔵 **Phase 6: Notifications & Triggered Email** issue #81 — prereq: Phase 5
🔵 **Phase 7: Institutional SSO** issue #82 — prereq: Phase 6

---

### Section F — 🟢 Deferred

Real items with an explicit deferral condition. Do not move these unless the condition is met.

🟢 **PRD-020 Option A: token interpretation wiring** — defer until beta user feedback confirms they want it
🟢 **Token popover AI panel** — defer until PRD-020 Option A is chosen
🟢 **Semantic snippet in global-search drawer** — defer until `entity_embeddings` is populated (PRD-019)
🟢 **COUNT(*) double-query pagination** — fine at current scale; revisit when search latency exceeds 200ms under load
🟢 **Compositions Phase 2 detail page** issue #90 — defer until PRD-017 browse layer is validated with users
🟢 **ML model integrations** (BabyLemmatizer, DETR, Akkademia) — no issues filed; post-MVP research area
🟢 **mcp.glintstone.org** — intentionally 502; `autostart=false` in supervisor; blocked on `mcp.server_http` implementation

---

## Step 3 — Identify the current milestone

State it explicitly. Derive from CI status, deploy status, and shipped auth features — don't assume.

- CI red → **CI green** (nothing else can ship)
- Deploy broken → **Deploy works** (nothing else can reach prod)
- No auth, app is functional read-only → **MVP beta invite** (2-3 test scholars)
- MVP beta shipped → **Phase 2 auth** issue #77

---

## Step 4 — Ask at most one question (skip if obvious)

Only if the milestone is genuinely ambiguous or a strategic call is needed that Claude shouldn't make unilaterally. Don't ask about effort or preferences — make a recommendation.

---

## Step 5 — Session plan

After the full inventory, show how the work slices into sessions to reach the current milestone.

**Session card format:**

```
### Session N — [title]
**Goal:** [one sentence — what done looks like]
**Unblocks:** [what this enables downstream]

| # | 🔴/🟠/🟡 | Task | Location | Time |
|---|----------|------|----------|------|
| 1 | 🔴 | ... | file:line | 15m |
| 2 | 🟠 | ... | file:line | 20m |

**Commit:** `type(scope): message`
**Swarm opportunity:** [yes/no — if 3+ items are independent, name them]
```

Session rules:
- Sessions are 2–4 hours. Don't inflate.
- Session 1 always starts with the highest-severity blocking item.
- First item in every session must be completable in <15 minutes.
- One commit point per logical unit — never more than 2h without committing.
- If a session is genuinely 45 minutes of real work, say so.

**End the output with:**

```
## Critical path to [milestone]
[item] → [item] → [item]

## Backlog summary
🔴 Blocking: N  |  🟠 Pre-beta: N  |  🟡 Active: N  |  🔵 Roadmap: N  |  🟢 Deferred: N
```

---

## Permanent constraints (override all sequencing)

1. 🔴 **Never push to main with red CI.** Fix the failing test before anything else.
2. 🔴 **Deploy pipeline must work.** Issue #92 (SSH timeout) blocks every production ship.
3. 🟠 **Cron ingestion secret.** `secrets.DEPLOY_SSH_KEY` is not set; `cron-ingest.yml` references it. Every scheduled run silently fails.
4. 🟠 **VPS snapshot before risky deploys.** Use `mcp__hostinger__VPS_createSnapshotV1` before anything touching nginx, supervisor, or migrations.
5. **Two-tier rule.** `app/` never touches the DB. Any route in `app/` that imports from `core/database.py` is wrong.
