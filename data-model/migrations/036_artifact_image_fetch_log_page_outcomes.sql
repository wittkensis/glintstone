-- 036: widen artifact_image_fetch_log.outcome check constraint
--
-- The image crawler now records PAGE-level skip outcomes (the artifact-page
-- fetch, not an image binary) so that re-runs short-circuit known-bad
-- P-numbers. Three new outcomes are added:
--   page_404         — cdli.earth/<P> returned 404
--   page_no_images   — page returned 200 but the manifest had zero images
--   page_http_error  — any other non-200 (5xx, redirects gone wrong, etc.)
--
-- These coexist with the existing image-binary outcomes (success, http_404,
-- http_5xx, timeout, decode_failed, rate_limited, other_error). The
-- candidates() query in ops/scripts/cdli_image_crawler.py filters by the
-- page_* values; the backfill script ignores them (it only targets
-- image-binary failures).
--
-- The constraint is widened via DROP + ADD because PostgreSQL has no
-- in-place CHECK modification. Both happen in a single transaction so
-- the column is never unconstrained.

BEGIN;

ALTER TABLE artifact_image_fetch_log
    DROP CONSTRAINT IF EXISTS artifact_image_fetch_log_outcome_check;

ALTER TABLE artifact_image_fetch_log
    ADD CONSTRAINT artifact_image_fetch_log_outcome_check
    CHECK (outcome IN (
        -- image-binary fetch outcomes (existing)
        'success',
        'http_404',
        'http_5xx',
        'timeout',
        'decode_failed',
        'rate_limited',
        'other_error',
        -- page-level fetch outcomes (new)
        'page_404',
        'page_no_images',
        'page_http_error'
    ));

COMMIT;
