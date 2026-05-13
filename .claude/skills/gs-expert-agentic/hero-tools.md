---
question: "What do the three hero tools accept and return, and how do I tell if they're working?"
created: 2026-05-12
modified: 2026-05-12
context: "Owns the contract for semantic_search, summarize_artifact, and interpret_token — the three forcing functions of the agentic architecture. If any of these regresses, push back on the change."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: ["#25", "#55", "#56"]
related_skills: [gs-expert-agentic, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Hero tools — specs and litmus tests

Three tools. The whole agentic surface is justified by them. Every other tool (`find_artifact`, `lookup_lemma`, `walk_token`, …) exists to support these.

---

## 1. `semantic_search`

### REST
```
GET /api/v2/search?q={query}&types={tablets,lemmas,signs,scholars,publications,entities}&limit=5&cursor={opaque}&mode={lexical|semantic|hybrid}
```

### MCP
```python
semantic_search(
    q: str,
    types: list[str] | None = None,            # default: all
    limit: int = 5,                            # per group
    cursor: str | None = None,                 # for View-All
    mode: Literal["lexical", "semantic", "hybrid"] = "hybrid",
    filters: dict | None = None,               # period, provenience, language, genre, pos
) -> ToolResponse[GroupedTablePayload]
```

### Retrieval stack

1. **Exact** — P/Q-number, designation literal, scholar full name. Free, always runs first.
2. **Lexical** — `pg_trgm` similarity on names/forms + `tsvector` rank on translations/glosses/blobs.
3. **Semantic** — Voyage `voyage-3-large` query embedding → pgvector cosine over `entity_embeddings`. Three artifact embedding flavors (translation, lemma_bag, designation) plus lemma glosses, scholar publication blobs, named-entity names.
4. **Fusion** — Reciprocal Rank Fusion (`k=60` default) across the three signals. Sort by RRF score, ties broken by recency, then by ID.

### Litmus tests

| Query | Expected |
|---|---|
| `"gilgamesh"` | ≥ 2 groups non-empty; literary tablets + Gilgameš lemma; scholar group includes Gilgamesh-focused scholars |
| `"P005614"` | First result is exact P-number match, score 1.0; other groups still populated for context |
| `"king"` | Lemmas group has `šarru`, `lugal`; tablets group filtered by ruler designation |
| `"harvest reports from Nippur mentioning silver"` | Admin-genre tablets, Nippur provenience filter applied automatically via filter parser; semantic ranking emphasizes silver/barley lemma_bag |
| `"diplomatic marriage Amarna"` | EA-corpus letters + Amarna-period scholars |
| `"Inanna descent"` | Sumerian literary tablets + Dumuzi-Inanna lemmas + composite Q-numbers |
| `"asdfqwerty"` | All groups empty; `follow_ups: [{tool: "did_you_mean"}]` |
| `"a"` (load) | < 300 ms p95 (lexical-only path) |
| any phrase | < 800 ms p95 (hybrid, includes 1 Voyage query-embedding call) |

### Performance budget

- Lexical-only mode: 300 ms p95
- Hybrid mode: 800 ms p95 (300 ms DB + ~150 ms Voyage embed + ~200 ms RRF + 150 ms render)
- 5-min cached query embedding: subsequent same-q hits drop to lexical-only budget

---

## 2. `summarize_artifact`

### REST
```
GET /api/v2/artifacts/{p_number}/summary?focus={general|research|translation_status}
```

### MCP
```python
summarize_artifact(
    p_number: str,
    focus: Literal["general", "research", "translation_status"] = "general",
) -> ToolResponse[CardPayload]
```

### Behavior

**Lazy-persist.** On call:
1. Load `agent_outputs` row for `(target_type='artifact', target_id=p_number, output_type='artifact_summary', focus=...)`.
2. If row exists AND not superseded AND ≤ 30 days old AND same `prompt_version` → return persisted output.
3. Otherwise generate, insert into `agent_outputs`, return.

**Generation pipeline:**

```
assemble_facts(p_number, focus) →
  1. Catalog facts (period, provenience, genre, language, museum, dimensions)
  2. Pipeline completeness (0-5) from pipeline_completeness view
  3. Importance signals (citation_count, collection membership, composite exemplar)
  4. Top 5 lemmas + top 5 named entities mentioned
  5. Similar tablets (5 nearest by averaged lemma_bag + translation embedding)
  6. If completeness < 3: sign sequence summary (first ~20 signs)
                          → enables best-guess section

→ synthesis call (Claude Sonnet 4.6, see citation-contract.md)
→ validate citations, retry once on failure
→ persist + return
```

### Best-guess gate

```python
if pipeline_completeness <= 2 and len(similar_tablets_above_cosine_0_72) >= 3:
    include_best_guess = True
```

When triggered, the system prompt includes a "(hypothesis)" section instruction; without trigger, that instruction is omitted (cleaner output, smaller prompt).

### Litmus tests

| P-number | Expected |
|---|---|
| `P227657` (well-known, well-attested) | Full card with completeness 4-5; `best_guess` absent; ≥ 4 citations in synthesis; named entities populated |
| `P005614` (some translation) | Card with completeness 3; `synthesis` references translation source; `best_guess` absent |
| Unknown unlemmatized tablet | Card with completeness ≤ 2; `best_guess` populated; phrasing uses "resembles"; ≥ 3 similar_tablets shown |
| Non-existent P-number | 404 with `ToolResponse` envelope; `summary: "No artifact found for P-number X"`, empty `data` |
| Two calls in succession | Second call returns persisted row (`generated_at` from first call); latency < 200 ms |
| After new annotation_run on the artifact | Next call regenerates (superseded_at was set on the old row) |

### Performance budget

- First call (generation): < 3 s
- Persisted-hit: < 200 ms (single SELECT)

---

## 3. `interpret_token`

### REST
```
GET /api/v2/artifacts/{p_number}/tokens/{token_id}/interpret
```

### MCP
```python
interpret_token(
    p_number: str,
    token_id: int,
) -> ToolResponse[ChainPayload]
```

### Behavior

Lazy-persist same as `summarize_artifact`, keyed on `(target_type='token', target_id=str(token_id))`.

### Generation pipeline

```
assemble_token_facts(token_id) →
  1. Token + token_readings (raw form, damage, sign function if known)
  2. Neighbor context — 3 tokens before/after, lemmas where present
  3. Sign hypothesis — for each candidate sign reading, most common lemmas (via lexical_sign_lemma_assoc)
  4. Genre prior — over-represented lemmas in this artifact's genre × period
  5. Surrounding-line lemma_bag — semantic field of the rest of the line if lemmatized

→ synthesis call (Claude Sonnet 4.6, prompt = prompts/interpret-token.v1.md)
→ output is ChainPayload with steps + 1-3 ranked hypotheses
→ validate citations + "resembles" guard rail (regex on output)
→ persist + return
```

### Output guarantees

- Every `ChainStep` has at least one source (factual steps cite annotation_runs; hypothesis steps cite the candidate-reading evidence chain).
- Every `Hypothesis` has `confidence_band ∈ {low, medium, high}` and `evidence_chain: list[str]` describing the inference.
- The synthesis text never says "this token means X". The "resembles X" guard rail is a post-process regex check; if violated, raise `SynthesisGroundingError`.

### Litmus tests

| Input | Expected |
|---|---|
| Lemmatized token (chain is complete) | `chain.steps` walks form → norm → lemma → senses; `hypotheses: null`; every step has sources |
| Unlemmatized token in a partially-lemmatized line | `chain.steps` shows what's known; 1-3 `hypotheses` ranked by confidence; evidence chain references neighbor lemmas |
| Unlemmatized token in fully-unlemmatized tablet | Hypotheses derive from sign-reading + genre prior alone; `confidence_band: "low"` for all |
| Token with no neighbors in line | Graceful degradation: `hypotheses` may be empty list; `summary` says so |
| Claude output contains "this token means" | `SynthesisGroundingError` raised, degraded response returned |
| Two calls in succession | Second call < 200 ms (persisted) |

### Performance budget

- First call: < 3 s
- Persisted-hit: < 200 ms

---

## Cross-cutting guarantees

All three hero tools share:

- **`ToolResponse` envelope** — see [envelope.md](envelope.md)
- **Citation contract** — see [citation-contract.md](citation-contract.md)
- **Learning loop** — every call writes to `agent_interactions`; see [learning-loop.md](learning-loop.md)
- **`sources[]` always populated** — if no scholarly source, then a `computed` SourceRef referencing the model + retrieval method
- **`required_attributions`** — populated whenever an eBL or ORACC source contributed (the schema already tracks `required_attribution` flags on sources)
- **MCP tool definitions auto-derive from these Pydantic types** — when adding a field, the MCP client sees it on next reconnect

## When to extend vs. add a new tool

| Situation | Action |
|---|---|
| New filter on `semantic_search` (e.g. `min_completeness`) | Extend params, add to MCP tool input schema, bump OpenAPI spec |
| New summary focus (e.g. `focus="curator"` for `summarize_artifact`) | Add value to focus enum, add a new prompt under `prompts/`, document here |
| Completely new question type (e.g. "find competing readings") | Add a new leaf tool. Don't bloat the hero tools. |
| Need a new render shape | Add a `RenderHint` value (see [envelope.md](envelope.md)) — public-contract change, decision required in [decisions.md](decisions.md) |
