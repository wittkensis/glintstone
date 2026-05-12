-- Migration 022: Artifact images table
--
-- Stores metadata for every tablet image (photo or line drawing) sourced from
-- CDLI (and eventually other sources). Binaries live in Cloudflare R2; this
-- table holds the pointer, copyright, and provenance.
--
-- Two ingestion paths populate this table, both writing rows the same way:
--   1) On-demand fetch when a user views an artifact card that has no rows yet
--   2) Background backfill respecting CDLI's robots.txt Crawl-delay: 60s
--
-- Per CLAUDE.md non-negotiable: every row carries annotation_run_id so the
-- fetch's source / tool version / timestamp is recoverable.

CREATE TABLE IF NOT EXISTS artifact_images (
    id                  bigserial   PRIMARY KEY,
    p_number            text        NOT NULL REFERENCES artifacts(p_number) ON DELETE CASCADE,
    image_type          text        NOT NULL,
    cdli_reader_id      integer,                                -- /artifacts/{id}/reader/{cdli_reader_id} on CDLI
    source_url          text        NOT NULL,                   -- URL we fetched from
    r2_key              text        NOT NULL UNIQUE,            -- object key in R2 bucket
    r2_thumbnail_key    text,                                   -- 400px WebP thumbnail; null until generated
    mime_type           text,
    byte_size           bigint,
    width               integer,
    height              integer,
    sha256              text,                                   -- of the original binary, for dedup verification
    copyright_holder    text,                                   -- parsed institution, e.g. "Vorderasiatisches Museum, Berlin"
    license             text,                                   -- best-known license; null if not stated
    attribution_raw     text,                                   -- the raw string scraped from CDLI HTML
    credit_line         text,                                   -- display-ready, e.g. "Image courtesy of X (via CDLI)"
    captured_date       date,                                   -- from photo_up metadata when parseable
    display_order       integer     NOT NULL DEFAULT 0,         -- 0 = primary; higher = secondary views
    ingested_at         timestamptz NOT NULL DEFAULT now(),
    annotation_run_id   integer     NOT NULL REFERENCES annotation_runs(id),
    CONSTRAINT artifact_images_type_check
        CHECK (image_type IN ('photo', 'lineart', 'other')),
    CONSTRAINT artifact_images_unique_source
        UNIQUE (p_number, image_type, cdli_reader_id)
);

CREATE INDEX IF NOT EXISTS artifact_images_p_number_idx
    ON artifact_images (p_number, display_order);
CREATE INDEX IF NOT EXISTS artifact_images_type_idx
    ON artifact_images (image_type);
CREATE INDEX IF NOT EXISTS artifact_images_sha256_idx
    ON artifact_images (sha256);


-- Fetch attempt log: lets us see what we tried and failed without polluting
-- the dead_letters channel (which is for systemic schema/parse errors).
-- Successful fetches also log a row here so we know when we last touched
-- a given URL — useful for re-fetch / cache-bust decisions later.

CREATE TABLE IF NOT EXISTS artifact_image_fetch_log (
    id                  bigserial   PRIMARY KEY,
    p_number            text        NOT NULL,
    source_url          text        NOT NULL,
    attempted_at        timestamptz NOT NULL DEFAULT now(),
    outcome             text        NOT NULL,                   -- 'success', 'http_404', 'http_5xx', 'timeout', 'decode_failed', 'rate_limited'
    http_status         integer,
    error_message       text,
    artifact_image_id   bigint REFERENCES artifact_images(id) ON DELETE SET NULL,
    CONSTRAINT artifact_image_fetch_log_outcome_check
        CHECK (outcome IN ('success', 'http_404', 'http_5xx', 'timeout', 'decode_failed', 'rate_limited', 'other_error'))
);

CREATE INDEX IF NOT EXISTS artifact_image_fetch_log_p_number_idx
    ON artifact_image_fetch_log (p_number, attempted_at DESC);
CREATE INDEX IF NOT EXISTS artifact_image_fetch_log_outcome_idx
    ON artifact_image_fetch_log (outcome) WHERE outcome <> 'success';


DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'glintstone') THEN
        GRANT SELECT, INSERT, UPDATE ON artifact_images TO glintstone;
        GRANT USAGE, SELECT ON SEQUENCE artifact_images_id_seq TO glintstone;
        GRANT SELECT, INSERT ON artifact_image_fetch_log TO glintstone;
        GRANT USAGE, SELECT ON SEQUENCE artifact_image_fetch_log_id_seq TO glintstone;
    END IF;
END$$;


COMMENT ON TABLE artifact_images IS
    'Per-image metadata for tablet photographs and line drawings. '
    'Binaries live in Cloudflare R2 (see core/storage.py). Multiple images per '
    'artifact are stored with distinct cdli_reader_id and display_order. '
    'copyright_holder + attribution_raw + credit_line are required for scholarly '
    'reuse; never overwrite once captured (create a new row instead).';

COMMENT ON COLUMN artifact_images.attribution_raw IS
    'The unmodified string scraped from the CDLI artifact page, e.g. '
    '"© Vorderasiatisches Museum, Berlin, Germany". Always preserve so we can '
    're-derive copyright_holder if our parser changes.';

COMMENT ON COLUMN artifact_images.credit_line IS
    'Display-ready credit. Format: "Image courtesy of {copyright_holder}, via CDLI". '
    'Used directly in the UI caption. Never inferred without attribution_raw.';
