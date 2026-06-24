-- Migration 059: Index translations(line_id)
--
-- Adds the missing foreign-key index on translations.line_id. Companion to
-- migration 058; both come from the 2026-06-23 speed audit (PERSONAL/
-- execution/glintstone-speed-audit-2026-06-23.md, QW-2).
--
-- Root cause: `_hydrate_tablet_extras` (core/agent/pipeline_completeness.py,
-- _HAS_TRANSLATION) does, per result tablet:
--
--     EXISTS (SELECT 1 FROM text_lines tl
--             JOIN translations tn ON tn.line_id = tl.id
--             WHERE tl.p_number = {p})
--
-- With no index on translations.line_id, each per-p_number subquery
-- sequential-scanned all ~87.5k translation rows. EXPLAIN ANALYZE on prod
-- (5 p_numbers) before:
--
--     ->  Seq Scan on translations tn (actual time=0.011..7.282 rows=87554 loops=5)
--     Execution Time: 90 ms
--
-- After this index:
--
--     ->  Index Only Scan using idx_translations_line_id on translations tn
--     Execution Time: 11 ms
--
-- Idempotent: on prod the index was created live on 2026-06-23 with
-- CREATE INDEX CONCURRENTLY (non-blocking, no table lock). IF NOT EXISTS makes
-- this migration a no-op there. It deliberately does NOT use CONCURRENTLY
-- because the migration runner wraps each file in a transaction and
-- CONCURRENTLY cannot run inside a transaction block.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_translations_line_id ON translations (line_id);

COMMENT ON INDEX idx_translations_line_id IS
    'FK index for translations.line_id. Makes the per-tablet has_translation '
    'EXISTS subquery index-driven instead of an ~87k-row seq scan. Added for '
    'the 2026-06-23 speed audit (QW-2).';

COMMIT;
