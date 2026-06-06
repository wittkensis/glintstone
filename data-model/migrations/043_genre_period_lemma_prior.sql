-- Migration 043: genre_period_lemma_prior materialized view
-- Used by PRD-007 (line suggestions) to provide vocabulary priors.
--
-- Schema correction: artifacts has no genre_normalized column.
-- Genre uses junction tables: artifact_genres → canonical_genres(name).
-- period_normalized exists directly on artifacts.

BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS genre_period_lemma_prior AS
SELECT
    cg.name             AS genre_normalized,
    a.period_normalized,
    lz.citation_form,
    lz.guide_word,
    COUNT(*)            AS attestation_count,
    RANK() OVER (
        PARTITION BY cg.name, a.period_normalized
        ORDER BY COUNT(*) DESC
    )                   AS rank
FROM artifacts a
JOIN artifact_genres ag  ON ag.p_number  = a.p_number
JOIN canonical_genres cg ON cg.id        = ag.genre_id
JOIN surfaces s          ON s.p_number   = a.p_number
JOIN text_lines tl       ON tl.surface_id = s.id
JOIN tokens t            ON t.line_id    = tl.id
JOIN lemmatizations lz   ON lz.token_id  = t.id
WHERE a.period_normalized IS NOT NULL
  AND lz.citation_form    IS NOT NULL
GROUP BY
    cg.name,
    a.period_normalized,
    lz.citation_form,
    lz.guide_word
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_genre_period_lemma_prior_dims
    ON genre_period_lemma_prior (genre_normalized, period_normalized, rank);

GRANT SELECT ON genre_period_lemma_prior TO glintstone;

COMMIT;
