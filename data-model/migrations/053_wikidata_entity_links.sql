-- Migration 053: entity_wikidata_links — link Glintstone entities to Wikidata Q-numbers.
--
-- Issue #164. Enriches the SSOT (search, profiles, future maps) by attaching a
-- Wikidata Q-number to Glintstone entities that have a HIGH-CONFIDENCE,
-- ID-BASED match. The only such path that exists today is:
--
--     provenience_canon.pleiades_id  ─(Wikidata property P1584 "Pleiades ID")→  Q-number
--
-- A Pleiades ID is a stable gazetteer identifier for an ancient place; Wikidata
-- stores it on the matching place item under property P1584. Mapping an ID to an
-- ID is exact — far safer than matching by name (which is ambiguous for ancient
-- places, deities, and people). The `wikidata-entities` connector resolves these
-- in BULK via a single SPARQL query and writes only the unambiguous matches here.
--
-- WHY a link table (not a column on provenience_canon):
--   * provenience_canon's primary key is `raw_provenience` (a free-text spelling),
--     and MANY rows share one pleiades_id (e.g. ~30 raw spellings of "Babylon"
--     all carry Pleiades 893951). The Wikidata fact belongs to the PLACE, not to
--     each spelling — so we key the link on the match SIGNAL (the pleiades_id),
--     not on a provenience row.
--   * A link table is forward-compatible: if named_entities (currently empty in
--     prod) is ever populated, deity/person/place matches by a different basis
--     slot in here under a different (entity_type, match_basis) without a schema
--     change.
--
-- ACCURACY OVER COVERAGE: only confident matches are stored. A pleiades_id that
-- resolves to >1 Wikidata item, or to none, is left UNMATCHED (the connector
-- dead-letters the ambiguous ones and simply omits the no-match ones). A wrong
-- Q-number is misinformation in a scholarly tool — we never guess.
--
-- GRANT: this is a NEW table owned by wittkensis; the app connects as glintstone.
-- The connector also runs as the migration owner on the VPS, but the read path
-- (search / profiles / map) goes through the app as glintstone, so we GRANT the
-- full CRUD set and USAGE on the BIGSERIAL sequence.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + the UNIQUE constraint backing the
-- connector's ON CONFLICT make re-runs of both the migration and the connector
-- no-ops.

BEGIN;

CREATE TABLE IF NOT EXISTS entity_wikidata_links (
    id              BIGSERIAL PRIMARY KEY,

    -- WHAT kind of Glintstone entity this row links. 'place' is the only value
    -- written today (provenience). Kept as free TEXT (not an enum) so future
    -- bases — 'deity', 'person' — need no migration; the connector is the gate
    -- on what is actually allowed to be written.
    entity_type     TEXT NOT NULL,

    -- The Glintstone-side identifier this Q-number is attached to, interpreted
    -- per match_basis. For match_basis='pleiades' this is the pleiades_id
    -- (a numeric gazetteer id stored as text), which joins to
    -- provenience_canon.pleiades_id (1 link → many provenience rows).
    source_key      TEXT NOT NULL,

    -- The Wikidata Q-number, e.g. 'Q5684' (Babylon). Always the bare 'Q…' form.
    wikidata_qid    TEXT NOT NULL,

    -- HOW the match was made — the audit trail for trust. 'pleiades' = resolved
    -- via Wikidata property P1584 from a Pleiades ID (the only basis shipped in
    -- #164). 'exact-name' is reserved for a future, exact, unambiguous
    -- name-match path; it is NOT used yet.
    match_basis     TEXT NOT NULL,

    -- Confidence in [0,1]. ID-based Pleiades→Wikidata matches are 1.0 (exact
    -- identifier equality). Name-based matches, if ever added, would carry < 1.0.
    confidence      REAL NOT NULL DEFAULT 1.0,

    -- The Wikidata label at match time, stored for human eyeballing / display
    -- without a second API call. Informational only — Wikidata is the source of
    -- truth for the live label.
    wikidata_label  TEXT,

    -- Which import run wrote this row (provenance, consistent with the rest of
    -- the ingestion framework). Nullable so a manual backfill is possible.
    run_id          BIGINT REFERENCES import_runs(id),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT entity_wikidata_links_confidence_range
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT entity_wikidata_links_qid_format
        CHECK (wikidata_qid ~ '^Q[0-9]+$')
);

-- One link per (entity_type, source_key, match_basis): a given Pleiades place has
-- at most one confident Q-number. This is the ON CONFLICT target the connector
-- uses for idempotent re-runs.
CREATE UNIQUE INDEX IF NOT EXISTS entity_wikidata_links_uq
    ON entity_wikidata_links (entity_type, source_key, match_basis);

-- Reverse lookups (find the Glintstone entity behind a Q-number) and joins from
-- provenience_canon back into this table.
CREATE INDEX IF NOT EXISTS entity_wikidata_links_qid_idx
    ON entity_wikidata_links (wikidata_qid);
CREATE INDEX IF NOT EXISTS entity_wikidata_links_source_key_idx
    ON entity_wikidata_links (entity_type, source_key);

GRANT SELECT, INSERT, UPDATE, DELETE ON entity_wikidata_links TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE entity_wikidata_links_id_seq TO glintstone;

COMMIT;
