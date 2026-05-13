-- Migration 025: Agentic foundations
--
-- Establishes the substrate for the agentic surface (MCP + REST):
--   1. Extensions: pg_trgm, vector (pgvector)
--   2. Trigram + tsvector indexes for hybrid lexical search
--   3. entity_embeddings table for Voyage voyage-3-large vectors
--   4. agent_interactions — every call recorded
--   5. interaction_feedback — outcomes (ratings, corrections, click-throughs)
--   6. agent_outputs — lazy-persisted summaries/interpretations with supersession
--
-- See .claude/skills/gs-expert-agentic/learning-loop.md for the schema rationale.
--
-- Tables owned by wittkensis; explicit GRANTs to glintstone (the app role) on
-- every new table and sequence.

BEGIN;

-- ── 1. Extensions ────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ── 2. Trigram indexes for hybrid search ─────────────────────────────────────
-- These accelerate `ILIKE %x%` and `similarity()` queries used by the lexical
-- arm of semantic_search. CONCURRENTLY is not used because migrations run in
-- a transaction; if the locks become a problem at deploy time, split this
-- migration and run the indexes out-of-band.

CREATE INDEX IF NOT EXISTS idx_artifacts_designation_trgm
    ON artifacts USING GIN (designation gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_artifacts_pnumber_trgm
    ON artifacts USING GIN (p_number gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lexical_lemmas_cf_trgm
    ON lexical_lemmas USING GIN (citation_form gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lexical_lemmas_gw_trgm
    ON lexical_lemmas USING GIN (guide_word gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lexical_senses_gloss_trgm
    ON lexical_senses USING GIN (gloss gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_scholars_name_trgm
    ON scholars USING GIN (name gin_trgm_ops);

-- composites.designation may not exist on all deployments; guard the index.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'composites' AND column_name = 'designation'
    ) THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_composites_designation_trgm
                 ON composites USING GIN (designation gin_trgm_ops)';
    END IF;
END $$;

-- ── 3. entity_embeddings ─────────────────────────────────────────────────────
-- One row per (entity_type, entity_id, model). Lets multiple model versions
-- coexist during a re-embedding rollout. Voyage voyage-3-large is 1024-dim.

CREATE TABLE IF NOT EXISTS entity_embeddings (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL,
        -- 'artifact_translation' | 'artifact_lemma_bag' | 'artifact_designation'
        -- | 'lemma_gloss' | 'scholar_blob' | 'named_entity' | 'composite_designation'
    entity_id       TEXT NOT NULL,         -- p_number, lemma_id::text, scholar_id::text, etc.
    model           TEXT NOT NULL,         -- 'voyage-3-large'
    dim             INTEGER NOT NULL,      -- 1024 for voyage-3-large
    vec             vector(1024) NOT NULL,
    source_text     TEXT NOT NULL,         -- the actual text that was embedded
    source_hash     TEXT NOT NULL,         -- sha256 of source_text; skip re-embed if unchanged
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_entity_embeddings
    ON entity_embeddings(entity_type, entity_id, model);

CREATE INDEX IF NOT EXISTS idx_entity_embeddings_hash
    ON entity_embeddings(entity_type, entity_id, source_hash);

-- HNSW index for cosine similarity. m=16, ef_construction=64 are the pgvector
-- defaults; good for ~1M vectors at our scale.
CREATE INDEX IF NOT EXISTS idx_entity_embeddings_vec
    ON entity_embeddings USING hnsw (vec vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

GRANT SELECT, INSERT, UPDATE, DELETE ON entity_embeddings TO glintstone;
GRANT USAGE ON SEQUENCE entity_embeddings_id_seq TO glintstone;

-- ── 4. agent_interactions ────────────────────────────────────────────────────
-- Every call — REST, MCP, web, debug. Append-only.

CREATE TABLE IF NOT EXISTS agent_interactions (
    id                  BIGSERIAL PRIMARY KEY,
    session_id          UUID NOT NULL,
    surface             TEXT NOT NULL,                  -- 'api' | 'mcp' | 'web' | 'debug'
    tool_name           TEXT,                           -- null for direct REST calls
    route_path          TEXT,                           -- null for MCP calls
    request             JSONB NOT NULL,
    response_summary    JSONB,                          -- summary + sources count; not full data
    result_ids          TEXT[] NOT NULL DEFAULT '{}',   -- canonical refs surfaced to the caller
    latency_ms          INTEGER NOT NULL,
    error_code          TEXT,
    client_label        TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_interactions_session
    ON agent_interactions(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_interactions_tool
    ON agent_interactions(tool_name, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_interactions_result_ids
    ON agent_interactions USING GIN(result_ids);

GRANT SELECT, INSERT ON agent_interactions TO glintstone;
GRANT USAGE ON SEQUENCE agent_interactions_id_seq TO glintstone;

-- ── 5. interaction_feedback ─────────────────────────────────────────────────
-- Joined to agent_interactions; rare; possibly multi-row per interaction.

CREATE TABLE IF NOT EXISTS interaction_feedback (
    id              BIGSERIAL PRIMARY KEY,
    interaction_id  BIGINT NOT NULL REFERENCES agent_interactions(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,
        -- 'explicit_rating' | 'implicit_click' | 'correction' | 'citation_followup'
    payload         JSONB NOT NULL,
    scholar_id      INTEGER REFERENCES scholars(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interaction_feedback_kind
    ON interaction_feedback(kind, created_at);

CREATE INDEX IF NOT EXISTS idx_interaction_feedback_scholar
    ON interaction_feedback(scholar_id) WHERE scholar_id IS NOT NULL;

GRANT SELECT, INSERT ON interaction_feedback TO glintstone;
GRANT USAGE ON SEQUENCE interaction_feedback_id_seq TO glintstone;

-- ── 6. agent_outputs ─────────────────────────────────────────────────────────
-- Lazy-persisted generated text. Loaded on tablet view; never pre-baked.
-- The unique index is partial so superseded rows can coexist (history).

CREATE TABLE IF NOT EXISTS agent_outputs (
    id              BIGSERIAL PRIMARY KEY,
    interaction_id  BIGINT REFERENCES agent_interactions(id),
    output_type     TEXT NOT NULL,         -- 'artifact_summary' | 'token_interpretation'
    target_type     TEXT NOT NULL,         -- 'artifact' | 'token'
    target_id       TEXT NOT NULL,         -- p_number or token_id::text
    focus           TEXT,                  -- null for token_interpretation
    model           TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,         -- 'synthesis.v1' | 'interpret-token.v1'
    output_text     TEXT NOT NULL,         -- text with [n] markers preserved
    citations       JSONB NOT NULL,        -- list[Citation]
    source_run_ids  INTEGER[] NOT NULL DEFAULT '{}',
    best_guess_flag BOOLEAN NOT NULL DEFAULT false,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    superseded_at   TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_outputs_target
    ON agent_outputs(target_type, target_id, output_type, COALESCE(focus, ''), prompt_version)
    WHERE superseded_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_agent_outputs_source_runs
    ON agent_outputs USING GIN(source_run_ids);

CREATE INDEX IF NOT EXISTS idx_agent_outputs_generated
    ON agent_outputs(generated_at DESC) WHERE superseded_at IS NULL;

GRANT SELECT, INSERT, UPDATE ON agent_outputs TO glintstone;
GRANT USAGE ON SEQUENCE agent_outputs_id_seq TO glintstone;

-- ── 7. annotation_runs method seed values ────────────────────────────────────
-- annotation_runs.method is a free-text column on this schema; we just need
-- to be sure no CHECK constraint rejects the new values. (If a method
-- vocabulary table exists, seed it here.)

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'annotation_runs_method'
    ) THEN
        -- vocab table exists; seed new values idempotently
        INSERT INTO annotation_runs_method (method, description)
        VALUES
            ('agent-hypothesis',            'Hypothesis generated by interpret_token'),
            ('agent-summary',               'Synthesis generated by summarize_artifact'),
            ('agent-hypothesis-correction', 'Scholar correction of an agent hypothesis'),
            ('user-correction',             'Scholar correction of another scholar''s annotation')
        ON CONFLICT (method) DO NOTHING;
    END IF;
END $$;

COMMIT;
