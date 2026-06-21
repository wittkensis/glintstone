-- 050_artifact_contributors.sql
-- Issue #261 — real per-artifact scholar attribution.
--
-- The attribution data for ORACC editions lives as unparsed prose in
-- artifact_credits.credits_text (e.g. "Lemmatised by Mikko Luukko, 2017 …
-- Edition by X … directed by Karen Radner"). Each artifact credits MULTIPLE
-- scholars in MULTIPLE roles, so the single annotation_runs.scholar_id (one
-- run shared by all 353K artifacts) cannot hold it. This junction is the real
-- many-to-many home: one row per (artifact x scholar x role).
--
-- annotation_runs.scholar_id is intentionally left for its original purpose
-- (future human annotation runs); it is NOT the attribution source any more.

BEGIN;

CREATE TABLE IF NOT EXISTS artifact_contributors (
    id               BIGSERIAL PRIMARY KEY,
    p_number         TEXT   NOT NULL REFERENCES artifacts(p_number),
    scholar_id       INTEGER NOT NULL REFERENCES scholars(id),
    -- Controlled role vocabulary derived from the credit prose. Keep it small
    -- and explicit; unknown phrasings are dropped by the parser, never coerced.
    role             TEXT   NOT NULL CHECK (role IN (
                         'lemmatizer',   -- "Lemmatised/Lemmatized by", "lemmatized by"
                         'editor',       -- "Edition by", "Edited by", "Edition:"
                         'adapter',      -- "Adapted from/for", "adapted for X by"
                         'director',     -- "directed by"
                         'creator',      -- "Created by"
                         'contributor'   -- generic fallback ("courtesy", "Identification")
                       )),
    oracc_project    TEXT   NOT NULL,
    -- Provenance: the artifact_credits row this link was parsed out of, so a
    -- re-parse can be diffed and a bad parse can be traced back to its prose.
    source_credit_id INTEGER REFERENCES artifact_credits(id),
    -- The exact name string lifted from the prose before normalization, kept
    -- for audit ("did we match the right person?"). Never displayed.
    matched_name     TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One link per artifact x scholar x role x project. Re-running the backfill is
-- idempotent (ON CONFLICT DO NOTHING against this constraint).
CREATE UNIQUE INDEX IF NOT EXISTS uq_artifact_contributors_link
    ON artifact_contributors (p_number, scholar_id, role, oracc_project);

-- The ledger query (/scholars/{id}/contributions) filters by scholar_id.
CREATE INDEX IF NOT EXISTS idx_artifact_contributors_scholar
    ON artifact_contributors (scholar_id);

-- Re-parse / trace by source credit row.
CREATE INDEX IF NOT EXISTS idx_artifact_contributors_source_credit
    ON artifact_contributors (source_credit_id);

-- IMPORTANT: app connects as glintstone; tables are owned by wittkensis.
GRANT SELECT, INSERT, UPDATE, DELETE ON artifact_contributors TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE artifact_contributors_id_seq TO glintstone;

COMMIT;
