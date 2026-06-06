-- Migration 043: genre_period_lemma_prior materialized view
-- Used by PRD-007 (line suggestions) to provide vocabulary priors.
-- Joins artifacts → surfaces → text_lines → tokens → lemmatizations.
--
-- Schema note: lemmatizations stores citation_form and guide_word directly;
-- there is no lexical_lemmas.id FK on lemmatizations in the current schema.
-- The PRD-agentic-translation.md §2.2 DDL references lexical_lemmas but that
-- join path does not exist — using lemmatizations columns directly is correct.
--
-- Refresh: nightly via ops/cron/refresh_views.sh or after major ingestion runs.

BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS genre_period_lemma_prior AS
SELECT
    a.genre_normalized,
    a.period_normalized,
    lz.citation_form,
    lz.guide_word,
    COUNT(*)        AS attestation_count,
    RANK() OVER (
        PARTITION BY a.genre_normalized, a.period_normalized
        ORDER BY COUNT(*) DESC
    )               AS rank
FROM artifacts a
JOIN surfaces s   ON s.p_number  = a.p_number
JOIN text_lines tl ON tl.surface_id = s.id
JOIN tokens t      ON t.line_id   = tl.id
JOIN lemmatizations lz ON lz.token_id = t.id
WHERE a.genre_normalized   IS NOT NULL
  AND a.period_normalized  IS NOT NULL
  AND lz.citation_form     IS NOT NULL
GROUP BY
    a.genre_normalized,
    a.period_normalized,
    lz.citation_form,
    lz.guide_word
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_genre_period_lemma_prior_dims
    ON genre_period_lemma_prior (genre_normalized, period_normalized, rank);

GRANT SELECT ON genre_period_lemma_prior TO glintstone;

COMMIT;
