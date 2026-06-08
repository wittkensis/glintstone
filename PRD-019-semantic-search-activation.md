---
question: "Can I find tablets by meaning, not just by exact word match?"
created: 2026-06-07
modified: 2026-06-07
context: "Generated from a full code audit of core/agent/search_engine.py + core/agent/voyage_client.py on 2026-06-07. The retrieval infrastructure is complete; the data pipeline to populate it is not."
status: active
audience: [eric]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic, gs-expert-data-model, gs-expert-deployment]
supersedes: null
superseded_by: null
---

# PRD-019 — Semantic Search: Activation

## Harness fingerprint
| Field | Value |
|-------|-------|
| PRD template | PRD-agentic v1.0 |
| Authored | 2026-06-07 |
| Embedding model | `voyage-3-large` (1024-dim) via Voyage AI API |
| Query mode | hybrid (lexical + semantic + RRF k=60) |

---

## 1. North star

**Job: Triage.** "Show me tablets related to agricultural contracts from the Old Babylonian period" — the kind of query a scholar types in natural language, where exact string match finds nothing but semantic similarity finds many. Semantic search turns the global-search drawer from a fuzzy autocomplete into a genuine research tool.

---

## 2. What Is Already Built (audit 2026-06-07)

| Component | File | State |
|-----------|------|-------|
| Hybrid search engine | `core/agent/search_engine.py` → `SearchEngine` | Done |
| Voyage client | `core/agent/voyage_client.py` → `VoyageClient` | Done |
| Lexical retrieval | `_lexical_search` (pg_trgm + tsvector) | Done |
| Semantic retrieval | `_semantic_search` (pgvector cosine + HNSW index) | Done |
| RRF fusion | `_rrf` (k=60) | Done |
| Graceful degradation | Falls back to lexical-only if Voyage unavailable | Done |
| In-process query cache | 5-minute TTL, keyed on (query, mode) | Done |
| Retry with backoff | Voyage retries: 5x with exponential delay, max 30s | Done |
| Entity types | tablets, scholars, lemmas, compositions | Done |
| Search API route | `GET /api/v2/search?q=…&mode=hybrid` | Done |
| Global search frontend | `app/static/js/global-search.js` | Done |

---

## 3. The Gaps

### Gap 1 — `entity_embeddings` table is likely empty (CRITICAL)

The search engine queries `entity_embeddings` for cosine-similar results. If the table is empty, `_semantic_search` returns zero results for every query. The RRF fusion then returns only lexical results — the behavior is correct but the semantic feature doesn't exist.

There is no confirmed backfill in the codebase. `voyage_client.py` has a `filter_unchanged` helper for dedup (to skip re-embedding unchanged texts), but no CLI backfill script was found in the audit.

**What to do:**
1. On VPS: `psql -U glintstone glintstone -c "SELECT entity_type, COUNT(*) FROM entity_embeddings GROUP BY entity_type;"` — if this returns zero rows, backfill hasn't run.
2. Find or write a backfill script. The highest-value targets are **tablets** (353k rows — embed the designation + period + genre concatenation) and **lexical lemmas** (346k rows — embed the guide word + sense). Scholars and compositions are smaller and lower priority.
3. The backfill will take hours. Run as `wittkensis` on the VPS, not as `glintstone`. Batch size 128 (Voyage's limit). Estimate: ~2,800 batches for tablets at 128/batch.

### Gap 2 — VOYAGE_API_KEY not confirmed on VPS (HIGH)

`VoyageClient.__init__` falls back to `ANTHROPIC_API_KEY` if `VOYAGE_API_KEY` is not set:
```python
self.api_key = (
    api_key
    or os.environ.get("VOYAGE_API_KEY")
    or os.environ.get("ANTHROPIC_API_KEY")  # fallback
)
```

This fallback is wrong — the Anthropic key won't authenticate against the Voyage API. The result is a `RuntimeError` that propagates to `_get_voyage()` in `agent_service.py`, which catches and logs it, then degrades to lexical-only. So it fails silently: queries work but never use semantic results.

**Fix:** Add `VOYAGE_API_KEY` to the VPS `.env`. Get the key from the Voyage AI console. Note that Voyage AI is now Anthropic-affiliated but still uses its own key management.

### Gap 3 — No UI signal for semantic mode (LOW)

When a query uses hybrid mode and semantic results surface tablets that wouldn't appear in a pure string search, there's no indicator. The scholar has no way to know why a result appeared or whether to trust it.

This is low priority for MVP but important for scholarly trust. A small "semantic match" label on search results that ranked higher in the semantic component than the lexical component would help.

### Gap 4 — Composition embeddings may not have usable text (MEDIUM)

`SearchEngine.embedding_type_map` includes `"compositions"` mapped to `"composite_designation"`. If the `composite_designation` column in `entity_embeddings` is short (just the CDLI Q-number or a title like "Gilgamesh") it won't embed meaningfully. The embedding text for compositions should include the genre, period, and a brief description to make semantic similarity useful.

---

## 4. What "semantic text" should be embedded per entity type

The text fed to Voyage at index time determines what semantic similarity means. These are recommendations for the backfill.

| Entity type | Recommended embedding text | Example |
|-------------|---------------------------|---------|
| Tablets | `"{designation}. {period}. {genre}. {provenience}."` | "BM 017152. Old Babylonian. administrative. Nippur." |
| Lexical lemmas | `"{guide_word} ({pos}): {primary_sense}"` | "king (N): person who rules" |
| Scholars | `"{full_name}. {institution}. {specialization if available}"` | "Niek Veldhuis. UC Berkeley." |
| Compositions | `"{title}. {genre}. {period}. {canonical_language}."` | "Hymn to Inana. literary. Old Babylonian. Sumerian." |

---

## 5. Implementation sequence

### Phase A — Verify current state

1. SSH to VPS.
2. Check `entity_embeddings` counts:
   ```sql
   SELECT entity_type, COUNT(*) FROM entity_embeddings GROUP BY entity_type;
   ```
3. Check `VOYAGE_API_KEY` in `.env`. If missing, get from Voyage console and add.
4. Test degraded-only path: `curl "http://localhost:8001/api/v2/search?q=grain+distribution&mode=hybrid"` — if it returns results quickly with no errors, the engine is running (even if only lexically).

### Phase B — Write the backfill script

5. Create `scripts/backfill_embeddings.py`:
   - Accept `--entity-type` (tablets | lemmas | scholars | compositions)
   - Accept `--limit` for partial runs
   - Query the relevant table for text candidates
   - Call `VoyageClient.embed()` in batches of 128
   - Use `filter_unchanged` to skip already-embedded rows (compare sha256)
   - Insert into `entity_embeddings(entity_type, entity_id, model, source_hash, embedding)` with `ON CONFLICT DO UPDATE`
   - Print progress: N embedded, M skipped (unchanged), K failed

6. Run on VPS for scholars first (20k rows, ~2 min) as a smoke test. Then lemmas (346k, ~30 min). Then tablets (353k, ~45 min with rate limiting).

7. After backfill, re-run the search curl. Results should now include semantic hits (you'll see tablets that don't match the literal query string).

### Phase C — UI signal (post-MVP, optional)

8. In `global_search_results.html`, add a small "≈ semantic" badge on result rows where `score` is significantly above the lexical floor (threshold TBD empirically, something like `score > 0.4`).

---

## 6. Done criteria

- [ ] VPS: `entity_embeddings` has rows for tablets (>100k), lemmas (>100k)
- [ ] VPS: `VOYAGE_API_KEY` confirmed set and valid
- [ ] Smoke test: `GET /api/v2/search?q=agricultural+administration` returns tablet results that include tablets without those literal words in their designation
- [ ] Backfill script exists at `scripts/backfill_embeddings.py` with `--entity-type` and `--limit` flags
- [ ] Degradation verified: removing `VOYAGE_API_KEY` causes fallback to lexical-only with no HTTP error to the client

---

## 7. Out of scope for this PRD

- Changing the embedding text format after initial backfill (requires re-embed)
- MCP-exposed semantic search tool (future)
- Semantic snippets in the global-search drawer (PRD-agentic-translation.md covers this for tablets)
- Embedding image features via CLIP or similar (post-MVP)
