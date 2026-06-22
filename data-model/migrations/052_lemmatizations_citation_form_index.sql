-- Migration 052: Index lemmatizations(citation_form, guide_word)
--
-- Backs the new per-lemma attestation endpoint (#176). The lemma detail page
-- now renders an INLINE table of the tablets/lines where a lemma actually
-- occurs, replacing the old count+jump card. That table joins the dictionary
-- entry (lexical_lemmas) to the raw token-level lemmatizations by their text
-- citation form, then walks tokens -> text_lines -> artifacts:
--
--     lexical_lemmas.citation_form (+ guide_word)
--        = lemmatizations.citation_form (+ guide_word)
--          -> tokens.id  (lemmatizations.token_id)
--          -> tokens.line_id -> text_lines.id
--          -> text_lines.p_number -> artifacts.p_number
--
-- Why the text join rather than a foreign key: lemmatizations has no FK to
-- lexical_lemmas. The 2026 Fix A/C backfill 9x'd lemmatizations (65.9k ->
-- 5.4M rows) but populated citation_form + guide_word, NOT norm_id (only ~20k
-- rows carry norm_id) and NOT entry_id (zero rows). So citation_form +
-- guide_word is the only column pair that links the dictionary to the corpus
-- at scale. guide_word disambiguates homographs (e.g. sah[pig] vs sah[clean]).
--
-- Without this index, COUNT(DISTINCT p_number) and the paginated page each
-- seq-scan the 5.4M-row lemmatizations table (~1.8 s on prod for a common
-- lemma like sarru[king], which has 65k occurrences across 6.6k tablets).
-- The composite (citation_form, guide_word) index makes the WHERE filter
-- index-driven, taking the lookup to single-digit ms before the token/line
-- hydration.
--
-- Idempotent: IF NOT EXISTS makes this a no-op if the index was already
-- created live on prod with CREATE INDEX CONCURRENTLY. It deliberately does
-- NOT use CONCURRENTLY here because the migration runner wraps each file in a
-- transaction and CONCURRENTLY cannot run inside a transaction block.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_lemmatizations_citation_form
    ON lemmatizations (citation_form, guide_word);

COMMENT ON INDEX idx_lemmatizations_citation_form IS
    'Backs the per-lemma attestation lookup (#176): joins lexical_lemmas to '
    'lemmatizations by (citation_form, guide_word) to list the tablets/lines '
    'where a dictionary lemma occurs. Makes the filter index-driven instead of '
    'a 5.4M-row seq scan.';

COMMIT;
