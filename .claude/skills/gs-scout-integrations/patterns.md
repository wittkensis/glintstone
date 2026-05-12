---
question: "How do the four integration paths (data source, ML model, API, reference data) actually work in Glintstone?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. The four patterns map cleanly to existing code surfaces — most decisions reduce to picking the right one."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-scout-integrations, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# Integration patterns

Four patterns cover every external resource we might integrate.

## 1. Ingestion connector (bulk data → Postgres)

When the upstream provides bulk-downloadable structured data, write a connector. Examples: CDLI catalog, ORACC glossaries, a new museum's tablet inventory.

- Lives in: `ingestion/connectors/<slug>.py`
- Subclass: `SourceConnector`
- Triggered by: `python -m ingestion.cli run <id>`
- See: `gs-expert-integrations/framework.md`

**Choose this when**: the data is finite (~thousands to millions of rows), changes on a known cadence (weekly to yearly), and benefits from Postgres queries.

## 2. ML model (runtime inference → API endpoint)

When the upstream is a model that takes inputs and produces predictions. Examples: BabyLemmatizer, sign detection (DETR), a new translation model.

- Lives in: `ml/service/<slug>/`
- Pattern:
  - `inference.py` — loads model, exposes `predict(input) -> output`
  - `routes.py` — API endpoints under `/api/ml/<slug>/`
  - `cache.py` — optional, cache predictions by input hash
- Deployment: usually Modal or similar — see `ml/service/deploy/MODAL_DEPLOYMENT.md`

**Choose this when**: input is per-request (one tablet, one image, one token), output is a prediction (potentially competing analyses), and value comes from on-demand application rather than pre-computed bulk ingestion.

## 3. External API (live query)

When the upstream provides a queryable API and we don't need to bulk-cache. Examples: OpenAlex enrichment, Pleiades geo lookup, eBL bibliography.

- Lives in: `api/services/<slug>_service.py`
- Pattern:
  - Thin httpx wrapper with retry + rate-limit handling
  - In-process LRU cache for hot queries
  - Optional persistence into a `staging_<slug>` table for offline analysis

**Choose this when**: data updates frequently, query patterns are sparse (we don't need it all), or upstream license requires live attribution.

## 4. Reference data (small static lookup)

When the upstream is a small taxonomy or code list. Examples: ISO 639-3 language codes, ORACC POS codes, new genre canonical mappings.

- Lives in: extending `ingestion/connectors/lookup_tables.py` to seed a new table
- Migration adds the table; the connector seeds it

**Choose this when**: under ~1000 rows, changes rarely (years), and used as a join target.

## Decision tree

```
Is it bulk data with structure?
├── Yes → Pattern 1 (connector)
└── No: is it a model with predict() shape?
    ├── Yes → Pattern 2 (ML service)
    └── No: is it a queryable API?
        ├── Yes → Pattern 3 (live service)
        └── No: is it a small lookup?
            ├── Yes → Pattern 4 (reference data)
            └── No: don't integrate. (Or you misread the upstream.)
```

## Common pattern combinations

- **Model + ingestion**: BabyLemmatizer runs as Pattern 2 (live inference) but its outputs are also bulk-imported (Pattern 1) via `baby_lemmatizer.py` for tablets we've pre-processed.
- **API + reference**: OpenAlex serves Pattern 3 for live enrichment, but its "topics" taxonomy is seeded as Pattern 4 once.
- **Connector + API**: ORACC is Pattern 1 (bulk JSON ZIPs) for corpus data, but per-text credits may eventually need Pattern 3 (live).

## License flowchart

```
Upstream license
├── CC0 → integrate freely
├── CC BY → integrate, surface attribution
├── CC BY-SA → integrate, surface attribution, our output is also CC BY-SA
├── Apache 2.0 / MIT → integrate (code)
├── Research-only / non-commercial → STOP. Not compatible with CC BY-SA distribution.
└── Custom license → read it. If it permits derivative academic distribution, proceed; else stop.
```

## When in doubt

Sketch the connector skeleton anyway — actually writing the `extract()` signature usually clarifies whether the data is "bulk" or "stream" or "lookup". Then bring in `gs-expert-integrations` for the build.
