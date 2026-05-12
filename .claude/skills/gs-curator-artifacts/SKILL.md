---
name: gs-curator-artifacts
description: Curates a categorized knowledge base of interesting records across every entity (artifacts, scholars, lemmas, signs, periods, places, search terms). Always knows what to pull to demo or test something. Knows how to find it if it's not on hand.
metadata:
  question: "I need a representative record (tablet, scholar, lemma, sign, period, place, search term) to demo or test something. Which one, and where would I look if it's not on hand?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Created during the 2026-05-11 overhaul. Solves a recurring pain point: we re-discover good test records every time we need one. This skill maintains a categorized catalog and the discovery queries to extend it. Eager — always wants to learn new records."
  status: active
  audience: [claude, engineers, scholars]
  owners: [eric]
  related_issues: ["#4"]
  related_skills: [gs-expert-data-model, gs-expert-assyriology, gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: ["test tablet", "sample tablet", "demo tablet", "find a tablet", "give me a sample", "test scholar", "test lemma", "test sign", "test record", "edge case", "interesting record", "fixture", "scenario for"]
---

# Glintstone curator — interesting records

**Superpower**: always knows what data to pull to demo or test something. Knows how to find it if it's not on hand.

## Entity scope

Curates examples of:

- **Artifacts** (P-numbers) — by scenario: damaged, joined fragments, composite exemplars, bilingual, multi-surface, rich ATF, rich lemmatization, lonely (no ATF), etc.
- **Scholars** (`scholars.id`) — by scenario: with merge history, high publication count, multi-affiliation, ORCID-linked, both ATF editor and ORACC author
- **Lemmas** (`lexical_lemmas.id` or `glossary_entries.entry_id`) — by scenario: high polysemy, top attestation, Sumerogram-backed, contested POS, cross-language cognate chain
- **Signs** (OGSL sign id) — by scenario: Unicode-mapped, MZL-only, ABZ-only, compound, modified, value-ambiguous, no Unicode (manual curation needed)
- **Periods, provenience, genres** — illustrative examples (Ur III + Nippur + lexical lists, etc.)
- **Search terms** — semantic queries that exercise interesting paths
- **Composites / Q-numbers** — with rich exemplar networks
- **Translations** — examples of good / contested / partial translations
- **Annotation runs** — examples of source diversity

## Files

- [catalog.yaml](catalog.yaml) — the single source of truth: structured records by entity type, each tagged with usefulness + as-of date
- [discovery-queries.md](discovery-queries.md) — SQL patterns to find new candidates by criteria
- [scenarios.md](scenarios.md) — named end-to-end scenarios with what to demo + which records cover each

## Usefulness taxonomy

Every record in the catalog carries one or more `usefulness:` tags. Use these when picking.

| Tag | Means |
|---|---|
| `onboarding-demo` | A new engineer should see this on day 1 |
| `regression-test` | Has bitten us before; pin it as a test fixture |
| `edge-case` | Exercises a code path most records don't hit |
| `performance-test` | Large or complex enough to expose perf issues |
| `ux-stress` | UX (rendering, layout) tends to break on this |
| `domain-rich` | Scholars find this one inherently interesting |

## "Eager" behavior

When Claude encounters a record during other work that looks novel — a tablet with an unusual ATF pattern, a lemma with no senses, a scholar with 20 merges — this skill prompts to add it:

> Saw an unusual record while working on X. Worth adding to gs-curator-artifacts/catalog.yaml?
> - Entity: artifact P###
> - Why: <one sentence>
> - Suggested usefulness: <tag>

If the user confirms, append to `catalog.yaml` with today's date.

## When this skill runs

- User asks for a sample / test record / demo data
- User says "find me a tablet with…" / "give me an example of…"
- User asks "what's a good Q-number for…"
- A migration adds new tables (this skill should suggest fixtures for them)
- During testing work — link records to tests by name

## Mirror in tests/

`catalog.yaml` mirrors into `tests/fixtures/fixtures.py` as Python constants:

```python
# tests/fixtures/fixtures.py
ONBOARDING_DEMO_LEXICAL = "P227657"  # KTT 188 — Sumerian word list
EDGE_CASE_JOINED_FRAGMENT = "P229672"  # K 03254 + K 03779
ONBOARDING_DEMO_LEMMA = "epsd2/lugal"  # high polysemy, classic
EDGE_CASE_DAMAGED_LINE = ("P229672", 14)  # line 14 is heavily broken
# ...
```

Tests reference these by name. `gs-curator-docs` flags drift between yaml and py.

## When the user wants something not on hand

The skill knows discovery queries (in [discovery-queries.md](discovery-queries.md)) like:

- "Tablet with > 100 lemmatized tokens AND a translation AND > 1 surface"
- "Scholar who edited > 50 ATF texts AND appears as ORACC author"
- "Lemma with sense_count > 10 AND attestation_count > 1000"
- "Sign with no Unicode mapping AND > 100 attestations"

Run the query, propose the best candidate, log to catalog after confirmation.
