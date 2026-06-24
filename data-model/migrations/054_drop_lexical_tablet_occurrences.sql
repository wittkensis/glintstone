-- Migration 054: Drop the stale lexical_tablet_occurrences precompute (#279)
--
-- This table was a precomputed (lemma_id|sign_id|sense_id, p_number) ->
-- occurrence_count cache, populated by core/jobs/lexical_occurrences.py. That
-- job resolved lemmas through the lemmatizations.norm_id -> lexical_norms ->
-- lexical_lemmas path, which only ever covered ~20k of the 5.4M lemmatization
-- rows after the 2026 Fix A/C backfill (Fix A/C 9x'd lemmatizations to 5.4M
-- but populated citation_form + guide_word, NOT norm_id). The precompute was
-- therefore frozen at 3,875 rows and under-counted tablet occurrences by
-- orders of magnitude. No sign-level or sense-level rows were ever populated.
--
-- Rather than recompute a cache that would still need a nightly job and could
-- drift again, the table is RETIRED in favour of the live (citation_form,
-- guide_word) join the attestation endpoints already use (#176/#201), backed
-- by idx_lemmatizations_citation_form (migration 052). The two code consumers
-- were migrated to that live join before this drop:
--   - api/repositories/lexical_repo.py :: get_lemma_occurrence_stats
--   - core/lexical.py :: get_tablets_for_lemma / get_tablets_for_sign
-- and the orphaned populate job (core/jobs/lexical_occurrences.py) was deleted.
--
-- Idempotent: DROP TABLE IF EXISTS removes the table, its primary-key sequence
-- (owned by the table, so it goes with it), its indexes, and its foreign-key
-- constraints in one statement. CASCADE is not needed — nothing depends on it.
--
-- Reversal: there is no down-migration. If a precompute is ever wanted again,
-- recreate it from migration 008's DDL and repopulate from the live join.

BEGIN;

DROP TABLE IF EXISTS lexical_tablet_occurrences;

COMMIT;
