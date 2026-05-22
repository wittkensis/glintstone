---
question: "What format should a Glintstone hardening audit report follow?"
created: 2026-05-18
modified: 2026-05-18
context: "Template for the structured report produced in Step 3 of gs-audit-hardening. Paste this structure directly as the body of a GitHub issue. Every finding must be specific and actionable — no vague 'could be improved' items."
status: active
audience: [claude]
owners: [eric]
related_issues: ["#83"]
related_skills: [gs-audit-hardening]
supersedes: null
superseded_by: null
---

# Report template

Use this structure verbatim for the GitHub issue body. Fill every field — leave no finding without a concrete fix.

---

```markdown
# Hardening & Optimization Audit — YYYY-MM-DD

> **Previous audit:** [link to prior issue]
> **Scope:** deploy pipeline · provisioning · nginx · rollback · CI/CD · MCP · database · query perf · web layer · docs · config · git hygiene

---

## Summary

| Phase | Description | Items |
|---|---|---|
| Phase 1 | Critical + High, fix before next deploy | N |
| Phase 2 | Docs and config drift, XS–S effort | N |
| Phase 3 | Pipeline quality gaps, M effort | N |
| Phase 4 | Performance wins, ordered by ROI | N |
| Phase 5 | Security and infrastructure | N |

**Items resolved since last audit:** N of M
**Net new items:** N

---

## Previously open items

> Mark each item from the prior audit issue as one of: ✅ Fixed · 🔄 Partially addressed · ❌ Still open · ⚠️ Fix introduced regression

| # | Finding | Status | Notes |
|---|---|---|---|
| 1 | Description from prior audit | ✅ Fixed | Commit sha or PR |
| 2 | Description | ❌ Still open | Current state |

---

## Phase 1 — Fix before next deploy

*Critical or High severity, XS–S effort. A broken deploy or data loss risk lives here.*

### 1.1 [Short title] — **Critical**

**Area:** Deploy pipeline
**File:** `ops/deploy/deploy.sh:253`

**Problem:** Plain-English description of what is broken or will break. Name the exact failure mode — not "this could fail" but "when X happens, Y breaks because Z."

**Fix:**
```bash
# Before
sudo rc-service nginx reload 2>/dev/null || sudo nginx -s reload

# After
sudo nginx -t && (sudo rc-service nginx reload 2>/dev/null || sudo nginx -s reload)
```

Also add to `/etc/sudoers.d/glintstone`:
```
deploy ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t
```

---

### 1.2 [Short title] — **High**

**Area:** Server provisioning
**File:** `ops/deploy/provision.sh:89`

**Problem:** …

**Fix:** …

---

## Phase 2 — Docs and config drift

*Medium severity, XS–S effort. Stale docs and wrong env vars cause the next engineer (or next audit) to waste time or make wrong assumptions.*

### 2.1 [Short title] — **Medium**

**Area:** Documentation
**File:** `CLAUDE.md:13`

**Problem:** …

**Fix:** …

---

## Phase 3 — Pipeline quality

*Medium severity, M effort. Not broken today, but will fail under predictable conditions.*

### 3.1 [Short title] — **Medium**

**Area:** GitHub Actions
**File:** `.github/workflows/test.yml`

**Problem:** …

**Fix:** …

---

## Phase 4 — Performance

*Ordered by ROI: highest impact, lowest effort first.*

### 4.1 [Short title] — **High impact**

**Area:** Database indexes
**File:** `data-model/migrations/`

**Measured or estimated impact:** Full table scan on artifact_genres (N rows) on every filter request.

**Fix:**
```sql
CREATE INDEX idx_ag_p_number ON artifact_genres(p_number);
CREATE INDEX idx_al_p_number ON artifact_languages(p_number);
```

**Why this works:** …

---

### 4.2 [Short title] — **Medium impact**

**Area:** Web layer
**File:** `app/routes/tablets.py:NN`

**Problem:** …

**Fix:** …

---

## Phase 5 — Security and infrastructure

*Low–Medium risk items. Addresses attack surface and configuration hygiene.*

### 5.1 [Short title] — **Medium**

**Area:** nginx
**File:** `ops/deploy/nginx/glintstone.org.conf`

**Problem:** …

**Fix:** …

---

## Appendix: items verified clean

Items from the scope checklist that were explicitly checked and confirmed correct. Include these so the next audit knows what was already verified and doesn't re-investigate.

- **A.8** Pre-deploy DB snapshot: production-only. ✅ Correct.
- **A.9** KEEP_RELEASES=5: reasonable for current VPS disk usage. ✅ No change needed.
- …
```

---

## Finding format rules

1. **Every finding = one specific, verifiable problem + one concrete fix.** If you can't name the exact file, line, and failure mode, it's not ready to be a finding.
2. **Severity labels:** Critical / High / Medium / Low — use definitions from SKILL.md.
3. **Code blocks for fixes.** Show before/after when replacing existing code. Show the full snippet when adding new config.
4. **Phase 4 (performance): always include the measured or estimated impact.** Don't file a performance finding without stating why it matters — query plan, row count, latency delta, or at minimum a clear mechanism.
5. **Appendix is mandatory.** Audits without a "clean" section are harder to trust — readers can't tell if you checked or just skipped.
6. **Previously open items table is mandatory** when a prior audit exists. Don't silently re-file items that were already filed.
