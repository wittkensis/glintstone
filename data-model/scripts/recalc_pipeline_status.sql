-- Recalculate pipeline_status scores for all 353k artifacts.
-- Run during off-hours. Each stage takes 30s–2min on 353k rows.
--
-- Schema notes (verified 2026-06-06 against production):
--   - text_lines has p_number directly (no surfaces join needed)
--   - translations table has p_number + translation column
--   - surfaces has NO translation column
--   - artifact_images has p_number column
--
-- Usage (run as wittkensis PG user):
--   psql -U wittkensis -h 127.0.0.1 -d glintstone \
--     -f data-model/scripts/recalc_pipeline_status.sql
--
-- Pre-run snapshot (save for comparison):
--   SELECT ROUND(physical_complete,1), COUNT(*) FROM pipeline_status GROUP BY 1 ORDER BY 1;

-- ── Stage 1: Physical (has at least one image) ────────────────────────────────
BEGIN;
UPDATE pipeline_status ps
SET physical_complete = 1.0
WHERE EXISTS (SELECT 1 FROM artifact_images ai WHERE ai.p_number = ps.p_number);

UPDATE pipeline_status ps
SET physical_complete = 0.0
WHERE NOT EXISTS (SELECT 1 FROM artifact_images ai WHERE ai.p_number = ps.p_number);
COMMIT;

-- ── Stage 2: Reading (has at least one ATF text line) ─────────────────────────
BEGIN;
UPDATE pipeline_status ps
SET reading_complete = 1.0
WHERE EXISTS (SELECT 1 FROM text_lines tl WHERE tl.p_number = ps.p_number);

UPDATE pipeline_status ps
SET reading_complete = 0.0
WHERE NOT EXISTS (SELECT 1 FROM text_lines tl WHERE tl.p_number = ps.p_number);
COMMIT;

-- ── Stage 3: Linguistic (has lemmatizations with citation_form) ───────────────
BEGIN;
UPDATE pipeline_status ps
SET linguistic_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM text_lines tl
    JOIN tokens t ON t.line_id = tl.id
    JOIN lemmatizations lz ON lz.token_id = t.id
    WHERE tl.p_number = ps.p_number
      AND lz.citation_form IS NOT NULL
);

UPDATE pipeline_status ps
SET linguistic_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM text_lines tl
    JOIN tokens t ON t.line_id = tl.id
    JOIN lemmatizations lz ON lz.token_id = t.id
    WHERE tl.p_number = ps.p_number
      AND lz.citation_form IS NOT NULL
);
COMMIT;

-- ── Stage 4: Semantic (has at least one translation) ─────────────────────────
BEGIN;
UPDATE pipeline_status ps
SET semantic_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM translations tr
    WHERE tr.p_number = ps.p_number
      AND tr.translation IS NOT NULL
      AND tr.translation != ''
);

UPDATE pipeline_status ps
SET semantic_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM translations tr
    WHERE tr.p_number = ps.p_number
      AND tr.translation IS NOT NULL
      AND tr.translation != ''
);
UPDATE pipeline_status SET last_updated = NOW();
COMMIT;

-- ── Post-run validation ───────────────────────────────────────────────────────
-- SELECT
--   SUM(CASE WHEN physical_complete  > 0 THEN 1 ELSE 0 END) AS with_images,
--   SUM(CASE WHEN reading_complete   > 0 THEN 1 ELSE 0 END) AS with_atf,
--   SUM(CASE WHEN linguistic_complete > 0 THEN 1 ELSE 0 END) AS with_lemmas,
--   SUM(CASE WHEN semantic_complete  > 0 THEN 1 ELSE 0 END) AS with_translation
-- FROM pipeline_status;
-- Expected: ~8180 | ~101466 | ~497 | ~2492
