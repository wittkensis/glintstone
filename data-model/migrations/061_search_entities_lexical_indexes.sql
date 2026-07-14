-- Migration 061: Ensure the lexical GIN indexes on search_entities exist
--
-- Companion to the #1101 fix (graceful lexical-search timeout in hybrid mode).
--
-- Background: the hybrid retriever's lexical leg
-- (core/agent/search_engine.py::_lexical_search / _count_per_type) scans the
-- search_entities materialized view with two predicates:
--
--     search_blob %% :q                              -- pg_trgm similarity
--     tsv @@ plainto_tsquery('simple', :q)           -- tsvector full-text
--
-- Both are accelerated by GIN indexes originally created in migration 026
-- (idx_search_entities_blob_trgm on search_blob gin_trgm_ops, and
-- idx_search_entities_tsv on tsv). A multi-word query such as "Ur III" widens
-- the pg_trgm candidate set; if either GIN index is ever missing (e.g. the
-- matview was rebuilt via a script that dropped and recreated it without the
-- indexes), that leg falls back to a full sequential scan and times out.
--
-- This migration re-asserts both indexes idempotently, so any environment whose
-- search_entities was rebuilt off the index-less path is brought back into line
-- with migration 026. On an environment that already has them (prod, and any DB
-- migrated through 026) this is a no-op.
--
-- Idempotent: IF NOT EXISTS on both. Deliberately NOT CONCURRENTLY — the
-- migration runner wraps each file in a transaction and CONCURRENTLY cannot run
-- inside a transaction block (see migration 059 for the same note). If a future
-- rebuild needs a non-blocking create on a live prod table, run
-- `CREATE INDEX CONCURRENTLY ...` by hand out-of-band first; this file then
-- no-ops.

BEGIN;

-- pg_trgm requires the extension; created in an earlier migration but asserted
-- here so this file stands alone if run against a fresh DB.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_search_entities_blob_trgm
    ON search_entities USING GIN (search_blob gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_search_entities_tsv
    ON search_entities USING GIN (tsv);

COMMENT ON INDEX idx_search_entities_blob_trgm IS
    'pg_trgm GIN index backing the hybrid lexical leg''s `search_blob %% :q` '
    'similarity predicate. Re-asserted in migration 061 (#1101) so a matview '
    'rebuild can never leave the lexical leg on a full seq scan.';

COMMENT ON INDEX idx_search_entities_tsv IS
    'tsvector GIN index backing the hybrid lexical leg''s '
    '`tsv @@ plainto_tsquery` full-text predicate. Re-asserted in migration '
    '061 (#1101).';

COMMIT;
