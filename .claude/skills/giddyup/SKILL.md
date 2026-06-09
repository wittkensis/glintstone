---
name: giddyup
description: Backlog triage and sequencing — surveys open issues, recent audits, and project milestones, then proposes a concrete sequenced plan for the next 1–3 sessions. Ask it when you want to know what to work on next.
metadata:
  question: "What should I work on next, and in what order?"
  created: 2026-06-08
  modified: 2026-06-08
  context: "Created after the 2026-06-07 audit session that produced two audit reports (frontend + hardening), three new PRDs (018/019/020), and four GitHub issues. The project needed a recurring triage ritual that synthesizes audits, open issues, and the next milestone into an actionable next-session plan."
  status: active
  audience: [eric]
  owners: [eric]
  related_issues: []
  related_skills: [gs-orient-project, gs-audit-hardening, gs-audit-frontend]
  supersedes: null
  superseded_by: null
  triggers: [giddyup, what's next, triage, backlog, what should I work on, what do I do next, prioritize, sequence, next steps, plan the work, where do we stand]
---

# /giddyup — Backlog triage & next-session sequencing

Run this when you want to know what to work on next. It surveys the full backlog, surfaces the highest-leverage unblocked items, and proposes a concrete session sequence — not a vague list.

---

## How to run

### Step 1 — Load current state (do not skip)

Run all of these before forming any opinion:

```bash
# Open issues — the authoritative backlog
gh issue list --repo wittkensis/glintstone --state open --limit 50

# Recent commits — understand what just shipped
git log --oneline -15

# Audit files — unresolved findings from recent audits
ls AUDIT-*.md PRD-*.md 2>/dev/null | sort

# Any staged or uncommitted work
git status
```

Then read the most recent audit files (e.g. `AUDIT-2026-06-07-hardening.md`, `AUDIT-2026-06-07-frontend.md`) to extract unresolved findings that may not yet have individual GitHub issues.

Also check: `~/.claude/goals.md` — Glintstone's north star is "Ship Helpful Tools" for Assyriologists. Use it to break ties between equally-sized items.

### Step 2 — Build the triage picture

Categorize every open item into one of four buckets:

| Bucket | Criteria |
|--------|----------|
| **🔴 Blocking** | Broken right now, causing silent data loss, or blocks a deploy. Fix before anything else. |
| **🟠 Pre-beta gate** | Must be done before beta scholars are invited. Can't ship with this open. |
| **🟡 High value** | Meaningful feature or improvement; unblocked; high effort-to-impact ratio. |
| **🟢 Backlog** | Real but deferrable; has a clear "do it when X" condition. |

**Blocking criteria checklist:**
- Is CI passing? (`gh run list --repo wittkensis/glintstone --limit 5`)
- Are scheduled ingestion jobs working? (cron secret check — see hardening audit finding 1a)
- Is the deploy pipeline working? (issue #92 — SSH timeout)
- Are any production errors surfacing in nginx logs?

### Step 3 — Identify the current milestone

Look at the issue list for labeled items (`phase-*`, `prd`). Glintstone's auth phases (#75, #77–82) define the feature roadmap post-MVP. The current milestone is the lowest-numbered phase whose prerequisites are met. State it explicitly.

**Current milestone heuristic:**
- No auth shipped yet → milestone is **MVP beta invite** (unauth scholars can use the core read-only features)
- Phase 1 auth shipped → milestone is **Phase 2 — Personal Workspace** (#77)
- etc.

### Step 4 — Clarify priorities (ask if needed)

Before proposing a sequence, ask up to **two questions** if any of these are true:

1. There's a hard tie between two blocking/pre-beta items and the choice requires Eric's input (e.g. "fix the cron secret now" vs "fix the deploy SSH blockage first — which is the bigger pain?")
2. The milestone is ambiguous (the issue labels don't clearly indicate what phase is current)
3. A high-value item requires a time commitment that might conflict with Eric's current bandwidth

Do **not** ask if the answer is obvious from the backlog or audit. Fewer questions = faster start.

### Step 5 — Propose the plan

Output a **sequenced plan** for the next 1–3 sessions. Format:

```
## Next session: [session title]
**Goal:** One sentence — what "done" looks like.
**Unblocks:** What this enables downstream.

Items (in order):
1. [specific action] — [file or tool] — [10 min / 30 min / 1 session]
2. ...

Commit point: [when to commit and what message to use]

---

## Session after that: [title]
...
```

Rules for the plan:
- **Sessions are 2–4 hours.** Don't propose a session that requires a full week.
- **First item in a session must be verifiable in <15 minutes.** Quick win to confirm you're on track.
- **State what each item unblocks.** If an item unblocks nothing and isn't a pre-beta gate, it belongs in a later session.
- **One commit point per logical unit.** Don't let a session run without a commit for more than 2 items.
- **Name the blocking item first, always.** Even if it's small and boring — fix the crit, then move.

---

## Known permanent priorities (always consider these first)

These are standing constraints that override sequencing based on recency alone:

1. **Deploy pipeline must work.** If the deploy is broken (#92 — SSH timeout), nothing else matters until it's fixed. You can't ship anything.
2. **Scheduled ingestion must not silently fail.** `cron-ingest.yml` uses `secrets.DEPLOY_SSH_KEY`; `deploy.yml` uses `secrets.HOSTINGER_SSH_KEY`. If the wrong secret is set (or missing), weekly ORACC and monthly CDLI ingestion silently fail. Verify with `gh secret list --repo wittkensis/glintstone` before other work.
3. **Pre-beta audit findings (Phase 1) must close before beta invite.** Current Phase 1 items from the 2026-06-07 audits: cron secret (hardening 1a), HttpxTransport timeout (hardening 1b), dead parallel.css (frontend F-1), invalid btn-group gap (frontend F-2).
4. **PRDs move to "active" only when their "verify first" step is done.** PRD-018: verify 9 DOM IDs exist. PRD-019: check `entity_embeddings` count on VPS. PRD-020: decision gate (Option A or B).

---

## Standard output format

End the triage with a summary table:

| Session | Goal | Est. time | Unblocks |
|---------|------|-----------|----------|
| Next | ... | ... | ... |
| +1 | ... | ... | ... |
| +2 | ... | ... | ... |

Then one sentence: "The critical path to beta is: [item A] → [item B] → [item C]."

---

## When the backlog is genuinely unclear

If after loading issues and audits you still can't form a confident sequence, run `/gs-audit-hardening` or `/gs-audit-frontend` first and then re-run `/giddyup` with the fresh findings in context.

If Eric needs to make a strategic call (e.g. "should we invite beta scholars before the auth system is built?"), surface the decision and its consequences clearly — don't make the call yourself.
