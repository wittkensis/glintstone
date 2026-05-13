---
question: "How is every interaction recorded, what invalidates a persisted summary, and how does the system learn from user corrections?"
created: 2026-05-12
modified: 2026-05-12
context: "Owns the schema and semantics of agent_interactions, interaction_feedback, and agent_outputs. The learning loop is what makes the agentic surface improve over time. Without it, we'd just be calling Claude in a loop."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Learning loop

The system records every interaction and joins them to outcomes. Corrections from scholars become first-class annotations. No surface, no MCP tool, no REST route bypasses this.

## Three tables (migration 025)

### `agent_interactions`

Every call. Cheap to write, queryable.

```sql
CREATE TABLE agent_interactions (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID NOT NULL,                  -- groups multi-turn agent conversations
    surface         TEXT NOT NULL,                  -- 'api' | 'mcp' | 'web' | 'debug'
    tool_name       TEXT,                           -- 'semantic_search' | 'summarize_artifact' | …; null for direct REST
    route_path      TEXT,                           -- '/search' | '/artifacts/{p}/summary' | …; null for MCP
    request         JSONB NOT NULL,                 -- full args (Pydantic-serialized)
    response_summary JSONB,                         -- ToolResponse.summary + sources count; full data NOT stored here
    result_ids      TEXT[] NOT NULL DEFAULT '{}',   -- canonical refs: P-numbers, lemma_ids, etc.
    latency_ms      INTEGER NOT NULL,
    error_code      TEXT,                           -- null on success
    client_label    TEXT,                           -- opt-in; default anonymous session uuid
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_agent_interactions_session ON agent_interactions(session_id, created_at);
CREATE INDEX idx_agent_interactions_tool    ON agent_interactions(tool_name, created_at);
CREATE INDEX idx_agent_interactions_result_ids ON agent_interactions USING GIN(result_ids);

GRANT SELECT, INSERT ON agent_interactions TO glintstone;
GRANT USAGE ON SEQUENCE agent_interactions_id_seq TO glintstone;
```

**Why `result_ids` denormalized:** so we can ask "which queries returned this P-number" without parsing the response JSONB. Critical for retrieval-quality dashboards.

**Privacy:** `client_label` is opt-in (`?client=fatima@bm.org` or MCP env var `GS_CLIENT_LABEL`). Default: anonymous session UUID. No IP logging, no fingerprinting.

### `interaction_feedback`

Outcomes. Joined to interactions, not stored inline (interactions are append-only and cheap; feedback is rare and possibly multi-row).

```sql
CREATE TABLE interaction_feedback (
    id              BIGSERIAL PRIMARY KEY,
    interaction_id  BIGINT NOT NULL REFERENCES agent_interactions(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,                  -- 'explicit_rating' | 'implicit_click' | 'correction' | 'citation_followup'
    payload         JSONB NOT NULL,                 -- shape depends on kind; see below
    scholar_id      INTEGER REFERENCES scholars(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_interaction_feedback_kind ON interaction_feedback(kind, created_at);
CREATE INDEX idx_interaction_feedback_scholar ON interaction_feedback(scholar_id) WHERE scholar_id IS NOT NULL;

GRANT SELECT, INSERT ON interaction_feedback TO glintstone;
GRANT USAGE ON SEQUENCE interaction_feedback_id_seq TO glintstone;
```

**`kind` payload shapes:**

| kind | payload example |
|---|---|
| `explicit_rating` | `{"score": 4, "max": 5, "comment": "missed the Šulgi connection"}` |
| `implicit_click` | `{"clicked_result_id": "P227657", "rank": 2}` |
| `correction` | `{"original_claim": "Ur III", "corrected_claim": "OB", "new_annotation_run_id": 4471}` |
| `citation_followup` | `{"citation_n": 3, "source_id": 4471, "action": "viewed_chain"}` |

### `agent_outputs`

Lazy-persisted generated text. Tablet view loads, never pre-baked.

```sql
CREATE TABLE agent_outputs (
    id              BIGSERIAL PRIMARY KEY,
    interaction_id  BIGINT REFERENCES agent_interactions(id),  -- creator
    output_type     TEXT NOT NULL,                  -- 'artifact_summary' | 'token_interpretation'
    target_type     TEXT NOT NULL,                  -- 'artifact' | 'token'
    target_id       TEXT NOT NULL,                  -- p_number or token_id-as-string
    focus           TEXT,                           -- 'general' | 'research' | 'translation_status' — null for token_interpretation
    model           TEXT NOT NULL,                  -- 'claude-sonnet-4-6'
    prompt_version  TEXT NOT NULL,                  -- filename: 'synthesis.v1' | 'interpret-token.v1'
    output_text     TEXT NOT NULL,                  -- text with [n] markers preserved
    citations       JSONB NOT NULL,                 -- list[Citation]
    source_run_ids  INTEGER[] NOT NULL DEFAULT '{}',-- denormalized from citations for invalidation
    best_guess_flag BOOLEAN NOT NULL DEFAULT false,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    superseded_at   TIMESTAMPTZ                     -- set when a newer annotation_run targets this row
);

CREATE UNIQUE INDEX uq_agent_outputs_target
    ON agent_outputs(target_type, target_id, output_type, COALESCE(focus, ''), prompt_version)
    WHERE superseded_at IS NULL;

CREATE INDEX idx_agent_outputs_source_runs ON agent_outputs USING GIN(source_run_ids);

GRANT SELECT, INSERT, UPDATE ON agent_outputs TO glintstone;
GRANT USAGE ON SEQUENCE agent_outputs_id_seq TO glintstone;
```

**The unique index** is partial — only enforces uniqueness on non-superseded rows. Lets us keep history while ensuring "fresh" is unambiguous.

## Invalidation

A persisted summary becomes stale when any annotation it cites changes.

**Sweep query** (run on annotation_run insert, or nightly catch-all):

```sql
UPDATE agent_outputs
SET superseded_at = now()
WHERE superseded_at IS NULL
  AND EXISTS (
      SELECT 1 FROM annotation_runs ar_new
      WHERE ar_new.id = ANY(agent_outputs.source_run_ids)
        AND EXISTS (
            SELECT 1 FROM annotation_runs ar_newer
            WHERE ar_newer.source_name = ar_new.source_name
              AND ar_newer.created_at > ar_new.created_at
              AND ar_newer.id NOT IN (SELECT unnest(agent_outputs.source_run_ids))
        )
  );
```

**Inline trigger** (decided later — for v1 we just run the sweep on demand from the route that lazy-loads the summary). Pros of trigger: real-time. Cons: write-amplification on annotation_runs (a hot table).

**v1 approach:** the lazy-load path checks `WHERE superseded_at IS NULL` AND `generated_at > NOW() - INTERVAL '30 days'`. If superseded OR > 30 days old → regenerate. The 30-day TTL is a safety net for the case where supersession detection lags.

## Corrections → annotations

When a scholar corrects an agent's claim:

```
1. Scholar uses debug UI / API:
     POST /api/v2/agentic/corrections
     {
       "interaction_id": 4471,
       "claim": "lemma:8841 → 'king'",
       "correction": "should be 'shepherd'",
       "scholar_id": 12,
       "evidence": "CAD Š/2 p. 318"
     }

2. Server side:
     a. Insert into interaction_feedback (kind='correction')
     b. Create a new annotation_runs row:
          source_name = 'user-correction'
          method      = 'agent-hypothesis-correction'
          scholar_id  = 12
     c. Insert into lemmatization_decisions (or appropriate decision table)
        with the correction, linked to that annotation_run

3. The agent_output that contained the bad claim is left alone (it's history).
   Next request for the same target sees the new annotation_run, marks the
   old output superseded, regenerates.
```

This is the elegant part. **A correction is not a side-channel feedback signal.** It's a normal annotation with `method='agent-hypothesis-correction'`. It goes through the same trust infrastructure as any other scholarly correction. Future Fatima sees both readings via `unified_provenance`.

## New `annotation_runs.method` values

Migration 025 adds (via INSERT, since `annotation_runs.method` is text not enum):

- `agent-hypothesis` — a hypothesis generated by `interpret_token`
- `agent-summary` — a synthesis generated by `summarize_artifact`
- `agent-hypothesis-correction` — a scholar corrected an agent hypothesis
- `user-correction` — a scholar corrected another scholar's annotation (not agent-mediated)

These are stored as plain text; no schema migration needed beyond an INSERT into the `annotation_runs_method` view if it's enumerable, or just convention if it's free-form. Confirm in migration 025.

## Retention

Indefinite. The math:
- 1 KB/row × even 100k interactions/month = 100 MB/year
- 4 KB/row × 10k outputs/month = 500 MB/year

Trivial. If we ever exceed this, we roll older rows into a `agent_interactions_archive` table with the same shape but on cheaper storage. Schema doesn't need to change.

## Litmus tests

1. Every successful tool call appears in `agent_interactions` within 100 ms.
2. `agent_outputs` row exists after first `summarize_artifact` call; second call hits it (< 200 ms).
3. Insert a new `annotation_runs` row for an artifact; call `summarize_artifact` again → regenerates.
4. POST a correction to the agentic corrections endpoint → row appears in `interaction_feedback` AND new `annotation_runs` row exists AND old `agent_outputs` row marked superseded.
5. Query `SELECT result_ids FROM agent_interactions WHERE result_ids @> ARRAY['P227657']` returns every interaction that surfaced P227657.
6. `client_label` is null in `agent_interactions` for an MCP call with no env var set.
