-- Migration 031: ensure pg_trgm extension is available
--
-- Existing GIN trigram indexes on artifacts.designation and artifacts.p_number
-- (idx_artifacts_pnumber_trgm, idx_artifacts_designation_trgm) require the
-- pg_trgm extension to be installed for ILIKE '%term%' searches to use them.
-- Without the extension, the planner falls back to a sequential scan even
-- though the indexes exist.
--
-- CREATE EXTENSION IF NOT EXISTS is idempotent — safe on environments where
-- it's already present. See issue #83 Phase 4e.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMIT;
