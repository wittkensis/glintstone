-- Migration 030: indexes on junction-table p_number columns
--
-- Every genre/language filter and every cross-filter count runs a correlated
-- EXISTS subquery joining on p_number. Without an index, PostgreSQL falls back
-- to a sequential scan of artifact_genres (~600K rows) and artifact_languages
-- for every filtered query against the 353K-row artifacts table.
--
-- See issue #83 Phase 1a.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_ag_p_number ON artifact_genres(p_number);
CREATE INDEX IF NOT EXISTS idx_al_p_number ON artifact_languages(p_number);

COMMIT;
