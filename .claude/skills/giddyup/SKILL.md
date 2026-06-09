---
name: giddyup
description: Full project status view + backlog triage. Loads all open issues, recent audits, untracked PRDs, and CI state, then produces a comprehensive work inventory (every known item, bucketed and sized) followed by a sequenced session plan. Run it when you want to see all remaining work and know what to do next.
metadata:
  question: "What is the complete remaining work, and how should it be sequenced?"
  created: 2026-06-08
  modified: 2026-06-08
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

## Step 1 — Load all signal sources (do not skip any)

```bash
# Open GitHub issues
gh issue list --repo wittkensis/glintstone --state open --limit 50 --json number,title,labels,createdAt

# CI status — is anything on fire?
gh run list --repo wittkensis/glintstone --limit 8

# GitHub secrets — confirm cron-ingest prereqs
gh secret list --repo wittkensis/glintstone

# Recent commits — understand what just shipped
git log --oneline -15

# Uncommitted work
git status --short

# Local audit + PRD files (may contain findings not yet filed as issues)
ls AUDIT-*.md PRD-*.md 2>/dev/null | sort
```

Also read (if present): `AUDIT-2026-06-07-hardening.md`, `AUDIT-2026-06-07-frontend.md` — these contain Phase 1/2 findings that feed the pre-beta gate list.

Tie-breaker reference: `~/.claude/goals.md` — Glintstone's north star is "Ship Helpful Tools" for Assyriologists. When two items are equal size, pick the one closer to that.

---

## Step 2 — Build the complete work inventory

**This is the core of the output.** List every known work item — not just the top 5. Organize into the sections below. Within each section, order by effort (smallest first) so the reader can scan for quick wins.

---

### Section A — 🔴 Blocking (fix before anything else)

Items that are broken right now, causing silent failure, or preventing deploys. These gate everything else.

For each item include: what's broken, where it's broken, and the exact fix (file + line or command).

**Standing checklist — always verify these:**
- Is CI green? (`gh run list`) — if red, what test/step is failing and why?
- Is the deploy pipeline working? (issue #92 — GitHub Actions SSH timeout to Hostinger VPS)
- Is `DEPLOY_SSH_KEY` set as a GitHub secret? If not, `cron-ingest.yml` is silently failing — weekly ORACC + monthly CDLI ingestion not running. The fix: `cron-ingest.yml` should reference `secrets.HOSTINGER_SSH_KEY` (already set), not `secrets.DEPLOY_SSH_KEY` (not set).
- Are there uncommitted tracked worktree directories in `.claude/worktrees/`? These get misread as orphaned submodules by GitHub Actions and generate fatal cleanup errors.

---

### Section B — 🟠 Pre-beta gate (must close before inviting scholars)

Things that are wrong or missing that would embarrass the project in front of real users. Not catastrophic but also not shippable.

**Standing pre-beta items from 2026-06-07 audits:**

Hardening:
- **1a** — `cron-ingest.yml` wrong secret name + hardcoded VPS IP (6 lines) — file: `.github/workflows/cron-ingest.yml` — 20 min
- **1b** — `HttpxTransport` 10s timeout too low for Claude synthesis (30s+) — file: `app/transports.py:29` — 15 min
- **2a** — `glintstone-crawler.ini` not installed by `provision.sh` — file: `ops/deploy/provision.sh` — 10 min
- **2b** — CSP header missing from nginx security config — file: `ops/deploy/nginx/snippets/security-headers.conf` — 20 min

Frontend:
- **F-1** — `@import 'parallel.css'` in `atf-viewer/index.css` — dead code, parallel mode was removed — 5 min
- **F-2** — `btn-group { gap: -1px }` is invalid CSS (gap can't be negative; silently ignored) — fix with `margin-left: -1px` on non-first children — 10 min

Also include any other pre-beta items surfaced from the loaded issues.

---

### Section C — 🟡 Active PRDs (defined, unblocked or unstarted)

PRDs that have been written and are ready to implement, or have a clear "verify first" step before implementation starts.

**Known PRDs as of 2026-06-07:**

- **PRD-018** — AI Summaries MVP (issue #55)
  - Verify first: 9 DOM IDs exist in `detail.html` — 10 min
  - Fix `synthesis.v1` → `synthesis.v2` in `agent_service.py:268` — 5 min
  - Add caching to `do_suggest_line_translation` — 30 min
  - Estimated total: ~1 session

- **PRD-019** — Semantic Search Activation
  - Verify first: SSH to VPS, check `entity_embeddings` count — 5 min
  - Verify/add `VOYAGE_API_KEY` to VPS `.env`
  - Write `scripts/backfill_embeddings.py` — 2h
  - Run backfill (hours of VPS time, not Claude time)
  - Estimated total: ~1 session (+ background VPS time)

- **PRD-020** — Token Interpretation: Wire or Descope
  - Decision gate: Option A (wire up, 4-6h) vs Option B (descope, 0h — recommended for MVP)
  - If Option B: 10 min to document decision in the PRD and close the issue

- **PRD-002a** — Artifact Summary: Sidebar Refactor + AI Summaries (issue #55) — overlaps PRD-018
- **PRD-002b** — Line Translation Suggestions: ATF Viewer Integration (issue #56)
- **PRD-003** — Browse Tablets Page (issue #57)
- **PRD-005** — Tablet Viewer (issue #58)
- **PRD-001** — Translation Builder (issue #54)

For any PRD where the issue exists but the PRD file doesn't, note it as "needs PRD authoring" — don't treat it as ready to build.

---

### Section D — 🟡 High-value improvements (no PRD, but clear scope)

Improvements worth doing that aren't tracked as formal PRDs but have clear enough scope to estimate. Include proactive recommendations here — things that would meaningfully improve the project even if they haven't been explicitly requested.

**Infrastructure improvements:**
- **CI: Flip `mypy` and `pip-audit` to blocking** — currently `continue-on-error: true`; PRD-017 added 15+ new Python files. First check error count: `mypy api/ app/ core/ mcp/ --ignore-missing-imports`. If <20 errors, fix and flip. (~1-2h depending on error count)
- **Upgrade GitHub Actions to Node.js 24** — `actions/checkout@v4` and `actions/setup-python@v5` are running on deprecated Node.js 20; GitHub forces the upgrade June 16th 2026. Check for newer action versions and pin them. (~20 min)
- **Parallelize sequential httpx calls in `tablet_list`** — documented in `app/routes/tablets.py:34`; under concurrent load each page render holds a thread. Convert to `async def` + `asyncio.gather`. (~2h)
- **Verify `agent_outputs` TTL is sensible** — TTL for AI summary caching is unverified; too short = repeated Claude spend; too long = stale results. Check `core/agent/agent_outputs.py` — should be 30 days. (~10 min to read, 15 min to adjust)

**Data & ingestion:**
- **Triage ORACC dead-letter backlog** (#87, #63) — ~2.4M lemma tokens never processed. Run `python -m ingestion.cli dead-letters` and categorize: fixable vs permanently malformed vs just-needs-retry. This is a research session, not a coding session. (~2h)
- **Compositions Phase 2** (#90) — detail page, transmission history timeline, multi-composite fix
- **Dashboard Phase 2: Frontier section** (#91) — compositions with large coverage gaps
- **Comprehensive composites + source integration roadmap** (#89)

**Frontend / UX improvements:**
- **F-3** — Replace raw font-size/gap values with design tokens in `compositions.css` and `dictionary.css` — 20 min
- **F-4** — Inline `style="font-style: normal"` in `dictionary/index.html:273,292` — move to CSS class — 10 min
- **Search performance audit** (#88) — `perf: audit and optimize search, filtering, and page-load latency`
- **Token popover: add skeleton/loading state** — currently shows nothing while waiting for lexical data; a loading state prevents perceived jank
- **Extract inline auth IIFE from `base.html`** to `app/static/js/header-auth.js` — F-5 from frontend audit — 30 min
- **Add `aria-label="breadcrumb"` to breadcrumb nav** (or update the stale CI test that checks for it) — the PRD-017 redesign removed the breadcrumb from `detail.html` but left the test — CI is failing because of this. Either restore the breadcrumb or update the test. (~15 min)

**Proactive recommendations (not in the backlog yet, but worth doing):**
- **Write unit tests for PRD-017 routes** — compositions, scholars, dictionary, and dashboard were added by the swarm and have no unit tests. The CI test count (276 passing) hasn't grown with the new surface area. Add at minimum happy-path route tests for each new page. (~1 session)
- **Add nginx rate limiting to AI endpoints** — `/artifacts/*/summary` calls Claude; without rate limiting a single bad actor can run up API costs. Add `limit_req_zone` in nginx. (~30 min)
- **Add `ANTHROPIC_API_KEY` verification to the health check route** — if the key expires or is missing, AI endpoints fail silently. The health check at `GET /health` should verify the key is set (not the value — just `bool(os.environ.get("ANTHROPIC_API_KEY"))`). (~15 min)
- **VPS snapshot before next major deploy** — before shipping anything significant, take a Hostinger VPS snapshot via the MCP tool. Zero-downtime rollback insurance. (~2 min via `mcp__hostinger__VPS_createSnapshotV1`)
- **Pin Python version in CI** — `test.yml` doesn't pin a patch version; a Python 3.13.x point release could silently change behavior. Pin to `python-version: "3.13.x"`. (~5 min)

---

### Section E — 🔵 Auth roadmap (post-MVP, sequential)

These are post-MVP phases. They're sequentially dependent — ship each phase before the next.

| Phase | Issue | Description | Prereq |
|-------|-------|-------------|--------|
| Auth PRD | #75 | Auth & User System — PRD | MVP beta invite |
| Phase 2 | #77 | Personal Workspace (notes, history, filter sets, bookmarks) | Phase 1 auth |
| Phase 3 | #78 | Scholar Identity (claiming, bio editing) | Phase 2 |
| Phase 4 | #79 | User Settings & Preferences | Phase 3 |
| Phase 5 | #80 | Contributed Translations | Phase 4 |
| Phase 6 | #81 | Notifications & Triggered Email | Phase 5 |
| Phase 7 | #82 | Institutional SSO | Phase 6 |

These don't need session planning yet — they're post-beta. Surface them only if Eric asks.

---

### Section F — 🟢 Backlog / deferred

Items that are real but explicitly deferred. For each: state the deferral condition.

- **PRD-020 Option A** (token interpretation wiring) — defer until beta user feedback confirms they want it
- **Token popover AI panel** — defer until Option A of PRD-020 is chosen
- **Semantic snippet in global-search drawer** — post-PRD-019 (no point until embeddings are populated)
- **COUNT(*) double-query pagination** — replace with window function; fine at current scale
- **Compositions Phase 2 detail page** (#90) — after PRD-017 browse layer is validated with users
- **ML model integrations** (BabyLemmatizer, DETR, Akkademia) — no issues filed; post-MVP research area
- **mcp.glintstone.org** — intentionally returns 502; `autostart=false` in supervisor; blocked on `mcp.server_http` implementation

---

## Step 3 — Identify the current milestone

State the milestone explicitly. Don't assume — derive it from CI status, deploy status, and what auth features are shipped.

**Milestone heuristics:**
- CI red → milestone is **CI green** (nothing else can ship)
- Deploy broken → milestone is **Deploy works** (nothing else can reach prod)
- No auth shipped, app is functional read-only → milestone is **MVP beta invite** (invite 2-3 test scholars)
- MVP beta shipped → milestone is **Phase 2 auth** (#77)

---

## Step 4 — Ask at most one question (skip if obvious)

Only ask a clarifying question if:
1. The milestone is genuinely ambiguous and the answer changes the session sequence
2. A strategic call is needed that Claude shouldn't make (e.g., "skip auth entirely and just invite scholars with a magic link?")

Don't ask about effort, time, or preferences — make a recommendation.

---

## Step 5 — Output: session plan

After the full inventory, propose how the work slices into sessions. Sessions are 2–4 hours. Show as many sessions as needed to reach the current milestone, plus a brief description of what follows.

Format each session:

```
### Session N — [title]
**Goal:** [one sentence — what done looks like]
**Unblocks:** [what this enables]

| # | Task | File / Tool | Time |
|---|------|-------------|------|
| 1 | ... | ... | 15m |
| 2 | ... | ... | 30m |

Commit: `[type(scope): message]`
```

Rules:
- **Session 1 starts with the highest-severity blocking item**, even if it's boring.
- **Each session has a clear commit point.** Never more than 2h without committing.
- **Small wins come first within a session** — they build momentum and surface surprises early.
- **Don't pad sessions.** If a session is 45 minutes of real work, say so. Don't inflate it to fill time.
- **Surface the swarm opportunity** — if 3+ items in a session are independent, note: "these can be parallelized with `/swarm`."

End with:

```
## Critical path to [milestone]
[item A] → [item B] → [item C]

## Full backlog size
Blocking: N items | Pre-beta: N items | Active PRDs: N | Improvements: N | Deferred: N
```

---

## Permanent constraints (override all sequencing)

1. **Never push to main with red CI.** Fix the test before anything else.
2. **Deploy pipeline must work.** Issue #92 (SSH timeout) blocks every production ship.
3. **Cron ingestion secret.** `secrets.DEPLOY_SSH_KEY` is not set; `cron-ingest.yml` references it. Every scheduled run silently fails. Fix in `cron-ingest.yml` before the next ingest window.
4. **VPS snapshot before risky deploys.** Use `mcp__hostinger__VPS_createSnapshotV1` before anything that touches nginx, supervisor, or migrations.
5. **Two-tier rule.** `app/` never touches the DB directly. Any improvement touching `app/routes/` that reaches for `core/database.py` is wrong.
