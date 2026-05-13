-- Migration 026: search_entities matview + pipeline_completeness view
--
-- search_entities is the unified lexical surface that the hybrid retriever
-- queries. It UNIONs the searchable entity types (tablets, lemmas, signs,
-- scholars, composites, named_entities) into one shape so trigram + tsvector
-- ranking compares apples to apples.
--
-- pipeline_completeness scores each artifact 0-5 on the five pipeline stages
-- (Captured → Recognized → Transcribed → Lemmatized → Translated) plus an
-- entity-mention bonus. summarize_artifact uses this for its best-guess gate.
--
-- See .claude/skills/gs-expert-agentic/hero-tools.md for usage.

BEGIN;

-- ── search_entities matview ─────────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS search_entities CASCADE;

CREATE MATERIALIZED VIEW search_entities AS
-- Tablets / artifacts
SELECT
    'tablets'::text                                 AS entity_type,
    a.p_number::text                                AS entity_id,
    a.designation                                   AS primary_label,
    COALESCE(a.period_normalized, '')
        || CASE WHEN a.provenience_normalized IS NOT NULL
                THEN ' • ' || a.provenience_normalized ELSE '' END  AS secondary_label,
    COALESCE(a.designation, '') || ' '
        || COALESCE(a.period_normalized, '') || ' '
        || COALESCE(a.provenience_normalized, '') || ' '
        || a.p_number                                AS search_blob,
    to_tsvector('simple',
        COALESCE(a.designation, '') || ' '
        || COALESCE(a.period_normalized, '') || ' '
        || COALESCE(a.provenience_normalized, '')
    )                                                AS tsv,
    ARRAY['cdli_catalog']::text[]                    AS sources,
    a.p_number                                       AS p_number_ref,
    NULL::int                                        AS int_ref,
    NULL::timestamptz                                AS updated_at
FROM artifacts a

UNION ALL

-- Lexical lemmas
SELECT
    'lemmas'::text                                   AS entity_type,
    ll.id::text                                      AS entity_id,
    ll.citation_form                                 AS primary_label,
    COALESCE(ll.guide_word, '')
        || CASE WHEN ll.pos IS NOT NULL THEN ' • ' || ll.pos ELSE '' END
        || CASE WHEN ll.language IS NOT NULL THEN ' • ' || ll.language ELSE '' END
                                                     AS secondary_label,
    COALESCE(ll.citation_form, '') || ' '
        || COALESCE(ll.guide_word, '') || ' '
        || COALESCE(ll.pos, '') || ' '
        || COALESCE(ll.language, '')                 AS search_blob,
    to_tsvector('simple',
        COALESCE(ll.citation_form, '') || ' '
        || COALESCE(ll.guide_word, '')
    )                                                AS tsv,
    ARRAY[COALESCE(ll.primary_source, 'lexical')]::text[]  AS sources,
    NULL::text                                       AS p_number_ref,
    ll.id                                            AS int_ref,
    NULL::timestamptz                                AS updated_at
FROM lexical_lemmas ll

UNION ALL

-- Lexical signs
SELECT
    'signs'::text                                    AS entity_type,
    ls.id::text                                      AS entity_id,
    COALESCE(ls.sign_name, ls.unicode_char, ls.id::text)  AS primary_label,
    COALESCE(ls.unicode_char, '')                    AS secondary_label,
    COALESCE(ls.sign_name, '') || ' ' || COALESCE(ls.unicode_char, '')  AS search_blob,
    to_tsvector('simple', COALESCE(ls.sign_name, ''))   AS tsv,
    ARRAY['ogsl', 'epsd2']::text[]                   AS sources,
    NULL::text                                       AS p_number_ref,
    ls.id                                            AS int_ref,
    NULL::timestamptz                                AS updated_at
FROM lexical_signs ls

UNION ALL

-- Scholars
SELECT
    'scholars'::text                                 AS entity_type,
    s.id::text                                       AS entity_id,
    s.name                                           AS primary_label,
    COALESCE(s.affiliation, '')                      AS secondary_label,
    s.name || ' ' || COALESCE(s.affiliation, '')     AS search_blob,
    to_tsvector('simple', s.name || ' ' || COALESCE(s.affiliation, ''))  AS tsv,
    ARRAY['scholars_registry']::text[]               AS sources,
    NULL::text                                       AS p_number_ref,
    s.id                                             AS int_ref,
    NULL::timestamptz                                AS updated_at
FROM scholars s

UNION ALL

-- Named entities (when populated)
SELECT
    'entities'::text                                 AS entity_type,
    ne.id::text                                      AS entity_id,
    ne.canonical_name                                AS primary_label,
    COALESCE(ne.entity_type, '')                     AS secondary_label,
    ne.canonical_name || ' ' || COALESCE(ne.entity_type, '')  AS search_blob,
    to_tsvector('simple', ne.canonical_name)         AS tsv,
    ARRAY['named_entities']::text[]                  AS sources,
    NULL::text                                       AS p_number_ref,
    ne.id                                            AS int_ref,
    NULL::timestamptz                                AS updated_at
FROM named_entities ne;

CREATE UNIQUE INDEX uq_search_entities ON search_entities(entity_type, entity_id);
CREATE INDEX idx_search_entities_tsv ON search_entities USING GIN(tsv);
CREATE INDEX idx_search_entities_blob_trgm ON search_entities USING GIN(search_blob gin_trgm_ops);
CREATE INDEX idx_search_entities_type ON search_entities(entity_type);

GRANT SELECT ON search_entities TO glintstone;

-- Refresh routine — invoke from a cron / scheduled job, not from request path.
-- Cheap-ish; full refresh against current row counts ~30s.
COMMENT ON MATERIALIZED VIEW search_entities IS
    'Unified search corpus. Refresh nightly via: REFRESH MATERIALIZED VIEW CONCURRENTLY search_entities;';

-- ── pipeline_completeness view ──────────────────────────────────────────────
-- Score 0-5: has-ATF (text_lines), has-tokens, has-lemmatization (≥50%),
-- has-translation, has-named-entities (when populated). Plus a sixth-stage
-- bonus for has-image (artifact_images).

DROP VIEW IF EXISTS pipeline_completeness CASCADE;

CREATE VIEW pipeline_completeness AS
WITH a AS (
    SELECT a.p_number, a.designation
    FROM artifacts a
),
tl AS (
    SELECT DISTINCT s.p_number
    FROM text_lines tl
    JOIN surfaces s ON tl.surface_id = s.id
),
tk AS (
    SELECT DISTINCT s.p_number, COUNT(*) AS token_count
    FROM tokens t
    JOIN text_lines tl ON t.line_id = tl.id
    JOIN surfaces s ON tl.surface_id = s.id
    GROUP BY s.p_number
),
lm AS (
    SELECT s.p_number,
           COUNT(*) FILTER (WHERE lz.id IS NOT NULL)::float
           / NULLIF(COUNT(*), 0) AS lemma_ratio
    FROM tokens t
    JOIN text_lines tl ON t.line_id = tl.id
    JOIN surfaces s ON tl.surface_id = s.id
    LEFT JOIN lemmatizations lz ON lz.token_id = t.id
    GROUP BY s.p_number
),
tr AS (
    SELECT DISTINCT s.p_number
    FROM translations tn
    JOIN text_lines tl ON tn.line_id = tl.id
    JOIN surfaces s ON tl.surface_id = s.id
),
ne AS (
    SELECT DISTINCT s.p_number
    FROM entity_mentions em
    LEFT JOIN tokens t ON em.token_id = t.id
    LEFT JOIN text_lines tl_t ON t.line_id = tl_t.id
    LEFT JOIN text_lines tl_l ON em.line_id = tl_l.id
    JOIN surfaces s ON s.id = COALESCE(tl_t.surface_id, tl_l.surface_id)
),
img AS (
    SELECT DISTINCT p_number
    FROM artifact_images
)
SELECT
    a.p_number,
    a.designation,
    (tl.p_number IS NOT NULL)::int                          AS has_atf,
    COALESCE(tk.token_count, 0)                             AS token_count,
    (tk.p_number IS NOT NULL)::int                          AS has_tokens,
    COALESCE(lm.lemma_ratio, 0.0)                           AS lemma_ratio,
    (COALESCE(lm.lemma_ratio, 0) >= 0.5)::int               AS has_lemmatization,
    (tr.p_number IS NOT NULL)::int                          AS has_translation,
    (ne.p_number IS NOT NULL)::int                          AS has_entities,
    (img.p_number IS NOT NULL)::int                         AS has_image,
    (   (tl.p_number IS NOT NULL)::int
      + (tk.p_number IS NOT NULL)::int
      + (COALESCE(lm.lemma_ratio, 0) >= 0.5)::int
      + (tr.p_number IS NOT NULL)::int
      + (ne.p_number IS NOT NULL)::int
    )                                                       AS completeness_score
FROM a
LEFT JOIN tl  ON tl.p_number  = a.p_number
LEFT JOIN tk  ON tk.p_number  = a.p_number
LEFT JOIN lm  ON lm.p_number  = a.p_number
LEFT JOIN tr  ON tr.p_number  = a.p_number
LEFT JOIN ne  ON ne.p_number  = a.p_number
LEFT JOIN img ON img.p_number = a.p_number;

GRANT SELECT ON pipeline_completeness TO glintstone;

COMMIT;
