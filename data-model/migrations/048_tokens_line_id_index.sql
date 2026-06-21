-- Migration 048: Index tokens(line_id)
--
-- Adds the missing foreign-key index on tokens.line_id. Without it, any query
-- that gathers a tablet's tokens by joining text_lines -> tokens has to fall
-- back to a sequential scan over the whole tokens table (~5.1M rows on prod).
--
-- This is the root cause of issue #255: the hero search path's per-result
-- "pipeline completeness" hydration derived its 5-dot badge (has_atf,
-- has_tokens, has_lemmatization, has_translation, has_entities) from the
-- corpus-wide `pipeline_completeness` view. For the handful of tablet hits on
-- screen it only needs those flags for a few p_numbers, but the token/lemma
-- branches seq-scanned all of `tokens`, pushing end-to-end search to ~10 s
-- even though the semantic SQL itself runs in ~270 ms.
--
-- The companion code change in core/agent/search_engine.py rewrites the
-- hydration to per-p_number EXISTS / ratio subqueries that filter at the base
-- tables; this index is what makes those subqueries index-driven instead of
-- seq scans, taking the hydration stage from ~10 s to ~0.2 s for 5 tablets.
--
-- Idempotent: on prod the index was created live with CREATE INDEX
-- CONCURRENTLY (non-blocking on the live table); IF NOT EXISTS makes this
-- migration a no-op there. On fresh/staging databases it builds the index
-- (a brief lock, acceptable when the table is small or empty). It deliberately
-- does NOT use CONCURRENTLY because the migration runner wraps each file in a
-- transaction, and CONCURRENTLY cannot run inside a transaction block.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_tokens_line_id ON tokens(line_id);

COMMENT ON INDEX idx_tokens_line_id IS
    'FK index for tokens.line_id. Makes per-tablet token lookups '
    '(text_lines JOIN tokens) index-driven instead of a full tokens seq scan. '
    'Added for issue #255 (hero search hydration perf).';

COMMIT;
