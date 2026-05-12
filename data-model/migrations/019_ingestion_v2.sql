-- Migration 019: Ingestion framework v2
--
-- Replaces file-based JSON checkpoints (`_progress/*.json`) with DB-backed
-- run tracking, granular event logs, dead-letter queue, ML model registry,
-- and a sources catalog with license/citation metadata.
--
-- Tables:
--   sources             — one row per data source (CDLI, ORACC project, model, …)
--   model_registry      — every ML model version (HuggingFace repo, checkpoint, config)
--   import_runs         — one row per connector invocation
--   import_run_events   — granular log lines tied to a run (queryable by run_id)
--   import_dead_letters — every record that failed to integrate; triage queue

-- Idempotent: safe to re-run.

BEGIN;

-- ---------- sources ----------
CREATE TABLE IF NOT EXISTS sources (
    id              TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL,
    description     TEXT,
    kind            TEXT NOT NULL,
    upstream_url    TEXT,
    license         TEXT,
    license_url     TEXT,
    citation        TEXT,
    contact_email   TEXT,
    runs_after      TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sources_kind_check CHECK (
        kind IN ('catalog', 'corpus', 'lexicon', 'model', 'derived', 'annotation', 'lookup')
    )
);

CREATE INDEX IF NOT EXISTS sources_kind_idx ON sources (kind);

-- ---------- model_registry ----------
CREATE TABLE IF NOT EXISTS model_registry (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    hf_repo         TEXT,
    checkpoint_uri  TEXT,
    config_json     JSONB,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT model_registry_name_version_unique UNIQUE (name, version)
);

CREATE INDEX IF NOT EXISTS model_registry_active_idx
    ON model_registry (name) WHERE is_active = TRUE;

-- ---------- import_runs ----------
CREATE TABLE IF NOT EXISTS import_runs (
    id                  BIGSERIAL PRIMARY KEY,
    connector_id        TEXT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    run_mode            TEXT NOT NULL DEFAULT 'full',
    app_env             TEXT NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    status              TEXT NOT NULL DEFAULT 'running',
    source_checksum     TEXT,
    source_fetched_at   TIMESTAMPTZ,
    rows_seen           BIGINT NOT NULL DEFAULT 0,
    rows_inserted       BIGINT NOT NULL DEFAULT 0,
    rows_updated        BIGINT NOT NULL DEFAULT 0,
    rows_skipped        BIGINT NOT NULL DEFAULT 0,
    rows_dead_lettered  BIGINT NOT NULL DEFAULT 0,
    error_summary       TEXT,
    config_json         JSONB,
    model_id            BIGINT REFERENCES model_registry(id) ON DELETE SET NULL,
    git_sha             TEXT,
    duration_ms         BIGINT,
    CONSTRAINT import_runs_status_check CHECK (
        status IN ('running', 'succeeded', 'failed', 'cancelled', 'no_op')
    ),
    CONSTRAINT import_runs_mode_check CHECK (
        run_mode IN ('full', 'incremental', 'range', 'dry_run', 'verify_only')
    )
);

CREATE INDEX IF NOT EXISTS import_runs_connector_started_idx
    ON import_runs (connector_id, started_at DESC);
CREATE INDEX IF NOT EXISTS import_runs_status_idx
    ON import_runs (status);

-- ---------- import_run_events ----------
CREATE TABLE IF NOT EXISTS import_run_events (
    id          BIGSERIAL PRIMARY KEY,
    run_id      BIGINT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level       TEXT NOT NULL,
    message     TEXT NOT NULL,
    context     JSONB,
    CONSTRAINT import_run_events_level_check CHECK (
        level IN ('debug', 'info', 'warn', 'error')
    )
);

CREATE INDEX IF NOT EXISTS import_run_events_run_at_idx
    ON import_run_events (run_id, at);

-- ---------- import_dead_letters ----------
-- Single home for every record that failed to integrate, regardless of why.
-- Replaces ad-hoc disk files like `_progress/19_unmatched_translations.json`,
-- `_progress/unmatched_sign_values.txt`, etc.
--
-- Records are written via the v2 connector framework's DeadLetterSink and
-- carry their original payload as JSONB so they can be inspected, replayed
-- after a fix, or marked wontfix without losing the source data.
CREATE TABLE IF NOT EXISTS import_dead_letters (
    id                 BIGSERIAL PRIMARY KEY,
    run_id             BIGINT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    connector_id       TEXT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    category           TEXT NOT NULL,
    subcategory        TEXT,
    source_key         TEXT,
    payload            JSONB NOT NULL,
    reason             TEXT,
    resolution_status  TEXT NOT NULL DEFAULT 'open',
    resolution_note    TEXT,
    resolved_by        TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at        TIMESTAMPTZ,
    CONSTRAINT import_dead_letters_category_check CHECK (
        category IN ('validation_failed', 'no_match', 'missing_reference',
                     'schema_drift', 'duplicate', 'other')
    ),
    CONSTRAINT import_dead_letters_status_check CHECK (
        resolution_status IN ('open', 'investigating', 'wontfix', 'fixed', 'duplicate')
    )
);

CREATE INDEX IF NOT EXISTS import_dead_letters_triage_idx
    ON import_dead_letters (connector_id, category, resolution_status);
CREATE INDEX IF NOT EXISTS import_dead_letters_run_idx
    ON import_dead_letters (run_id);
CREATE INDEX IF NOT EXISTS import_dead_letters_open_idx
    ON import_dead_letters (resolution_status) WHERE resolution_status = 'open';

-- ---------- helper view ----------
CREATE OR REPLACE VIEW v_ingestion_status AS
SELECT
    s.id                            AS connector_id,
    s.display_name,
    s.kind,
    s.license,
    last_run.id                     AS last_run_id,
    last_run.started_at             AS last_run_at,
    last_run.status                 AS last_run_status,
    last_run.rows_inserted          AS last_run_inserted,
    last_run.rows_dead_lettered     AS last_run_dead_lettered,
    last_run.duration_ms            AS last_run_duration_ms,
    dl.open_count                   AS open_dead_letters
FROM sources s
LEFT JOIN LATERAL (
    SELECT id, started_at, status, rows_inserted, rows_dead_lettered, duration_ms
    FROM import_runs
    WHERE connector_id = s.id
    ORDER BY started_at DESC
    LIMIT 1
) last_run ON TRUE
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS open_count
    FROM import_dead_letters
    WHERE connector_id = s.id AND resolution_status = 'open'
) dl ON TRUE;

COMMIT;
