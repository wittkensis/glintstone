-- Migration 040: Add raw_form to tokens and backfill from token_readings
--
-- tokens.raw_form was referenced by core/agent/fact_assembly.py but was
-- never added to the schema. The surface form of a token (its ATF reading)
-- lives in token_readings.form. This migration:
--   1. Adds a nullable raw_form TEXT column to tokens.
--   2. Backfills from the consensus token_reading (is_consensus = 1),
--      falling back to the first reading for tokens without a consensus flag.
--   3. Leaves raw_form NULL for tokens with no readings at all (pipeline
--      stages < Transcribed).
--   4. Grants SELECT to glintstone.

BEGIN;

ALTER TABLE tokens ADD COLUMN IF NOT EXISTS raw_form TEXT;

-- Backfill from consensus reading where available
UPDATE tokens t
SET raw_form = tr.form
FROM token_readings tr
WHERE tr.token_id = t.id
  AND tr.is_consensus = 1
  AND t.raw_form IS NULL;

-- Backfill from any reading for tokens that still have none
UPDATE tokens t
SET raw_form = tr.form
FROM (
    SELECT DISTINCT ON (token_id) token_id, form
    FROM token_readings
    ORDER BY token_id, id
) tr
WHERE tr.token_id = t.id
  AND t.raw_form IS NULL;

GRANT SELECT ON tokens TO glintstone;

COMMIT;
