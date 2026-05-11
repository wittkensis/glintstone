-- Migration 021: Source snapshot metadata table
--
-- Tracks when raw source files were downloaded/archived and where they're stored.
-- Storage backend is abstracted: uri column holds either a B2 or local path.
-- Decision: use B2 for large blobs (CDLI ATF ~500MB); VPS disk for small reference files.

CREATE TABLE IF NOT EXISTS source_snapshots (
    id              bigserial PRIMARY KEY,
    source_name     text        NOT NULL,           -- matches annotation_runs.source_name
    snapshot_date   date        NOT NULL,
    version_label   text,                           -- e.g. "Aug 2022", "2024-01"
    file_name       text        NOT NULL,
    file_size_bytes bigint,
    sha256_checksum text,
    storage_backend text        NOT NULL CHECK (storage_backend IN ('b2', 'vps', 'local')),
    uri             text        NOT NULL,           -- b2://bucket/path or /abs/path or gs://...
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS source_snapshots_source_name_idx ON source_snapshots (source_name);
CREATE INDEX IF NOT EXISTS source_snapshots_date_idx ON source_snapshots (snapshot_date);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'glintstone') THEN
        GRANT SELECT, INSERT, UPDATE ON source_snapshots TO glintstone;
        GRANT USAGE, SELECT ON SEQUENCE source_snapshots_id_seq TO glintstone;
    END IF;
END$$;

COMMENT ON TABLE source_snapshots IS
    'Tracks raw source file archives. Storage backend (B2 vs VPS disk) is '
    'determined per-source by ops policy — see ops/snapshots/README.md.';
