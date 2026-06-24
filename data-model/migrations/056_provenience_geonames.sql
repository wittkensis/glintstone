-- Migration 056: provenience_geonames — resolve find-spots to GeoNames places.
--
-- Issue #166. The map program (#197-#199) places each canonical find-spot
-- (provenience_canon) on a map using latitude/longitude. Migration 049 added
-- those columns and ops/scripts/geocode_provenience.py fills them from the
-- Pleiades gazetteer — but Pleiades is an ANCIENT-places gazetteer and misses
-- many sites (the backlog notes ~106 still ungeocoded, including Nineveh under
-- some spellings). GeoNames is a complementary, modern, far larger gazetteer
-- (12M+ places) with excellent coverage of modern tell names and cities.
--
-- This table records, for each provenience that we could resolve to a GeoNames
-- place with HIGH CONFIDENCE, the GeoNames id + coordinates + the match basis.
-- It is the GeoNames sibling of entity_wikidata_links (#164):
--   * keyed on the provenience identity, with the match SIGNAL stored so the
--     audit trail explains *why* we believe the match,
--   * accuracy over coverage — only confident matches are written; ambiguous or
--     low-confidence candidates are dead-lettered, never guessed. A wrong place
--     is bad scholarly data (CLAUDE.md).
--
-- WHY a link table (not just backfilling provenience_canon.latitude):
--   * provenience_canon's PK is raw_provenience (a free-text spelling); many
--     spellings share one real place. The GeoNames fact belongs to the PLACE.
--   * Keeping the GeoNames id + match_basis + confidence separately preserves
--     provenance: we can see which coordinates came from Pleiades vs GeoNames,
--     re-run conservatively, and audit/repair without losing the trail.
--   * The connector ALSO backfills provenience_canon.latitude/longitude, but
--     ONLY where they are currently NULL (it never overwrites a Pleiades match),
--     so the map gains coverage without the two sources fighting.
--
-- GRANT: NEW table owned by wittkensis; the app reads it as glintstone (map /
-- profiles), so GRANT the CRUD set + sequence usage.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + the UNIQUE index backing the
-- connector's ON CONFLICT make re-runs of both migration and connector no-ops.

BEGIN;

CREATE TABLE IF NOT EXISTS provenience_geonames (
    id                BIGSERIAL PRIMARY KEY,

    -- The provenience this GeoNames place is attached to. We key on the
    -- canonical ancient_name (the site identity) rather than raw_provenience
    -- so one confident match covers all spellings of the same site. Stored as
    -- the exact ancient_name string present in provenience_canon.
    ancient_name      TEXT NOT NULL,

    -- The GeoNames integer id (e.g. 99070 = Mosul). Stored as text for a stable
    -- deep-link (https://www.geonames.org/<id>) and to match other id columns.
    geonames_id       TEXT NOT NULL,

    -- The GeoNames canonical (ascii) name we matched, for human eyeballing.
    geonames_name     TEXT,

    -- Coordinates from GeoNames (decimal degrees). Copied here so the map / map
    -- API can read them without a second lookup, and so we can audit what we
    -- backfilled onto provenience_canon.
    latitude          DOUBLE PRECISION NOT NULL,
    longitude         DOUBLE PRECISION NOT NULL,

    -- GeoNames feature code (e.g. PPL populated place, PPLA seat, TELL, RUIN,
    -- ANS antiquity site). The audit trail for plausibility — an archaeological
    -- site code is a stronger signal than a generic populated place.
    feature_code      TEXT,
    country_code      TEXT,

    -- HOW the match was made — the trust audit trail. Values written by the
    -- connector: 'modern-name' (provenience.modern_name == GeoNames name),
    -- 'ancient-name' (provenience.ancient_name == a GeoNames name), 'alias'
    -- (curated alias table). Never a fuzzy/edit-distance basis — exact folded
    -- equality only.
    match_basis       TEXT NOT NULL,

    -- Confidence in [0,1]. Exact folded-name equality against an archaeological
    -- feature code = 0.95; against a generic populated place = 0.85; via a
    -- curated, human-verified alias = 1.0. Sub-1.0 because name equality (even
    -- exact) is weaker evidence than an id-to-id map (cf. Pleiades = 1.0).
    confidence        REAL NOT NULL DEFAULT 0.9,

    -- Which import run wrote this row (framework provenance).
    run_id            BIGINT REFERENCES import_runs(id),

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT provenience_geonames_confidence_range
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT provenience_geonames_geonames_id_format
        CHECK (geonames_id ~ '^[0-9]+$'),
    CONSTRAINT provenience_geonames_lat_range
        CHECK (latitude >= -90.0 AND latitude <= 90.0),
    CONSTRAINT provenience_geonames_lon_range
        CHECK (longitude >= -180.0 AND longitude <= 180.0)
);

-- One confident GeoNames match per (ancient_name, match_basis). This is the
-- ON CONFLICT target the connector uses for idempotent re-runs.
CREATE UNIQUE INDEX IF NOT EXISTS provenience_geonames_uq
    ON provenience_geonames (ancient_name, match_basis);

CREATE INDEX IF NOT EXISTS provenience_geonames_geonames_id_idx
    ON provenience_geonames (geonames_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON provenience_geonames TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE provenience_geonames_id_seq TO glintstone;

COMMIT;
