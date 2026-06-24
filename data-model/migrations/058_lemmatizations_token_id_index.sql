-- Migration 058: Index lemmatizations(token_id)
--
-- Adds the missing foreign-key index on lemmatizations.token_id. This is the
-- single highest-leverage fix from the 2026-06-23 speed audit (PERSONAL/
-- execution/glintstone-speed-audit-2026-06-23.md, QW-1 / §7).
--
-- Root cause: every semantic/hybrid search runs `_hydrate_tablet_extras`
-- (core/agent/pipeline_completeness.py, _HAS_LEMMATIZATION), which for each
-- result tablet does:
--
--     LEFT JOIN lemmatizations lz ON lz.token_id = t.id
--
-- With no index on lemmatizations.token_id, each per-p_number subquery
-- sequential-scanned all 5.4M lemmatization rows. EXPLAIN ANALYZE on prod
-- (5 p_numbers) before the fix:
--
--     ->  Seq Scan on lemmatizations lz (actual time=0.032..561 rows=5431793 loops=5)
--     Execution Time: 5302 ms
--
-- After this index:
--
--     ->  Index Scan using idx_lemmatizations_token_id on lemmatizations lz
--         (actual time=0.001..0.001 rows=0 loops=44161)
--     Execution Time: 103 ms
--
-- End-to-end: live API semantic search on prod dropped from ~5 s (loopback;
-- ~11 s end-to-end per the audit's DIAG total_ms=11258) to ~0.2 s.
--
-- Idempotent: on prod the index was created live on 2026-06-23 with
-- CREATE INDEX CONCURRENTLY (non-blocking, 3.8 s build, no table lock).
-- IF NOT EXISTS makes this migration a no-op there. On fresh/staging databases
-- it builds the index (a brief lock, acceptable when the table is small or
-- empty). It deliberately does NOT use CONCURRENTLY because the migration
-- runner wraps each file in a transaction and CONCURRENTLY cannot run inside a
-- transaction block.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_lemmatizations_token_id ON lemmatizations (token_id);

COMMENT ON INDEX idx_lemmatizations_token_id IS
    'FK index for lemmatizations.token_id. Makes the per-tablet '
    'lemmatized-token-ratio subquery (_HAS_LEMMATIZATION) index-driven instead '
    'of a 5.4M-row seq scan. Added for the 2026-06-23 speed audit (QW-1): cut '
    'search hydration from ~5.3 s to ~0.1 s for 5 tablets.';

COMMIT;
