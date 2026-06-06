---
name: canary-in-the-coalmine
description: For a batch of small bugs/fixes, treat each as a possible symptom of a broader pattern before fixing it. Use when the user hands over a laundry list of bugs/issues to debug ("fix these", "here's a list", "debug this list", "small fixes", "punch list"), or any single bug that smells systemic. For each bug it names the invariant violated, measures the blast radius (this file → this app → the whole fleet), classifies one-off vs systemic, fixes at the right altitude, and codifies the pattern so it can't recur.
---

# Canary in the Coalmine

A bug is a **sample from a distribution**, not an isolated event. The dead canary isn't
the problem — it's the warning that the air is bad everywhere. So for every item on a fix
list: fix the instance **and** ask "what broader pattern or inconsistency is this a symptom
of?" Then close the whole class, not just the one you were shown.

> Bullets showing on list rows in **one** app but not the others → a row/list pattern wasn't
> applied consistently. A viewport not filling the iOS view → the shell/CSS contract isn't
> uniformly applied. Each "small bug" is a probe into a systemic gap.

This is the **reactive** complement to a proactive audit pass. Use your shared
contracts as the yardstick: your shared design-system stylesheet, shared component/pattern modules, and shared auth.

---

## The loop — run for EACH bug

1. **Reproduce & locate.** Find the exact instance (file:line, the offending markup/CSS/logic).
2. **Name the invariant.** State the rule that *should* hold — the token, class, contract, or
   convention that, if applied, would make the bug impossible. If you can't name it, you don't
   understand the bug yet. (e.g. "list rows use `.row`, which sets `list-style:none`" / "the
   iOS shell is `#root{position:fixed;inset:0}` → `.page` flex column with `100dvh` + safe-area").
3. **Measure the blast radius.** Search for every place the same construct appears, in 3 scopes:
   - **Local** — same file/component (other rows, other inputs).
   - **App-wide** — everywhere in this app (`grep`/`rg` the repo).
   - **Workspace-wide** — every other project in your workspace + the shared base in
     `TEMPLATES/themes/`. The example bug usually has siblings here.
   Report counts + locations. "Found in 1/6 apps" vs "11 occurrences across 4 apps" changes the fix.
4. **Classify** the canary:
   | Class | Meaning | Fix altitude |
   |-------|---------|--------------|
   | **One-off** | genuinely isolated; the pattern holds elsewhere | fix the instance |
   | **Inconsistent application** | a correct shared pattern exists but isn't applied here (or there) | fix ALL violating instances; add enforcement |
   | **Missing pattern** | no shared rule — each app hand-rolls it (and one got it wrong) | codify the pattern (token/class/contract), then apply everywhere |
   | **Broken pattern** | the shared rule/base itself is wrong → every consumer is subtly affected | fix the source in `TEMPLATES/themes/` (or the skill), re-propagate to all consumers |
5. **Fix at the right altitude** (per the table) — never patch a systemic bug as a one-off.
6. **Prevent recurrence.** Make the class un-reintroducible: add/repair a shared design-system
   token or component class, tighten the contract in the relevant shared module/skill, add a
   audit dimension/check, or add a test scenario/assertion that fails
   if it regresses. Codify, don't just remember.
7. **Confirm the class is closed.** Re-run the search → clean. For UI, re-run the affected apps'
   scenarios via your visual/integration test suite so siblings didn't regress (mandatory for any
   shared design-system edit — re-validate **every** consumer).

---

## Batch handling (a laundry list)
1. **Triage first.** Read the whole list before fixing anything. Group items that likely share a
   root (three "spacing" bugs may be one token; "bullets" + "wrong list padding" may be one row
   pattern). Fixing the root may clear several list items at once.
2. **Order by blast radius**, not by list order: shared-base/broken-pattern bugs first (they ripple),
   then inconsistent-application, then true one-offs.
3. **One root, one change, then re-measure** — after a systemic fix, re-scan; some later list
   items may already be resolved. Don't re-fix them as one-offs.
4. **End with the canary report** (below) so the user sees which "small bugs" were actually
   systemic and what was codified.

## Output — per bug, then a summary
For each bug:
```
BUG: <what was reported>
  Instance:     <file:line + the offending construct>
  Invariant:    <the rule that should hold — token/class/contract>
  Blast radius: <local: N · app: N · fleet: N/6 apps>  [locations]
  Class:        one-off | inconsistent | missing-pattern | broken-pattern
  Fix:          <what changed, at what altitude>
  Prevention:   <token/class/contract/audit-dim/test added so it can't recur>
  Verified:     <search clean · scenarios pass on apps X,Y>
```
End with a table: `bug → scope → systemic? → root cause → action → siblings fixed`, and call out
any canary that revealed a real fleet-wide gap worth a follow-up.

---

## Worked examples
- **"Bullets on list rows in app X only."** Invariant: list rows render via `.row`/`.list-card`
  (no raw `<ul><li>` with default markers; `list-style:none`). Blast radius: `rg "<li" <your-workspace>/*`
  + check which apps use `.row` vs raw lists. Likely **inconsistent application** (X hand-rolled a
  `<ul>` instead of the row pattern) or **missing reset** (base lacks a list reset). Fix: convert X to
  `.row`/`.list-card`; if the base reset is missing, add `ul,ol,li{list-style:none}` (or a `.list`
  reset) to the shared design-system and re-propagate. Prevent: audit dimension "raw `<li>` in components".
- **"Viewport doesn't fill the iOS view in app Y."** Invariant: the iOS shell contract
  (your shared layout/architecture reference) — `#root{position:fixed;inset:0;overflow:hidden}` → `.page`
  flex column `height:100dvh` → fixed bottom nav with `env(safe-area-inset-bottom)` and
  `<meta viewport ... viewport-fit=cover>`. Blast radius: check the shell + viewport meta in all 6
  apps. Usually **inconsistent application** (Y missing `100dvh`/`viewport-fit=cover`/the fixed root)
  or **broken pattern** (the shared shell drifted). Fix at the shell layer; prevent with a
  a visual-test assertion that the nav reaches the bottom (no seam) + a viewport-meta check.

## Guardrails
- **Don't stop at the symptom.** A patched instance with the class still open is an unfixed bug.
- **Don't blanket-fix without confirming the same root** — two bugs that look alike can have
  different causes; verify the invariant matches before batch-applying.
- **Don't scope-creep.** Close the class the canary points to; don't fold in unrelated refactors.
- **Honor altitude both ways** — don't fix a one-off as a fleet change, and don't fix a fleet
  problem six times by hand when one base change does it.
- **Codify or it returns.** If the only thing stopping recurrence is your memory, it's not fixed.
