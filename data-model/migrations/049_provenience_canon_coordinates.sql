-- Migration 049: Add latitude/longitude to provenience_canon
--
-- The map program (issues #197-#199) needs to place each canonical
-- provenience (ancient find-spot) on a map. provenience_canon already carries
-- ancient_name / modern_name / pleiades_id, but has no coordinate columns.
--
-- This migration adds two nullable double-precision columns. They are filled
-- out-of-band by the one-time enrichment script
--   ops/scripts/geocode_provenience.py
-- which joins each row to the public Pleiades gazetteer (a single bulk CSV
-- fetch, NOT per-row API calls) and writes reprLat/reprLong. Rows that cannot
-- be matched stay NULL; the map simply omits them.
--
-- Nullable on purpose: most rows will be matched, but ~half of the canonical
-- proveniences are "uncertain" ancient places with no known modern location,
-- so coordinates are best-effort, not a NOT NULL contract.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS makes a re-run a no-op. The table is
-- owned by wittkensis; the app connects as glintstone and already holds
-- SELECT on the table (it is a lookup table seeded by ingestion), so no new
-- GRANT is required for the read path. The enrichment script connects as
-- wittkensis (the owner) to perform the UPDATE.

BEGIN;

ALTER TABLE provenience_canon
    ADD COLUMN IF NOT EXISTS latitude  DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

COMMENT ON COLUMN provenience_canon.latitude IS
    'Best-effort decimal latitude of the find-spot, from the Pleiades '
    'gazetteer (reprLat). NULL when the site could not be located. '
    'Populated by ops/scripts/geocode_provenience.py (issue #196).';

COMMENT ON COLUMN provenience_canon.longitude IS
    'Best-effort decimal longitude of the find-spot, from the Pleiades '
    'gazetteer (reprLong). NULL when the site could not be located. '
    'Populated by ops/scripts/geocode_provenience.py (issue #196).';

COMMIT;
