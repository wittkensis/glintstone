-- Migration 046: comprehensive composites + publication integration (Tier 1 of #89)
--
-- Extends the composites table with five high-coverage ORACC fields and adds a
-- composite_publications join table linking composites to the publications
-- catalogue.  This is Tier 1 only — data already in hand from the ORACC
-- catalogue.json files the oracc-composite-catalog connector already reads.
-- No new download required; the connector is extended in the same change.
--
-- ORACC field coverage across 8,763 Q-numbers (from #89 audit):
--   primary_publication 54% · popular_name 36% · ruler 64% ·
--   dynastic_seat 67% · publication_history 11%
--
-- composite_publications.role is freeform TEXT for now (NOT a CHECK-constrained
-- vocabulary). #89 leaves the edition/study/translation/commentary vocabulary
-- as an open question; freeform avoids locking it in before that is decided.

BEGIN;

-- ── composites: five new metadata columns ───────────────────────────────────
ALTER TABLE composites
    ADD COLUMN IF NOT EXISTS primary_publication TEXT,
    ADD COLUMN IF NOT EXISTS popular_name        TEXT,
    ADD COLUMN IF NOT EXISTS ruler               TEXT,
    ADD COLUMN IF NOT EXISTS dynastic_seat       TEXT,
    ADD COLUMN IF NOT EXISTS publication_history TEXT;

COMMENT ON COLUMN composites.primary_publication IS
    'ORACC primary_publication — canonical first/standard publication reference.';
COMMENT ON COLUMN composites.popular_name IS
    'ORACC popular_name — common scholarly name (e.g. "Code of Hammurabi").';
COMMENT ON COLUMN composites.ruler IS
    'ORACC ruler — attributed ruler / royal author where applicable.';
COMMENT ON COLUMN composites.dynastic_seat IS
    'ORACC dynastic_seat — seat of the dynasty (capital city) where applicable.';
COMMENT ON COLUMN composites.publication_history IS
    'ORACC publication_history — free-text history of editions/publications.';

-- ── composite_publications: link composites → publications ───────────────────
CREATE TABLE IF NOT EXISTS composite_publications (
    q_number       TEXT    NOT NULL REFERENCES composites(q_number) ON DELETE CASCADE,
    publication_id INTEGER NOT NULL REFERENCES publications(id)     ON DELETE CASCADE,
    role           TEXT,  -- freeform: 'edition', 'study', 'translation', 'commentary', ...
    PRIMARY KEY (q_number, publication_id)
);

COMMENT ON TABLE composite_publications IS
    'Join table linking composites (canonical texts) to publications. '
    'role describes the publication''s relationship to the composite '
    '(edition / study / translation / commentary); freeform pending #89.';

CREATE INDEX IF NOT EXISTS idx_composite_publications_publication
    ON composite_publications (publication_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON composite_publications TO glintstone;

COMMIT;
