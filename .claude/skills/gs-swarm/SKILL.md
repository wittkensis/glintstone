---
name: gs-swarm
description: Glintstone-tuned parallel build/maintenance swarm. Wraps the generic `swarm` lifecycle but pins the right gs-* expert at each phase — gs-canary for triage/blast-radius, the gs-expert-* domain skills for fan-out, gs-expert-deployment + gs-curator-docs for the validate/ship gate — and enforces Glintstone's invariants (two-tier api/app split, migrations-as-wittkensis, one-deploy-at-a-time, source attribution). Use for any multi-part build, feature, or audit on Glintstone that splits into independent units. Triggers — glintstone swarm, glintstone build, build feature, parallel build, fan out, run audit, bug-bash.
metadata:
  question: "How do I run a parallel multi-agent build/audit on Glintstone with the right gs-* expert locked into each phase and Glintstone's invariants enforced?"
  created: 2026-06-25
  modified: 2026-06-25
  context: "Back-ported from fleet--swarm (the *.ericwittke.com fleet swarm) during backlog #29 Phase 3. The fleet version pins fleet--canary-scout / engineer / deploy-verifier per phase and guards kw-system. This Glintstone version pins the gs-* family and guards Glintstone's reality instead: the two-tier api↔app HTTP boundary, migrations run as wittkensis, serialized deploys (one VPS release at a time), and structural source attribution."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#29"]
  related_skills: [gs-canary, gs-expert-deployment, gs-expert-data-model, gs-expert-integrations, gs-expert-ui, gs-expert-assyriology, gs-curator-docs, gs-orient-project]
  supersedes: null
  superseded_by: null
  triggers: [swarm, "glintstone swarm", "glintstone build", "build feature", "parallel build", "fan out", "run audit", "bug-bash", orchestrate, decompose]
---

# Glintstone Swarm

## Invocation
Triggers: glintstone swarm, glintstone build, build feature, parallel build, fan out, run audit, bug-bash

The generic `swarm` lifecycle (decompose → worktrees → fan out → integrate → validate) with the **right gs-* expert locked into each phase** and Glintstone's invariants enforced. Use this — not bare `swarm` — whenever a Glintstone build/fix/audit splits into ≥2 independent units. Run the generic `swarm` skill for the orchestration mechanics; this skill only overrides *which gs-* skill governs which phase* and the Glintstone guardrails.

## Phase → skill/agent map (the whole point)

| Phase | Skill / agent | Why |
|-------|---------------|-----|
| **Triage / blast-radius** | `gs-canary` (read-only — run one per distinct symptom) | Decide **api-only vs app-only vs shared** (the api↔app contract, the token CSS, a migration, a gs-expert domain) *before* fixing, so a symptom isn't patched on both tiers or in the wrong tier. Skip for a single obviously-local change. |
| **Decompose** | `Plan` agent + the routing map below | Cut the work along the two-tier seam and by file ownership; every unit's `owns` set disjoint. |
| **Build / fan-out** | `swarm-worker` (`run_in_background`, `isolation:"worktree"`), each briefed with its gs-expert domain | Each worker owns one slice the Glintstone way (see routing). Migration units run as `wittkensis` + `GRANT` to `glintstone`. |
| **Validate** | `gs-expert-deployment` (CI/pipeline gate) + `gs-curator-docs` (commit/push freshness) | Two-tier: pytest/ruff/mypy green, then **exercise** the feature against a running api+web pair. Deploys are serialized — one VPS release at a time. |

## Routing — which gs-expert governs each unit

Brief each `swarm-worker` with the gs-expert skill its slice lives under (scoped memory per worker, not a shared pile):

| Unit touches | Worker loads | Owns (typical) |
|---|---|---|
| New connector / source / ETL | `gs-expert-integrations` | `ingestion/connectors/*.py`, `ingestion/base.py` |
| Schema, migration, repository, query, lexical | `gs-expert-data-model` | `source-data/migrations/NNN_*.sql`, `core/`, `api/repositories/` |
| ATF, lemma, sign, glossary, morphology | `gs-expert-assyriology` | the linguistics slice of the above |
| CSS, BEM, templates, accessibility | `gs-expert-ui` | `app/templates/`, `app/static/` |
| Deploy, pipeline, supervisor, env | `gs-expert-deployment` | `ops/deploy/`, `.github/workflows/` |
| Commit / push / PR | `gs-curator-docs` | n/a — the ship gate |

## Flow
1. **Triage.** If the change spans the api↔app seam or smells systemic, fan out `gs-canary` (one per distinct symptom, parallel); read each CLASSIFICATION/FIX-TIER. **Fix shared roots once** — a contract change in `api/` that `app/` consumes, a token in the CSS, a base migration — before per-unit work.
2. **Decompose** (`Plan` agent) along the **two-tier seam first**, then by file ownership. The api↔app boundary is a natural cut line: an `api/` unit and the `app/` unit that consumes it are usually *separate* units in *separate waves* (app depends on the new API endpoint). **HARD CHECK:** every `owns` set disjoint — no two concurrent units write the same file.
3. **Group into waves** by dependency depth. API/contract/migration units are almost always **wave 1** (the app tier and UI depend on them).
4. **Fan out** `swarm-worker`, one unit each, background worktrees, each briefed with its gs-expert domain + numbered deliverables. **Migration units:** run migrations as `wittkensis`; after any new table/sequence, `GRANT` to `glintstone` (or the app tier can't read it). Honor the psycopg rollback trap (`ON CONFLICT`/`NOT EXISTS`, not try/except).
5. **Integrate** in dependency order (orchestrator owns merges; workers never merge). Glintstone is a single repo — one commit history; commit per logical unit, not batched blindly.
6. **Validate & ship.** `gs-expert-deployment` gate: pytest + ruff + mypy green, then **exercise the feature against a running api+web pair** (the two-tier contract only proves out live — "it compiled" misses a 500 from a missing `GRANT` or a contract drift). Then `gs-curator-docs` for the commit/push freshness check. **Deploys are serialized:** one VPS release at a time — never two `deploy.yml` runs racing the symlink swap. Push to `main` only with CI green; never `--no-verify`.

> **Pipeline, not a toss:** the two-tier seam is the spine of a Glintstone swarm. Cut along it, ship the API tier first, and the app tier has a real contract to build against instead of guessing.

## Guardrails (inherited from Glintstone CLAUDE.md / gs-orient-project — non-negotiable)
- **Two-tier boundary**: `app/` never touches the DB — it calls `api/` over HTTP (httpx). No unit may smuggle a DB call into the web tier.
- **Migrations as `wittkensis`**; new tables/sequences need an explicit `GRANT` to `glintstone`.
- **psycopg rollback trap**: `conn.rollback()` undoes ALL uncommitted work — use `ON CONFLICT`/`NOT EXISTS`.
- **Source attribution is structural**: annotation rows carry `annotation_run_id`; never silently overwrite — new run.
- **Competing interpretations are a feature**: don't dedupe on disagreement.
- **Serialized deploy**: one VPS release at a time; CI green before `main`; never `--no-verify`; route every deploy through `gs-expert-deployment`.
- **Verify by exercising** a live api+web pair, not by reading code.

TERMINATION: done when every in-scope unit meets its done-criterion, shared roots (contract/token/migration) are fixed once at the right tier, the api+web pair has been exercised green (pytest/ruff/mypy + a live run), and the change is committed (pushed only if the user authorized a deploy, serialized) — or the blocked units are reported with reasons.

## Related
- `swarm` — generic: the orchestration mechanics this wraps (decompose, worktrees, integrate, validate gate)
- `gs-canary` — the triage-phase blast-radius scout this dispatches
- `gs-expert-deployment` — the validate/ship gate; owns deploy serialization
- `gs-curator-docs` — commit/push freshness gate
- `canary-in-the-coalmine` — generic per-bug class-closing loop (gs-canary is the Glintstone-tiered front of it)
