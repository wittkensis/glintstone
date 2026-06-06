-- Recalculate pipeline_status scores for all 353k artifacts.
-- Run during off-hours. Expected runtime: 10–30 minutes.
--
-- Usage:
--   PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -p 5432 -U glintstone -d glintstone \
--     -f data-model/scripts/recalc_pipeline_status.sql
--
-- Pre-run snapshot (save for comparison):
--   SELECT ROUND(physical_complete, 1) AS score, COUNT(*) FROM pipeline_status GROUP BY 1 ORDER BY 1;
--
-- Post-run validation: run the queries in PRD-001 §Validation.

BEGIN;

-- ── Stage 1: Physical (has at least one image) ────────────────────────────────
UPDATE pipeline_status ps
SET physical_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM artifact_images ai
    WHERE ai.p_number = ps.p_number
);

UPDATE pipeline_status ps
SET physical_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM artifact_images ai
    WHERE ai.p_number = ps.p_number
);

-- ── Stage 2: Reading (has at least one ATF text line) ─────────────────────────
UPDATE pipeline_status ps
SET reading_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM surfaces s
    JOIN text_lines tl ON tl.surface_id = s.id
    WHERE s.p_number = ps.p_number
);

UPDATE pipeline_status ps
SET reading_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM surfaces s
    JOIN text_lines tl ON tl.surface_id = s.id
    WHERE s.p_number = ps.p_number
);

-- ── Stage 3: Linguistic (has lemmatized tokens with citation_form) ────────────
UPDATE pipeline_status ps
SET linguistic_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM surfaces s
    JOIN text_lines tl ON tl.surface_id = s.id
    JOIN tokens t ON t.line_id = tl.id
    JOIN lemmatizations lz ON lz.token_id = t.id
    WHERE s.p_number = ps.p_number
      AND lz.citation_form IS NOT NULL
);

UPDATE pipeline_status ps
SET linguistic_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM surfaces s
    JOIN text_lines tl ON tl.surface_id = s.id
    JOIN tokens t ON t.line_id = tl.id
    JOIN lemmatizations lz ON lz.token_id = t.id
    WHERE s.p_number = ps.p_number
      AND lz.citation_form IS NOT NULL
);

-- ── Stage 4: Semantic (has at least one translation line) ─────────────────────
-- translation lives on surfaces.translation or in a translations table.
-- Check both patterns.
UPDATE pipeline_status ps
SET semantic_complete = 1.0
WHERE EXISTS (
    SELECT 1 FROM surfaces s
    WHERE s.p_number = ps.p_number
      AND s.translation IS NOT NULL
      AND s.translation != ''
);

UPDATE pipeline_status ps
SET semantic_complete = 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM surfaces s
    WHERE s.p_number = ps.p_number
      AND s.translation IS NOT NULL
      AND s.translation != ''
);

-- ── Refresh last_updated ──────────────────────────────────────────────────────
UPDATE pipeline_status SET last_updated = NOW();

COMMIT;

-- ── Post-run validation ───────────────────────────────────────────────────────
-- Run these queries to verify results before marking PRD-001 done:
--
-- P000001: should have ATF (reading=1.0) but no images (physical=0.0)
-- SELECT physical_complete, reading_complete, linguistic_complete, semantic_complete
-- FROM pipeline_status WHERE p_number = 'P000001';
--
-- Aggregate counts:
-- SELECT
--   SUM(CASE WHEN physical_complete  > 0 THEN 1 ELSE 0 END) AS with_images,
--   SUM(CASE WHEN reading_complete   > 0 THEN 1 ELSE 0 END) AS with_atf,
--   SUM(CASE WHEN linguistic_complete > 0 THEN 1 ELSE 0 END) AS with_lemmas,
--   SUM(CASE WHEN semantic_complete  > 0 THEN 1 ELSE 0 END) AS with_translation
-- FROM pipeline_status;
-- Expected: ~1 | ~101,402 | ~1,687 | ~2,492
