-- Migration 020: Staging schema for v2 connectors
--
-- Connectors land raw rows in `staging_*` tables first, then a follow-up
-- "promotion" connector copies validated rows into canonical tables. This
-- decouples ingestion failures from app-visible data.

BEGIN;

CREATE TABLE IF NOT EXISTS staging_cdli_catalog (
    p_number          TEXT PRIMARY KEY,
    designation       TEXT,
    period_raw        TEXT,
    provenience_raw   TEXT,
    genre_raw         TEXT,
    language_raw      TEXT,
    museum_no         TEXT,
    loaded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS staging_cdli_catalog_loaded_idx
    ON staging_cdli_catalog (loaded_at);

COMMIT;
