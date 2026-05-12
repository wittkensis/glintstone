---
name: gs-scout-integrations
description: Outside-view scout for new external resources — HuggingFace models, datasets, APIs, papers, corpora. Outputs a fit / path / sketch / placement / risks brief. Use when the user surfaces something new and asks "could we use this?".
metadata:
  question: "Someone surfaced a new HuggingFace model / dataset / API / corpus. How would it fit Glintstone, and what's the integration path?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Created during the 2026-05-11 overhaul to replace ad-hoc evaluation of new external resources with a structured framework. Pairs with gs-expert-integrations (the inside-view sibling that builds connectors once we've decided to integrate)."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#11", "#12", "#27"]
  related_skills: [gs-expert-integrations, gs-expert-assyriology, gs-expert-data-model, gs-expert-ui]
  supersedes: null
  superseded_by: null
  triggers: [huggingface, "hugging face", "hf model", "new model", "new dataset", "should we use", "should we integrate", "new corpus", "new ORACC project", "new API", "this paper has a model", lemmatizer, "sign detection", "translation model"]
---

# Scout new integrations

The outside-view companion to `gs-expert-integrations`. That skill builds connectors against the framework once we've decided. THIS skill evaluates whether we should.

## When to load which file

| Question | File |
|---|---|
| What integration pattern fits — data-source, ML model, API, reference data? | [patterns.md](patterns.md) |
| Where would this have most impact today (which gap does it close)? | [gap-analysis.md](gap-analysis.md) |
| Where in the UI would this surface? | [ui-surfaces.md](ui-surfaces.md) |
| Worked examples — the 5 HF candidates I was asked to evaluate | [worked-examples.md](worked-examples.md) |

## Output template

Every "should we integrate X?" question gets answered in five sections. Even short evaluations follow this shape.

### 1. Fit

What gap does this close? Cross-reference [gap-analysis.md](gap-analysis.md). If it closes nothing, say so plainly — novelty isn't a reason.

### 2. Integration path

One of:

- **Ingestion connector** — bulk data ingest into Postgres. New file in `ingestion/connectors/`.
- **ML model** — runtime inference. New module in `ml/service/`.
- **External API** — live query, not bulk import. Add a service wrapper in `api/services/`.
- **Reference data** — small static lookup (taxonomy, code list). Add via the lookup-tables connector.
- **Don't integrate** — interesting but not for us. Say why.

### 3. Sketch

- Connector skeleton (if data-source)
- Service stub (if ML model)
- Endpoint outline (if API)
- Migration outline (if reference data)

Just enough to know the shape — actual code is `gs-expert-integrations`'s job.

### 4. UI placement

Which surface(s) would expose this? Cross-reference [ui-surfaces.md](ui-surfaces.md). If no UI placement makes sense, say so — back-end-only is fine but flag it.

### 5. Risks

Always include:

- **License** — does it match our CC BY-SA 4.0 distribution? (CC0, CC BY, CC BY-SA, Apache 2.0, MIT all compatible; research-only or non-commercial often not)
- **Freshness** — how often does upstream update?
- **Attribution** — every ingested row gets an `annotation_run_id`; ensure the source name + version is recordable
- **Contested knowledge** — if the model produces opinions (lemmatization, dating, attribution), can we store competing analyses?

## Triggers — when this skill activates

- User pastes a HuggingFace URL
- User mentions a paper / model / dataset by name
- User asks "should we use…" / "is there a model that…"
- User mentions a new ORACC subproject, new museum collection, new resource

## How to use the framework

1. **Read the upstream**: model card, dataset card, paper abstract, license file
2. **Sketch the path** using [patterns.md](patterns.md)
3. **Check the gap** using [gap-analysis.md](gap-analysis.md)
4. **Place in UI** using [ui-surfaces.md](ui-surfaces.md)
5. **Score risks** using the checklist above
6. **Output the 5-section brief**

If the user wants to proceed: hand off to `gs-expert-integrations` for the actual connector work.
