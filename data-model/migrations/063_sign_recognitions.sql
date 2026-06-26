-- Migration 063: sign_recognitions — ML sign-reading predictions (Akkademia).
--
-- Backlog #535. Stores per-sign reading predictions produced by the Akkademia
-- model (pip package `akkadian`, repo gaigutherz/Akkademia). Akkademia takes
-- Unicode cuneiform glyphs and emits a transliteration — i.e. it predicts the
-- READING of each sign. We persist each predicted reading as one row here, with
-- the model's (derived) confidence and the alternative readings it ranked below
-- the top choice.
--
-- IMPORTANT — what Akkademia actually is (spec-vs-reality):
--   The #535 brief described "image sign recognition". The shipped Akkademia
--   library is NOT image-based: it is a text transliterator that consumes
--   Unicode cuneiform signs and returns sign-readings (HMM / MEMM / BiLSTM).
--   So this table records SIGN-READING predictions keyed to an artifact, and
--   carries `image_source_url` purely as provenance for the artifact image the
--   signs were read from (when one exists). The bounding_box column is kept
--   nullable for a future image-based detector; Akkademia leaves it NULL.
--
-- ATTRIBUTION IS STRUCTURAL (CLAUDE.md non-negotiable): every row carries
-- `annotation_run_id` -> annotation_runs.id. The Akkademia source is seeded as a
-- canonical annotation_runs row (source_name = 'akkademia-signs') by the
-- annotation-runs connector, exactly like CompVis / BabyLemmatizer. Competing
-- interpretations are a feature: a later run produces NEW rows (a new
-- annotation_run_id) rather than overwriting an earlier run's predictions.
--
-- GRANT: NEW table owned by wittkensis; the web path reads it as glintstone via
-- the API. Full CRUD + sequence USAGE granted to glintstone.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + the UNIQUE index backing the
-- connector's ON CONFLICT make re-runs of both the migration and the connector
-- no-ops within a given run.

BEGIN;

CREATE TABLE IF NOT EXISTS sign_recognitions (
    id                  BIGSERIAL PRIMARY KEY,

    -- The artifact whose signs were read. Glintstone's canonical artifact key
    -- is the P-number (artifacts.p_number) -- the table the UI surfaces as
    -- "tablets". (#535 called this `tablet_id`; the real FK is the P-number.)
    p_number            TEXT NOT NULL REFERENCES artifacts(p_number),

    -- Position of this sign within the sequence Akkademia transliterated, so the
    -- predicted readings stay ordered without relying on row id. 0-based.
    sign_index          INTEGER NOT NULL DEFAULT 0,

    -- The predicted transliteration (sign-reading) for this sign, e.g. 'sza2',
    -- 'nak', 'ba'. This is Akkademia's top choice for the glyph.
    sign_label          TEXT NOT NULL,

    -- The Unicode cuneiform glyph(s) this reading was predicted from, kept for
    -- audit / display so a scholar can see exactly what the model read.
    source_glyph        TEXT,

    -- Confidence in [0,1]. Akkademia's public API does not expose a raw
    -- probability, so the connector derives a coarse confidence from which of
    -- the top-3 BiLSTM candidates this reading is (rank 1 >> rank 2 >> rank 3).
    confidence          REAL,

    -- The full ranked alternative list the model returned for this sign (top-3),
    -- so competing readings are inspectable without re-running inference.
    -- JSON array of strings, e.g. ["sza2","sza","MUN"]. NULL when only one.
    alternatives        JSONB,

    -- Pixel bounding box on the source image, when an image-based detector
    -- produces one. Akkademia is text-based and leaves this NULL. Shape (future):
    -- {"x":int,"y":int,"w":int,"h":int}.
    bounding_box        JSONB,

    -- Provenance: the artifact image the signs were read from, when one exists
    -- (R2 public URL or CDLI source URL). Informational -- Akkademia does not
    -- consume the image, but #535 wants the link recorded for traceability.
    image_source_url    TEXT,

    -- Structural attribution -- which run produced this prediction.
    annotation_run_id   INTEGER NOT NULL REFERENCES annotation_runs(id),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT sign_recognitions_confidence_range
        CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0))
);

-- One reading per (artifact, run, sign position): re-running the SAME run is a
-- no-op (ON CONFLICT DO NOTHING). A NEW run gets a NEW annotation_run_id, so its
-- predictions coexist with prior runs -- competing interpretations preserved.
CREATE UNIQUE INDEX IF NOT EXISTS sign_recognitions_run_sign_uq
    ON sign_recognitions (p_number, annotation_run_id, sign_index);

-- The UI read path: "give me the recognized signs for this tablet, newest run
-- first, in sign order".
CREATE INDEX IF NOT EXISTS sign_recognitions_p_number_idx
    ON sign_recognitions (p_number, annotation_run_id DESC, sign_index);

GRANT SELECT, INSERT, UPDATE, DELETE ON sign_recognitions TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE sign_recognitions_id_seq TO glintstone;

COMMIT;
