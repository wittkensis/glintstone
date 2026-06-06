-- Migration 042: filter_options_cache materialized view
-- Replaces four sequential DISTINCT queries per page load with a single indexed read.
-- Expected: < 5ms vs 2-5s cold.
--
-- Refresh: nightly via ops/cron/refresh_views.sh or after major ingestion runs.
-- Note: genre and language are denormalized here for fast reads; they join through
-- junction tables (artifact_genres/artifact_languages) in the live query path but
-- are pre-aggregated here for performance. Counts reflect all artifacts regardless
-- of active cross-filters (the in-memory TTL cache handles cross-filtered variants).

BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS filter_options_cache AS

SELECT
    'period'             AS dimension,
    period_normalized    AS value,
    COUNT(*)             AS count
FROM artifacts
WHERE period_normalized IS NOT NULL
GROUP BY period_normalized

UNION ALL

SELECT
    'provenience'        AS dimension,
    provenience_normalized AS value,
    COUNT(*)             AS count
FROM artifacts
WHERE provenience_normalized IS NOT NULL
GROUP BY provenience_normalized

UNION ALL

SELECT
    'genre'              AS dimension,
    cg.name              AS value,
    COUNT(*)             AS count
FROM canonical_genres cg
JOIN artifact_genres ag ON ag.genre_id = cg.id
GROUP BY cg.name

UNION ALL

SELECT
    'language'           AS dimension,
    cl.name              AS value,
    COUNT(*)             AS count
FROM canonical_languages cl
JOIN artifact_languages al ON al.language_id = cl.id
GROUP BY cl.name

WITH DATA;

CREATE INDEX IF NOT EXISTS idx_filter_options_cache_dim
    ON filter_options_cache (dimension, value);

GRANT SELECT ON filter_options_cache TO glintstone;

COMMIT;
